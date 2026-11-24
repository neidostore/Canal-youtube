#!/usr/bin/env python3
"""Revisión por Telegram de SHOCK MENTAL (solo este canal), lado del PC.

La configuración vive FUERA del repo, en ~/.canales-youtube/shockmental-bot.json:
  {"telegram_token": "...", "dueno_id": "...", "url": "https://shockmental-revision.xxx.workers.dev", "clave": "..."}
(la crea bot-revision/desplegar.py)

Uso:
  python revision.py quien
      Antes de activar el bot: enseña quién le ha escrito (para sacar tu ID de Telegram).
  python revision.py enviar docs/shockmental/12-ranking06.md --tipo ranking [--id ranking06] [--video ruta.mp4]
      Sube el vídeo a YouTube como PRIVADO (no se publica), te lo manda al bot y pone los botones
      ✅ Aprobar / ✏️ Pedir cambios / ❌ Descartar. Tipos: ranking, short, dosis.
  python revision.py tareas
      Cambios que has pedido desde el bot (los audios se transcriben aquí con Whisper). Salida JSON.
  python revision.py estado ID rehaciendo --nota "🛠️ Aplicando tus cambios…"
  python revision.py ideas [--usar N]
  python revision.py avisar "texto"
"""
import argparse, json, os, subprocess, sys, tempfile, urllib.parse
try:  # usa los certificados de Windows (el antivirus puede inspeccionar las conexiones)
    import truststore; truststore.inject_into_ssl()
except ImportError:
    pass
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import subir_youtube as SY  # noqa: E402

CONF = SY.BASE / "shockmental-bot.json"
CANAL = "shockmental"
LIMITE_TG = 49 * 1024 * 1024   # la API de bots de Telegram admite vídeos de hasta 50 MB


def conf():
    if not CONF.exists():
        sys.exit(f"Falta {CONF}. Se crea al instalar el bot (bot-revision/desplegar.py).")
    return json.loads(CONF.read_text(encoding="utf-8-sig"))


def tg(c, metodo, **kw):
    r = requests.post(f"https://api.telegram.org/bot{c['telegram_token']}/{metodo}", timeout=600, **kw)
    j = r.json()
    if not j.get("ok"):
        raise RuntimeError(f"Telegram {metodo}: {j}")
    return j["result"]


def bot(c, ruta, datos=None, **params):
    url = c["url"].rstrip("/") + "/pc/" + ruta
    h = {"X-Clave": c["clave"]}
    r = requests.post(url, json=datos, headers=h, timeout=60) if datos is not None else requests.get(url, params=params, headers=h, timeout=60)
    j = r.json()
    if not j.get("ok"):
        raise RuntimeError(f"bot /{ruta}: {j}")
    return j


def medidas(video):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                          "-of", "json", str(video)], capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    s = d["streams"][0]
    return int(s["width"]), int(s["height"]), int(float(d["format"]["duration"]))


def para_telegram(video):
    """Si pasa de 49 MB, hace una copia comprimida solo para revisar en el móvil."""
    if video.stat().st_size <= LIMITE_TG:
        return video
    w, h, dur = medidas(video)
    destino = Path(tempfile.gettempdir()) / f"revision-{video.parent.parent.name}.mp4"
    kbps = int((40 * 8 * 1024) / max(dur, 1)) - 128          # ~40 MB en total
    escala = "scale=-2:1280" if h > w else "scale=1280:-2"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", escala, "-c:v", "libx264", "-preset", "medium",
                    "-b:v", f"{max(kbps, 400)}k", "-maxrate", f"{max(kbps, 400) * 2}k", "-bufsize", f"{max(kbps, 400) * 2}k",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(destino)], check=True)
    return destino


def enviar(a):
    c = conf()
    f = SY.leer_ficha(a.ficha)
    video = Path(a.video) if a.video else f["video"]
    if not video or not video.exists():
        sys.exit(f"No encuentro el vídeo: {video}")
    ident = a.id or Path(a.ficha).stem.split("-", 1)[-1]
    h = bot(c, "hueco", tipo=a.tipo, id=ident)
    print(f"Fecha propuesta: {h['fecha_texto']} (España)")

    yt = SY.servicio(CANAL)
    print(f"Subiendo a YouTube como PRIVADO en «{SY.nombre_canal(yt)}» (no se publica)…")
    vid = SY.subir(yt, f, video, "private", None, None, False)

    # El usuario prefiere ver los vídeos en la conversación de Claude; a Telegram solo va el aviso con los botones.
    if a.video_telegram:
        peq = para_telegram(video)
        w, hh, dur = medidas(peq)
        with open(peq, "rb") as fh:
            tg(c, "sendVideo", data={"chat_id": c["dueno_id"], "caption": f"🎬 {f['titulo']}", "width": w, "height": hh,
                                     "duration": dur, "supports_streaming": "true"}, files={"video": fh})
    r = bot(c, "revision", {"id": ident, "tipo": a.tipo, "titulo": f["titulo"], "descripcion": f["descripcion"],
                            "etiquetas": f["etiquetas"], "youtube_id": vid, "fecha_utc": h["fecha_utc"],
                            "para_ninos": f["para_ninos"], "sintetico": f["sintetico"], "comentario": f.get("comentario"),
                            "ficha": str(Path(a.ficha).as_posix())})
    print(f"ENVIADO a revisión: {ident} · versión {r['version']} · {r['fecha_texto']} · https://youtu.be/{vid}")


def transcribir(ruta):
    import numpy as np
    from faster_whisper import WhisperModel
    # el audio se decodifica con ffmpeg (la librería «av» que trae faster-whisper falla con algunas versiones)
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ruta), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0
    modelo = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = modelo.transcribe(audio, language="es", vad_filter=True)
    return " ".join(s.text.strip() for s in segs).strip()


def tareas(a):
    c = conf()
    out = []
    carpeta = SY.BASE / "audios"
    carpeta.mkdir(parents=True, exist_ok=True)
    for t in bot(c, "tareas")["tareas"]:
        cambios = []
        for ch in t.get("cambios", []):
            if ch.get("voz"):
                info = tg(c, "getFile", data={"file_id": ch["voz"]})
                destino = carpeta / f"{t['id']}-{Path(info['file_path']).name}"
                if not destino.exists():
                    r = requests.get(f"https://api.telegram.org/file/bot{c['telegram_token']}/{info['file_path']}", timeout=120)
                    destino.write_bytes(r.content)
                cambios.append({"audio": str(destino), "texto": transcribir(destino)})
            else:
                cambios.append({"texto": ch.get("texto", "")})
        out.append({"id": t["id"], "titulo": t["titulo"], "ficha": t.get("ficha"), "tipo": t.get("tipo"),
                    "version": t.get("version"), "cambios": cambios})
    print(json.dumps(out, ensure_ascii=False, indent=1))


def quien(a):
    c = conf()
    vistos = {}
    for u in tg(c, "getUpdates", data={"timeout": 0}):
        m = u.get("message") or {}
        de = m.get("from")
        if de:
            vistos[de["id"]] = f"{de.get('first_name', '')} {de.get('last_name', '')} @{de.get('username', '')}".strip()
    if not vistos:
        print("Nadie ha escrito al bot todavía (o el webhook ya está activo).")
    for i, n in vistos.items():
        print(f"ID {i}: {n}")


def main():
    p = argparse.ArgumentParser(description="Revisión por Telegram de Shock Mental")
    s = p.add_subparsers(dest="orden", required=True)
    e = s.add_parser("enviar"); e.add_argument("ficha"); e.add_argument("--tipo", required=True, choices=["ranking", "short", "dosis"])
    e.add_argument("--id"); e.add_argument("--video")
    e.add_argument("--video-telegram", action="store_true", help="manda también el vídeo a Telegram (por defecto solo el aviso)")
    s.add_parser("tareas"); s.add_parser("quien")
    st = s.add_parser("estado"); st.add_argument("id"); st.add_argument("estado"); st.add_argument("--nota")
    i = s.add_parser("ideas"); i.add_argument("--usar", type=int, help="marca como usada la idea N (empieza en 1)")
    av = s.add_parser("avisar"); av.add_argument("texto")
    a = p.parse_args()
    if a.orden == "enviar":
        enviar(a)
    elif a.orden == "tareas":
        tareas(a)
    elif a.orden == "quien":
        quien(a)
    elif a.orden == "estado":
        bot(conf(), "estado", {"id": a.id, "estado": a.estado, "nota": a.nota})
        print("ok")
    elif a.orden == "ideas":
        r = bot(conf(), "ideas", {"usar": a.usar - 1}) if a.usar else bot(conf(), "ideas")
        for n, idea in enumerate(r["ideas"], 1):
            print(f"{n}. {idea['texto']}")
    elif a.orden == "avisar":
        bot(conf(), "avisar", {"texto": a.texto})
        print("ok")


if __name__ == "__main__":
    main()
