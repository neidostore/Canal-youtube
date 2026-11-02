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
    import time
    for intento in range(5):  # reintentos si Google da un error temporal (429/5xx)
        try:
            r = json.load(urllib.request.urlopen(req, timeout=120)); break
        except urllib.error.HTTPError as err:
            if err.code not in (429, 500, 502, 503, 504) or intento == 4:
                raise
            time.sleep(2 ** (intento + 1))
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
    if escena["tipo"] == "foto" and escena.get("punch"):
        zb, fx, fy = escena["punch"]
        corte = escena.get("corte", "zoom")
        if corte == "desliza":   # barrido lateral rápido
            x = f"(iw-iw/zoom)*{'on' if fx < 0.5 else f'({n}-on)'}/{n}"
            vf = f"zoompan=z='{zb}':x='{x}':y='(ih-ih/zoom)*{fy}':d={n}:s={W}x{H}:fps={FPS}"
        else:                    # zoom rápido hacia un detalle
            vf = f"zoompan=z='{zb}+0.07*on/{n}':x='(iw-iw/zoom)*{fx}':y='(ih-ih/zoom)*{fy}':d={n}:s={W}x{H}:fps={FPS}"
        if corte == "destello":  # destello blanco muy corto al entrar
            vf += ",fade=t=in:st=0:d=0.12:color=white"
        vf += ",format=yuv420p"
        sh("ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-i", escena["img"], "-vf", vf, "-frames:v", str(n),
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-r", str(FPS), str(destino))
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
            e = {"texto": f["t"], "kw": f.get("kw"), "voz_texto": f.get("voz", f["t"]), "pausa": PAUSA_BLOQUE if i == len(fr) - 1 else PAUSA}
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

    # 5) clips de vídeo (en paralelo). En modo dinámico, cada frase con foto se parte en tomas de ~2 s
    estilo = spec.get("estilo", {})
    dinamico, plano = estilo.get("dinamico", False), estilo.get("plano", 2.0)
    planos = []
    for e in escenas:
        if dinamico and e["tipo"] == "foto" and e["dur"] > plano * 1.4:
            k = max(2, round(e["dur"] / plano)); d = e["dur"] / k
            for j in range(k):
                p = dict(e, ini=e["ini"] + j * d, dur=d)
                if j > 0:
                    p["punch"] = (round(random.uniform(1.25, 1.45), 2), round(random.uniform(0.15, 0.85), 2),
                                  round(random.uniform(0.2, 0.8), 2))
                    p["corte"] = random.choices(["zoom", "desliza", "destello"], weights=[5, 3, 1])[0]
                planos.append(p)
        else:
            planos.append(e)
    for i, e in enumerate(planos):
        h = hashlib.md5(f"{e['img']}|{e['dur']:.3f}|{e.get('movimiento')}|{e.get('punch')}|{e.get('corte')}".encode()).hexdigest()[:10]
        e["clip"] = trabajo / "clips" / f"{i:03d}_{h}.mp4"
    with cf.ThreadPoolExecutor(4) as ex:
        list(ex.map(lambda e: clip(e, e["clip"]), planos))
    (trabajo / "clips.txt").write_text("".join(f"file '{e['clip']}'\n" for e in planos))
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
           "120,120,90,1\n"
           "Style: KW,Inter Display Black,150,&H0000C4FF,&H0000C4FF,&H00000000,&H96000000,0,0,0,0,100,100,-2,0,1,9,5,5,"
           "100,100,0,1\n"
           "Style: KWB,Inter Display Black,120,&H00130F0E,&H00130F0E,&H0000C4FF,&H0000C4FF,0,0,0,0,100,100,-1,0,3,22,0,5,"
           "100,100,0,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    kw_ev = []
    for e in escenas:
        if e.get("kw") and e["texto"]:
            primera = e["kw"].split()[0].lower().strip("¿?¡!.,")
            pos = e["texto"].lower().find(primera)
            t0 = e["ini"] + (e["voz_dur"] * pos / len(e["texto"]) if pos > 0 else 0.1)
            t1 = min(t0 + 1.5, e["ini"] + e["dur"] - 0.05)
            kw_ev.append((t0, t1, e["kw"].upper()))
    def anim(i):  # alterna estilo (texto amarillo / caja amarilla) y altura
        y = (470, 330, 430)[i % 3]
        rot = ("", r"\frz-3", r"\frz2")[i % 3]
        return (f"{{\\pos(960,{y}){rot}\\fscx40\\fscy40\\t(0,110,\\fscx118\\fscy118)"
                f"\\t(110,200,\\fscx100\\fscy100)\\fad(0,120)}}")
    (trabajo / "subs.ass").write_text(cab + "".join(
        f"Dialogue: 0,{ts(a, '.')},{ts(b, '.')},Sub,,0,0,0,,{txt}\n" for a, b, txt in ass_ev) + "".join(
        f"Dialogue: 1,{ts(a, '.')},{ts(b, '.')},{'KWB' if i % 2 else 'KW'},,0,0,0,,{anim(i)}{txt}\n"
        for i, (a, b, txt) in enumerate(kw_ev)), encoding="utf-8")

    # 6b) efectos de sonido: "whoosh" en cada corte y "pop" en palabras clave y tarjetas
    pistas_extra = []
    if dinamico:
        import numpy as np, wave
        SR = 48000; total_n = int((t + 1) * SR); fx_buf = np.zeros(total_n, dtype=np.float32)
        EF = RAIZ / "efectos"
        def cargar(nombre):
            with wave.open(str(EF / f"{nombre}.wav")) as w:
                return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32767
        lib = {n: cargar(n) for n in ["whoosh1", "whoosh2", "whoosh3", "whoosh4", "swipe", "pop1", "pop2", "pop3",
                                      "click", "ding", "caja", "subida", "tictac"]}
        VOL = {"whoosh": 0.11, "swipe": 0.10, "pop": 0.22, "click": 0.25, "ding": 0.22, "caja": 0.24,
               "subida": 0.13, "tictac": 0.22}
        ultimo = {"v": None}
        def elegir(opciones):  # nunca el mismo sonido dos veces seguidas
            o = [x for x in opciones if x != ultimo["v"]] or opciones
            ultimo["v"] = random.choice(o); return ultimo["v"]
        def poner(nombre, t_seg):
            snd = lib[nombre] * VOL[nombre.rstrip("0123456789")]
            i0 = int(max(0, t_seg) * SR); i1 = min(total_n, i0 + len(snd))
            fx_buf[i0:i1] += snd[: i1 - i0]
        for p in planos[1:]:
            if p["tipo"] != "intro":
                poner(elegir(["whoosh1", "whoosh2", "whoosh3", "whoosh4", "swipe"]), p["ini"] - 0.12)
        for a, _, _ in kw_ev:
            poner(elegir(["pop1", "pop2", "pop3", "click"]), a)
        for e in escenas:
            if e["tipo"] != "card" or not e.get("texto"):
                continue
            c = tarjetas[e["card"]]; tipo = c.get("tipo")
            if tipo == "cifra":
                poner("caja" if any(m in c.get("cifra", "") for m in "$€£") else "ding", e["ini"])
            elif tipo == "barras":
                poner("caja", e["ini"])
            elif tipo == "anio":
                poner("tictac", e["ini"])
            elif tipo == "cita":
                poner("subida", e["ini"] - 0.55)
            elif tipo == "lista":
                poner("click", e["ini"])
            else:
                poner(elegir(["pop1", "pop2", "pop3"]), e["ini"])
        with wave.open(str(trabajo / "efectos.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(fx_buf, -1, 1) * 32767).astype(np.int16).tobytes())
        pistas_extra.append((trabajo / "efectos.wav", 1.0))
    if spec.get("musica"):
        m = spec["musica"]
        pistas_extra.append((RAIZ / m["archivo"], m.get("volumen", 0.10)))

    # 7) montaje final: vídeo + subtítulos + voz (normalizada)
    entradas, mezcla = ["-i", str(trabajo / "video_mudo.mp4"), "-i", str(trabajo / "narracion.wav")], "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[v0];"
    etiquetas = ["[v0]"]
    for k, (f, vol) in enumerate(pistas_extra, start=2):
        bucle = ["-stream_loop", "-1"] if "musica" in str(f) else []
        entradas += [*bucle, "-i", str(f)]
        fade = f",afade=t=in:d=2,afade=t=out:st={max(0, t-3):.2f}:d=3" if bucle else ""
        mezcla += f"[{k}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={vol},atrim=0:{t:.2f}{fade}[x{k}];"
        etiquetas.append(f"[x{k}]")
    mezcla += "".join(etiquetas) + f"amix=inputs={len(etiquetas)}:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11[a]"
    sh("ffmpeg", "-y", *entradas,
       "-filter_complex", f"[0:v]ass={trabajo / 'subs.ass'}[vv];{mezcla}", "-map", "[vv]", "-map", "[a]",
       "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
       "-c:a", "aac", "-b:a", "192k", "-shortest", str(salida / "video.mp4"))
    caps = [(e["ini"], e["bloque"]) for e in escenas if e.get("bloque")]
    (salida / "capitulos.txt").write_text("".join(f"{int(a//60):02d}:{int(a%60):02d} {n}\n" for a, n in caps))
    print(f"OK: {salida / 'video.mp4'}  ({t/60:.1f} min, {len(escenas)} escenas)")


if __name__ == "__main__":
    main(sys.argv[1])
