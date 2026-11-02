#!/usr/bin/env python3
"""Monta un vídeo de Detrás del Precio a partir de escenas.json.

Uso:  GOOGLE_TTS_API_KEY=... python3 produccion/montar.py produccion/video01
      (o la clave en el archivo indicado por GOOGLE_TTS_KEY_FILE)

Genera en <carpeta>/salida/: video.mp4, subtitulos.srt
Necesita: ffmpeg, Pillow, Node + Playwright (Chromium) y acceso a images.pexels.com y texttospeech.googleapis.com.
"""
import base64, concurrent.futures as cf, hashlib, json, os, random, subprocess, sys, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image, ImageFilter

W, H, FPS = 1920, 1080, 30
PAUSA, PAUSA_BLOQUE = 0.15, 0.45
RAIZ = Path(__file__).resolve().parent
INTRO_VIDEO = RAIZ.parent / "marca" / "intro" / "intro.mp4"
INTRO_AUDIO = RAIZ.parent / "marca" / "intro" / "intro_audio.wav"


def sh(*args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def duracion(f):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def clave():
    k = os.environ.get("GOOGLE_TTS_API_KEY", "").strip()
    if not k and os.environ.get("GOOGLE_TTS_KEY_FILE"):
        k = Path(os.environ["GOOGLE_TTS_KEY_FILE"]).read_text().strip()
    if not k:
        sys.exit("Falta la clave de Google TTS (GOOGLE_TTS_API_KEY)")
    return k


def tts(texto, voz, destino, key):
    if destino.exists():
        return
    body = {"input": {"text": texto}, "voice": {"languageCode": voz["idioma"], "name": voz["nombre"]},
            "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 48000,
                            "speakingRate": voz.get("velocidad", 1.0)}}
    req = urllib.request.Request("https://texttospeech.googleapis.com/v1/text:synthesize",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "X-Goog-Api-Key": key})
    r = json.load(urllib.request.urlopen(req, timeout=120))
    destino.write_bytes(base64.b64decode(r["audioContent"]))


def preparar_foto(nombre, pid, fotos_dir, trabajo, difuminar):
    src = fotos_dir / f"{nombre}.jpg"
    if not src.exists():
        url = f"https://images.pexels.com/photos/{pid}/pexels-photo-{pid}.jpeg?auto=compress&cs=tinysrgb&w=2400"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        src.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    out = trabajo / f"foto_{nombre}.jpg"
    if out.exists():
        return out
    im = Image.open(src).convert("RGB")
    for (x, y, w, h) in difuminar.get(nombre, []):
        box = tuple(int(v) for v in (x * im.width, y * im.height, (x + w) * im.width, (y + h) * im.height))
        im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(18)), box)
    # recorte 16:9 tipo "cover" a 2880x1620 (margen para el zoom)
    tw, th = 2880, 1620
    s = max(tw / im.width, th / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    l, t = (im.width - tw) // 2, (im.height - th) // 2
    im.crop((l, t, l + tw, t + th)).save(out, quality=92)
    return out


def render_tarjetas(tarjetas, trabajo):
    pend = {k: v for k, v in tarjetas.items() if not (trabajo / f"card_{k}.png").exists()}
    if not pend:
        return
    (trabajo / "tarjetas.json").write_text(json.dumps(pend, ensure_ascii=False))
    subprocess.run(["node", str(RAIZ / "render_tarjetas.js"), str(trabajo / "tarjetas.json"), str(trabajo)], check=True)


def clip(escena, destino):
    if destino.exists():
        return
    d = escena["dur"]
    n = max(1, round(d * FPS))
    if escena["tipo"] == "intro":
        sh("ffmpeg", "-y", "-i", escena["img"], "-an", "-vf", f"fps={FPS},scale={W}:{H},format=yuv420p",
           "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(destino))
        return
    if escena["tipo"] == "foto":
        modo = escena["movimiento"]
        z = {0: f"1+0.12*on/{n}", 1: f"1.12-0.12*on/{n}"}.get(modo, "1.10")
        if modo == 2:
            x, y = f"(iw-iw/zoom)*on/{n}", "(ih-ih/zoom)/2"
        elif modo == 3:
            x, y = f"(iw-iw/zoom)*(1-on/{n})", "(ih-ih/zoom)/2"
        else:
            x, y = "(iw-iw/zoom)/2", "(ih-ih/zoom)/2"
        vf = f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS},format=yuv420p"
        entrada = ["-loop", "1", "-framerate", str(FPS), "-i", escena["img"]]
    else:
        vf = (f"scale={int(W*1.5)}:{int(H*1.5)},zoompan=z='1+0.03*on/{n}':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2'"
              f":d={n}:s={W}x{H}:fps={FPS},format=yuv420p")
        entrada = ["-loop", "1", "-framerate", str(FPS), "-i", escena["img"]]
    sh("ffmpeg", "-y", *entrada, "-vf", vf, "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast",
       "-crf", "18", "-r", str(FPS), str(destino))


def ts(t, sep=","):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}{sep}{int(round((s % 1) * 1000)) % 1000:03d}" if sep == "," else \
        f"{int(h)}:{int(m):02d}:{s:05.2f}"


def trozos(texto, max_chars=34):
    pal, cur, out = texto.split(), "", []
    for p in pal:
        if cur and len(cur) + 1 + len(p) > max_chars:
            out.append(cur); cur = p
        else:
            cur = f"{cur} {p}".strip()
    if cur:
        out.append(cur)
    return out


def main(carpeta):
    carpeta = Path(carpeta).resolve()
    spec = json.loads((carpeta / "escenas.json").read_text())
    fotos_dir = carpeta / "fotos"; fotos_dir.mkdir(exist_ok=True)
    trabajo = carpeta / "trabajo"; trabajo.mkdir(exist_ok=True)
    (trabajo / "tts").mkdir(exist_ok=True); (trabajo / "clips").mkdir(exist_ok=True)
    salida = carpeta / "salida"; salida.mkdir(exist_ok=True)
    key, voz = clave(), spec["voz"]
    random.seed(7)

    # 1) escenas planas
    escenas, tarjetas = [], {}
    for b in spec["bloques"]:
        inicio_bloque = len(escenas)
        if b.get("intro"):
            escenas.append({"tipo": "intro", "texto": None, "pausa": 0.0, "bloque": b["nombre"]})
            continue
        if "silencio" in b:
            k = hashlib.md5(json.dumps(b["card"], sort_keys=True).encode()).hexdigest()[:10]
            tarjetas[k] = b["card"]
            escenas.append({"tipo": "card", "card": k, "texto": None, "pausa": b["silencio"]})
            continue
        fr = b["frases"]
        for i, f in enumerate(fr):
            e = {"texto": f["t"], "voz_texto": f.get("voz", f["t"]), "pausa": PAUSA_BLOQUE if i == len(fr) - 1 else PAUSA}
            if i == len(fr) - 1 and b.get("final"):
                e["pausa"] += b["final"]
            if "card" in f:
                k = hashlib.md5(json.dumps(f["card"], sort_keys=True).encode()).hexdigest()[:10]
                tarjetas[k] = f["card"]; e.update(tipo="card", card=k)
            else:
                e.update(tipo="foto", foto=f["img"], movimiento=random.randint(0, 3))
            escenas.append(e)
        escenas[inicio_bloque]["bloque"] = b["nombre"]

    # 2) fotos y tarjetas
    usadas = {e["foto"] for e in escenas if e["tipo"] == "foto"}
    with cf.ThreadPoolExecutor(6) as ex:
        rutas = dict(zip(usadas, ex.map(lambda n: preparar_foto(n, spec["fotos"][n], fotos_dir, trabajo,
                                                                spec.get("difuminar", {})), usadas)))
    render_tarjetas(tarjetas, trabajo)

    # 3) voz
    def hacer_tts(e):
        if not e["texto"]:
            return
        h = hashlib.md5((voz["nombre"] + str(voz.get("velocidad", 1.0)) + e["voz_texto"]).encode()).hexdigest()[:12]
        e["wav"] = trabajo / "tts" / f"{h}.wav"
        tts(e["voz_texto"], voz, e["wav"], key)
        e["voz_dur"] = duracion(e["wav"])
    with cf.ThreadPoolExecutor(4) as ex:
        list(ex.map(hacer_tts, escenas))

    # 4) línea de tiempo y pista de audio
    t, lista_audio = 0.0, []
    for i, e in enumerate(escenas):
        if e["tipo"] == "intro":
            e["ini"], e["dur"], e["img"] = t, duracion(INTRO_AUDIO), str(INTRO_VIDEO)
            lista_audio.append(INTRO_AUDIO)
            t += e["dur"]
            continue
        vd = e.get("voz_dur", 0.0)
        e["ini"], e["dur"] = t, vd + e["pausa"]
        if "wav" in e:
            lista_audio.append(e["wav"])
        if e["pausa"] > 0:
            sil = trabajo / "tts" / f"sil_{int(e['pausa']*1000)}.wav"
            if not sil.exists():
                sh("ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", str(e["pausa"]), str(sil))
            lista_audio.append(sil)
        e["img"] = str(rutas[e["foto"]] if e["tipo"] == "foto" else trabajo / f"card_{e['card']}.png")
        t += e["dur"]
    (trabajo / "audio.txt").write_text("".join(f"file '{p}'\n" for p in lista_audio))
    sh("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(trabajo / "audio.txt"), "-c:a", "pcm_s16le",
       str(trabajo / "narracion.wav"))

    # 5) clips de vídeo (en paralelo)
    for i, e in enumerate(escenas):
        h = hashlib.md5(f"{e['img']}|{e['dur']:.3f}|{e.get('movimiento')}".encode()).hexdigest()[:10]
        e["clip"] = trabajo / "clips" / f"{i:03d}_{h}.mp4"
    with cf.ThreadPoolExecutor(4) as ex:
        list(ex.map(lambda e: clip(e, e["clip"]), escenas))
    (trabajo / "clips.txt").write_text("".join(f"file '{e['clip']}'\n" for e in escenas))
    sh("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(trabajo / "clips.txt"), "-c", "copy",
       str(trabajo / "video_mudo.mp4"))

    # 6) subtítulos: SRT completo (para subir a YouTube) y ASS quemado solo en escenas con foto
    srt, ass_ev = [], []
    for e in escenas:
        if not e["texto"]:
            continue
        partes = trozos(e["texto"]); total = sum(len(p) for p in partes); t0 = e["ini"]
        for p in partes:
            d = e["voz_dur"] * len(p) / total
            srt.append((t0, t0 + d, p))
            if e["tipo"] == "foto":
                ass_ev.append((t0, t0 + d, p))
            t0 += d
    (salida / "subtitulos.srt").write_text(
        "\n".join(f"{i}\n{ts(a)} --> {ts(b)}\n{txt}\n" for i, (a, b, txt) in enumerate(srt, 1)), encoding="utf-8")
    cab = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n\n[V4+ Styles]\n"
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
           "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
           "MarginR, MarginV, Encoding\n"
           "Style: Sub,Inter Display Black,74,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,6,3,2,"
           "120,120,90,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    (trabajo / "subs.ass").write_text(cab + "".join(
        f"Dialogue: 0,{ts(a, '.')},{ts(b, '.')},Sub,,0,0,0,,{txt}\n" for a, b, txt in ass_ev), encoding="utf-8")

    # 7) montaje final: vídeo + subtítulos + voz (normalizada)
    sh("ffmpeg", "-y", "-i", str(trabajo / "video_mudo.mp4"), "-i", str(trabajo / "narracion.wav"),
       "-vf", f"ass={trabajo / 'subs.ass'}", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
       "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
       "-c:a", "aac", "-b:a", "192k", "-shortest", str(salida / "video.mp4"))
    caps = [(e["ini"], e["bloque"]) for e in escenas if e.get("bloque")]
    (salida / "capitulos.txt").write_text("".join(f"{int(a//60):02d}:{int(a%60):02d} {n}\n" for a, n in caps))
    print(f"OK: {salida / 'video.mp4'}  ({t/60:.1f} min, {len(escenas)} escenas)")


if __name__ == "__main__":
    main(sys.argv[1])
