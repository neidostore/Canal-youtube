#!/usr/bin/env python3
"""Lado de Claude: hablar con el bot de revisión de Neido Studio.

La clave del bot (CLAUDE_KEY) NO está aquí: el proxy de la sesión la añade a cada petición
dirigida al dominio del bot. La dirección del bot se lee de bot/config.json ("url").

Uso:
  python3 cliente.py enviar <video.mp4> <datos.json>   # manda a revisión (comprime si hace falta)
  python3 cliente.py tareas                            # aprobados y cambios pendientes (JSON)
  python3 cliente.py voz <file_id> <salida.ogg>        # descarga un audio de cambios
  python3 cliente.py transcribir <audio>               # audio → texto (faster-whisper, en local)
  python3 cliente.py actualizar '<json>'               # marca cambios/ideas, cambia estado, avisa
  python3 cliente.py mensaje "<texto>"                 # mensaje libre al dueño
  python3 cliente.py subir <video.mp4> <datos.json> <fecha_iso>   # sube a YouTube (privado + publicación programada)

datos.json: {"id": opcional (nueva versión), "tipo": "pelicula"|"short", "titulo", "descripcion", "etiquetas": [...], "nota": opcional}
"""
import json, subprocess, sys, tempfile
from pathlib import Path
import urllib.request

AQUI = Path(__file__).resolve().parent
CONFIG = json.loads((AQUI / "config.json").read_text()) if (AQUI / "config.json").exists() else {}
URL = CONFIG.get("url", "").rstrip("/")
LIMITE_TELEGRAM = 48 * 1024 * 1024          # Telegram admite 50 MB; dejamos margen
CABECERA = {"Authorization": "Bearer proxy-injected"}  # el proxy la sustituye por la clave real


def peticion(ruta, datos=None, metodo=None, crudo=False):
    if not URL:
        sys.exit("Falta la dirección del bot en bot/config.json")
    cuerpo = json.dumps(datos).encode() if datos is not None else None
    req = urllib.request.Request(f"{URL}/api/{ruta}", data=cuerpo, method=metodo or ("POST" if cuerpo else "GET"),
                                 headers={**CABECERA, **({"Content-Type": "application/json"} if cuerpo else {})})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read() if crudo else json.loads(r.read())


def comprimir(video):
    """Versión de revisión que quepa en Telegram: 720p y bitrate ajustado a la duración."""
    if Path(video).stat().st_size <= LIMITE_TELEGRAM:
        return video
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                               capture_output=True, text=True).stdout)
    kbps = int(LIMITE_TELEGRAM * 8 / 1000 / dur * 0.9) - 96
    salida = Path(tempfile.mkdtemp()) / (Path(video).stem + "-revision.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", video, "-vf", "scale=-2:720", "-c:v", "libx264",
                    "-b:v", f"{kbps}k", "-maxrate", f"{kbps}k", "-bufsize", f"{2*kbps}k", "-c:a", "aac", "-b:a", "96k",
                    "-movflags", "+faststart", str(salida)], check=True)
    return str(salida)


def enviar(video, datos_json):
    datos = json.loads(Path(datos_json).read_text())
    video = comprimir(video)
    if Path(video).stat().st_size > LIMITE_TELEGRAM:
        sys.exit("Sigue pesando más de 48 MB: súbelo a otro sitio y pon su dirección en datos['enlace'].")
    # multipart a mano (sin dependencias)
    limite = "----neido" + str(abs(hash(video)))
    partes = [f'--{limite}\r\nContent-Disposition: form-data; name="datos"\r\n\r\n{json.dumps(datos, ensure_ascii=False)}\r\n'.encode()]
    partes.append(f'--{limite}\r\nContent-Disposition: form-data; name="video"; filename="{Path(video).name}"\r\n'
                  f'Content-Type: video/mp4\r\n\r\n'.encode() + Path(video).read_bytes() + b"\r\n")
    partes.append(f"--{limite}--\r\n".encode())
    req = urllib.request.Request(f"{URL}/api/revision", data=b"".join(partes), method="POST",
                                 headers={**CABECERA, "Content-Type": f"multipart/form-data; boundary={limite}"})
    with urllib.request.urlopen(req, timeout=600) as r:
        print(r.read().decode())


def transcribir(audio):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "faster-whisper"], check=True)
        from faster_whisper import WhisperModel
    modelo = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = modelo.transcribe(audio, language="es")
    print(" ".join(s.text.strip() for s in segs))


def subir_youtube(video, datos_json, fecha_iso):
    """Sube el vídeo en PRIVADO con publicación programada (status.publishAt). Necesita googleapis permitido en la red."""
    datos = json.loads(Path(datos_json).read_text())
    token = peticion("youtube-token")
    if not token.get("access_token"):
        sys.exit(f"Sin token de YouTube: {token}")
    meta = {"snippet": {"title": datos["titulo"][:100], "description": datos["descripcion"], "tags": datos.get("etiquetas", []),
                        "categoryId": "1", "defaultLanguage": "es", "defaultAudioLanguage": "es"},
            "status": {"privacyStatus": "private", "publishAt": fecha_iso, "selfDeclaredMadeForKids": False,
                       "containsSyntheticMedia": True}}
    tam = Path(video).stat().st_size
    ini = urllib.request.Request("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                                 data=json.dumps(meta).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {token['access_token']}", "Content-Type": "application/json; charset=UTF-8",
                                          "X-Upload-Content-Length": str(tam), "X-Upload-Content-Type": "video/mp4"})
    with urllib.request.urlopen(ini) as r:
        destino = r.headers["Location"]
    sub = urllib.request.Request(destino, data=Path(video).read_bytes(), method="PUT",
                                 headers={"Authorization": f"Bearer {token['access_token']}", "Content-Type": "video/mp4"})
    with urllib.request.urlopen(sub, timeout=3600) as r:
        res = json.loads(r.read())
    print(json.dumps({"youtube_id": res.get("id"), "estado": res.get("status")}, ensure_ascii=False))


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "enviar": enviar(a[1], a[2])
    elif a[0] == "tareas": print(json.dumps(peticion("tareas"), ensure_ascii=False, indent=2))
    elif a[0] == "voz": Path(a[2]).write_bytes(peticion(f"voz/{a[1]}", crudo=True)); print(a[2])
    elif a[0] == "transcribir": transcribir(a[1])
    elif a[0] == "actualizar": print(peticion("actualizar", json.loads(a[1])))
    elif a[0] == "mensaje": print(peticion("mensaje", {"texto": a[1]}))
    elif a[0] == "subir": subir_youtube(a[1], a[2], a[3])
    else: sys.exit(__doc__)
