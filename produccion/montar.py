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
MARCO = None      # plantilla "marco" (barras, cuenta atrás, transiciones…): ver marco.py
ENCAJE = set()    # fotos que no llenan la pantalla: van sobre fondo animado
PAUSA, PAUSA_BLOQUE = 0.15, 0.45
RAIZ = Path(__file__).resolve().parent
INTRO_VIDEO = RAIZ.parent / "marca" / "intro" / "intro.mp4"
INTRO_AUDIO = RAIZ.parent / "marca" / "intro" / "intro_audio.wav"
CLIPS = RAIZ / "clips"


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
    out = trabajo / f"foto_{nombre}_{W}x{H}.jpg"
    if out.exists():
        if MARCO:
            with Image.open(out) as _i:
                if _i.width < 2000:
                    ENCAJE.add(nombre)
        return out
    im = Image.open(src).convert("RGB")
    for (x, y, w, h) in difuminar.get(nombre, []):
        box = tuple(int(v) for v in (x * im.width, y * im.height, (x + w) * im.width, (y + h) * im.height))
        im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(18)), box)
    if H > W and im.width > im.height:
        # vertical (Shorts) con foto horizontal: foto entera en el centro sobre una copia desenfocada
        bg = im.resize((1620, 2880)).filter(ImageFilter.GaussianBlur(60))
        bg = Image.eval(bg, lambda v: int(v * 0.55))
        fg = im.resize((1620, round(im.height * 1620 / im.width)), Image.LANCZOS)
        bg.paste(fg, (0, (2880 - fg.height) // 2 - 90))
        bg.save(out, quality=92)
        return out
    if MARCO and (im.width < 1500 or im.width / im.height < 1.45):
        ENCAJE.add(nombre)          # pequeña o poco apaisada: entera, con borde, sobre fondo animado
        k = min(H * 0.84 / im.height, W * 0.72 / im.width)
        im = im.resize((round(im.width * k / 2) * 2, round(im.height * k / 2) * 2), Image.LANCZOS)
        marco_b = Image.new("RGB", (im.width + 24, im.height + 24), "white"); marco_b.paste(im, (12, 12))
        marco_b.save(out, quality=93)
        return out
    # recorte tipo "cover" con margen para el zoom (2880x1620 en 16:9)
    tw, th = (2880, round(2880 * H / W / 2) * 2) if W > H else (1620, 2880)
    s = max(tw / im.width, th / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    l, t = (im.width - tw) // 2, (im.height - th) // 2
    im.crop((l, t, l + tw, t + th)).save(out, quality=92)
    return out


def render_tarjetas(tarjetas, trabajo, plantilla="tarjetas.html"):
    pend = {k: v for k, v in tarjetas.items() if not (trabajo / f"card_{k}.png").exists()}
    if not pend:
        return
    (trabajo / "tarjetas.json").write_text(json.dumps(pend, ensure_ascii=False))
    subprocess.run(["node", str(RAIZ / "render_tarjetas.js"), str(trabajo / "tarjetas.json"), str(trabajo), plantilla],
                   check=True)


def clip(escena, destino):
    if destino.exists():
        return
    d = escena["dur"]
    n = max(1, round(d * FPS))
    if escena["tipo"] == "intro":
        sh("ffmpeg", "-y", "-i", escena["img"], "-an", "-vf", f"fps={FPS},scale={W}:{H},format=yuv420p",
           "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(destino))
        return
    if escena["tipo"] == "video" and H > W:
        # vertical (Shorts): clip grande en el centro sobre una copia desenfocada que llena la pantalla
        off = escena.get("offset", 0.0)
        z = escena["punch"][0] if escena.get("punch") else 1.0
        fw = int(W * 1.4 * z) // 2 * 2
        flash = ",fade=t=in:st=0:d=0.12:color=white" if escena.get("corte") == "destello" else ""
        fc = (f"[0:v]split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"boxblur=24:2,eq=brightness=-0.18[bg];[b]scale={fw}:-2,crop={W}:ih[fg];"
              f"[bg][fg]overlay=(W-w)/2:(H-h)/2-60{flash},fps={FPS},format=yuv420p[v]")
        sh("ffmpeg", "-y", "-stream_loop", "-1", "-ss", f"{off:.2f}", "-i", escena["img"], "-an",
           "-filter_complex", fc, "-map", "[v]", "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "18", str(destino))
        return
    if escena["tipo"] == "video":
        off = escena.get("offset", 0.0)
        vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
        if escena.get("punch"):   # en tomas siguientes, encuadre más cerrado
            zb, fx, fy = escena["punch"]; zw, zh = int(W * zb), int(H * zb)
            vf = (f"scale={zw}:{zh}:force_original_aspect_ratio=increase,"
                  f"crop={W}:{H}:(iw-{W})*{fx}:(ih-{H})*{fy}")
        if escena.get("corte") == "destello":
            vf += ",fade=t=in:st=0:d=0.12:color=white"
        sh("ffmpeg", "-y", "-stream_loop", "-1", "-ss", f"{off:.2f}", "-i", escena["img"], "-an",
           "-vf", f"{vf},fps={FPS},format=yuv420p", "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "18", str(destino))
        return
    if escena["tipo"] == "foto" and escena.get("foto") in ENCAJE:
        # foto entera sobre fondo de color animado con confeti; entra con un pequeño rebote y zoom suave
        z0 = 0.9 if escena.get("toma", 0) % 2 == 0 else 1.0
        fc = (f"[0:v]fps={FPS},scale={W}:{H}[bg];"
              f"[1:v]scale=w='iw*({z0}+0.1*min(1,n/{n}))':h=-2:eval=frame[fg];"
              f"[bg][fg]overlay=(W-w)/2:(H-h)/2+max(0\\,1-n/5)*70:shortest=0,format=yuv420p[v]")
        sh("ffmpeg", "-y", "-stream_loop", "-1", "-i", escena["fondo"], "-loop", "1", "-framerate", str(FPS),
           "-i", escena["img"], "-filter_complex", fc, "-map", "[v]", "-frames:v", str(n), "-c:v", "libx264",
           "-preset", "veryfast", "-crf", "18", "-r", str(FPS), str(destino))
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
        vf = (f"scale={int(W*1.5)}:{int(H*1.5)}:force_original_aspect_ratio=increase,crop={int(W*1.5)}:{int(H*1.5)},zoompan=z='1+0.03*on/{n}':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2'"
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
    global W, H
    if spec.get("formato") == "vertical":   # Shorts: 1080x1920
        W, H = 1080, 1920
    vertical = H > W
    global MARCO
    if spec.get("marco") and not vertical:
        import marco as MK
        MARCO = spec["marco"]; H = MK.HC      # el vídeo va entre las dos barras
    fotos_dir = carpeta / "fotos"; fotos_dir.mkdir(exist_ok=True)
    trabajo = carpeta / "trabajo"; trabajo.mkdir(exist_ok=True)
    (trabajo / "tts").mkdir(exist_ok=True); (trabajo / "clips").mkdir(exist_ok=True)
    salida = carpeta / "salida"; salida.mkdir(exist_ok=True)
    key, voz = clave(), spec["voz"]
    random.seed(7)

    # 1) escenas planas
    escenas, tarjetas = [], {}
    for nb, b in enumerate(spec["bloques"]):
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
            e["nb"] = nb
            for extra in ("sfx", "rotulo", "recuadro"):
                if f.get(extra):
                    e[extra] = f[extra]
            if "card" in f:
                k = hashlib.md5(json.dumps(f["card"], sort_keys=True).encode()).hexdigest()[:10]
                tarjetas[k] = f["card"]; e.update(tipo="card", card=k)
            elif "vid" in f:
                lv = f["vid"] if isinstance(f["vid"], list) else [f["vid"]]
                e.update(tipo="video", vid=lv[0], vids=lv, movimiento=random.randint(0, 3))
            else:
                lst = f["img"] if isinstance(f["img"], list) else [f["img"]]
                e.update(tipo="foto", foto=lst[0], fotos=lst, movimiento=random.randint(0, 3))
            escenas.append(e)
        escenas[inicio_bloque]["bloque"] = b["nombre"]

    # 2) fotos y tarjetas
    usadas = {n for e in escenas if e["tipo"] == "foto" for n in e["fotos"]}
    with cf.ThreadPoolExecutor(6) as ex:
        rutas = dict(zip(usadas, ex.map(lambda n: preparar_foto(n, spec["fotos"][n], fotos_dir, trabajo,
                                                                spec.get("difuminar", {})), usadas)))
    render_tarjetas(tarjetas, trabajo, spec.get("tarjetas", "tarjetas.html"))
    global INTRO_VIDEO, INTRO_AUDIO
    if spec.get("intro"):
        INTRO_VIDEO, INTRO_AUDIO = RAIZ.parent / spec["intro"]["video"], RAIZ.parent / spec["intro"]["audio"]
    vids = {v for e in escenas if e["tipo"] == "video" for v in e["vids"]}
    faltan = [str(spec["videos"][v]) for v in vids if not (CLIPS / f"{spec['videos'][v]}.mp4").exists()]
    if faltan:
        subprocess.run(["bash", str(CLIPS / "descargar.sh"), *faltan], cwd=CLIPS, check=True)
    dur_clip = {v: duracion(CLIPS / f"{spec['videos'][v]}.mp4") for v in vids}

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
        if e["tipo"] == "video":
            e["img"] = str(CLIPS / f"{spec['videos'][e['vid']]}.mp4")
        else:
            e["img"] = str(rutas[e["foto"]] if e["tipo"] == "foto" else trabajo / f"card_{e['card']}.png")
        t += e["dur"]
    (trabajo / "audio.txt").write_text("".join(f"file '{p}'\n" for p in lista_audio))
    sh("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(trabajo / "audio.txt"), "-c:a", "pcm_s16le",
       str(trabajo / "narracion.wav"))

    # 5) clips de vídeo (en paralelo). En modo dinámico, cada frase con foto se parte en tomas de ~2 s
    estilo = spec.get("estilo", {})
    dinamico, plano = estilo.get("dinamico", False), estilo.get("plano", 2.0)
    planos = []
    inicios = spec.get("videos_inicio", {})   # segundo del clip donde empieza lo importante (p. ej. una reacción)
    for e in escenas:
        if dinamico and e["tipo"] in ("foto", "video") and e["dur"] > plano * 1.4:
            k = max(2, round(e["dur"] / plano)); d = e["dur"] / k
            for j in range(k):
                p = dict(e, ini=e["ini"] + j * d, dur=d, toma=j)
                if e["tipo"] == "video" and len(e["vids"]) > 1:   # varios clips: uno por toma
                    p["vid"] = e["vids"][j % len(e["vids"])]
                    p["img"] = str(CLIPS / f"{spec['videos'][p['vid']]}.mp4")
                if e["tipo"] == "foto" and len(e["fotos"]) > 1:   # varias fotos reales: una por toma
                    p["foto"] = e["fotos"][j % len(e["fotos"])]; p["img"] = str(rutas[p["foto"]])
                    p["movimiento"] = random.randint(0, 3)
                if e["tipo"] == "video":
                    lim = max(0.5, dur_clip[p["vid"]] - d - 0.2)
                    if p["vid"] in inicios:
                        k_mismo = sum(1 for jj in range(j) if e["vids"][jj % len(e["vids"])] == p["vid"])
                        p["offset"] = round(min(inicios[p["vid"]] + k_mismo * d, lim), 2); p.pop("punch", None)
                    else:
                        p["offset"] = round((j * 2.7 + random.uniform(0, 3)) % lim, 2)
                varios = len(e["fotos"] if e["tipo"] == "foto" else e["vids"])
                if j > 0 and not (varios > 1 and j < varios) and not (e["tipo"] == "video" and p["vid"] in inicios):
                    p["punch"] = (round(random.uniform(1.25, 1.45), 2), round(random.uniform(0.15, 0.85), 2),
                                  round(random.uniform(0.2, 0.8), 2))
                    p["corte"] = random.choices(["zoom", "desliza", "destello"], weights=[5, 3, 1])[0]
                planos.append(p)
        else:
            if e["tipo"] == "video":
                lim = max(0.0, dur_clip[e["vid"]] - e["dur"] - 0.2)
                e["offset"] = round(min(inicios[e["vid"]], lim) if e["vid"] in inicios else random.uniform(0, lim), 2)
            planos.append(e)
    if MARCO:
        (trabajo / "marco").mkdir(exist_ok=True)
        colores = MARCO.get("colores", MK.COLORES)
        for e in planos:
            if e["tipo"] == "foto" and e["foto"] in ENCAJE:
                e["img"] = str(rutas[e["foto"]])
                col = colores[e.get("nb", 0) % len(colores)]
                e["fondo"] = str(trabajo / "marco" / f"fondo_{col.lstrip('#')}.mp4")
                MK.fondo_animado(Path(e["fondo"]), col)
    for i, e in enumerate(planos):
        h = hashlib.md5(f"{W}x{H}|{e.get('fondo')}|{e.get('toma')}|{e['img']}|{e['dur']:.3f}|{e.get('movimiento')}|{e.get('punch')}|{e.get('corte')}|{e.get('offset')}".encode()).hexdigest()[:10]
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
        partes = trozos(e["texto"], 22 if vertical else 34); total = sum(len(p) for p in partes); t0 = e["ini"]
        for p in partes:
            d = e["voz_dur"] * len(p) / total
            srt.append((t0, t0 + d, p))
            if e["tipo"] in ("foto", "video"):
                ass_ev.append((t0, t0 + d, p))
            t0 += d
    (salida / "subtitulos.srt").write_text(
        "\n".join(f"{i}\n{ts(a)} --> {ts(b)}\n{txt}\n" for i, (a, b, txt) in enumerate(srt, 1)), encoding="utf-8")
    kwb_txt, kwb_box = ("&H00FFFFFF", "&H00FF8C1E") if spec.get("tema") == "shock" else ("&H00130F0E", "&H0000C4FF")
    sub_m, kw1, kw2 = ("70,70,560", 118, 96) if vertical else ("120,120,90", 150, 120)
    cab = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {W}\nPlayResY: {H}\n\n[V4+ Styles]\n"
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
           "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
           "MarginR, MarginV, Encoding\n"
           "Style: Sub,Inter Display Black,74,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,6,3,2,"
           f"{sub_m},1\n"
           f"Style: KW,Inter Display Black,{kw1},&H0000C4FF,&H0000C4FF,&H00000000,&H96000000,0,0,0,0,100,100,-2,0,1,9,5,5,"
           "100,100,0,1\n"
           f"Style: Cred,Inter Display,30,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,2,1,{7 if MARCO else 9},40,40,{24 if MARCO else 36},1\n"
           f"Style: KWB,Inter Display Black,{kw2},{kwb_txt},{kwb_txt},{kwb_box},{kwb_box},0,0,0,0,100,100,-1,0,3,22,0,5,"
           "100,100,0,1\n"
           "Style: Rot,Inter Display Black,84,&H00130F0E,&H00130F0E,&H0000C4FF,&H0000C4FF,0,0,0,0,100,100,0,0,3,18,0,1,0,0,0,1\n"
           "Style: RotA,Inter Display Black,40,&H00FFFFFF,&H00FFFFFF,&H00FF8C1E,&H00FF8C1E,0,0,0,0,100,100,1,0,3,12,0,1,0,0,0,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    cred_ev = [(e["ini"], e["ini"] + e["dur"], spec["credito_fotos"][e["foto"]]) for e in planos
               if e["tipo"] == "foto" and e["foto"] in spec.get("credito_fotos", {})]
    cred_ev += [(e["ini"], e["ini"] + e["dur"], spec["credito_videos"][e["vid"]]) for e in planos
                if e["tipo"] == "video" and e["vid"] in spec.get("credito_videos", {})]
    kw_ev = []
    for e in escenas:
        if e.get("kw") and e["texto"]:
            primera = e["kw"].split()[0].lower().strip("¿?¡!.,")
            pos = e["texto"].lower().find(primera)
            t0 = e["ini"] + (e["voz_dur"] * pos / len(e["texto"]) if pos > 0 else 0.1)
            t1 = min(t0 + 1.5, e["ini"] + e["dur"] - 0.05)
            kw_ev.append((t0, t1, e["kw"].upper()))
    rot_ev = []   # rótulos tipo tele (abajo a la izquierda): etiqueta pequeña + cifra o nombre en grande
    for e in escenas:
        if e.get("rotulo") and e.get("texto"):
            r = e["rotulo"] if isinstance(e["rotulo"], dict) else {"texto": e["rotulo"]}
            a = e["ini"] + r.get("en", 0.35); b = e["ini"] + e["dur"] - 0.1; yb = H - 190
            mv = lambda y: f"{{\\an1\\move(-900,{y},70,{y},0,260)\\fad(0,150)}}"
            rot_ev.append((a, b, "Rot", mv(yb) + r["texto"]))
            if r.get("arriba"):
                rot_ev.append((a + 0.12, b, "RotA", mv(yb - 112) + r["arriba"].upper()))
    def anim(i):  # alterna estilo (texto amarillo / caja amarilla) y altura
        y = ((760, 600, 700) if vertical else (470, 330, 430))[i % 3]
        if MARCO:
            y = int(y * H / 1080)
        rot = ("", r"\frz-3", r"\frz2")[i % 3]
        return (f"{{\\pos({W // 2},{y}){rot}\\fscx40\\fscy40\\t(0,110,\\fscx118\\fscy118)"
                f"\\t(110,200,\\fscx100\\fscy100)\\fad(0,120)}}")
    (trabajo / "subs.ass").write_text(cab + "".join(
        f"Dialogue: 0,{ts(a, '.')},{ts(b, '.')},Sub,,0,0,0,,{txt}\n" for a, b, txt in ass_ev) + "".join(
        f"Dialogue: 1,{ts(a, '.')},{ts(b, '.')},{'KWB' if i % 2 else 'KW'},,0,0,0,,{anim(i)}{txt}\n"
        for i, (a, b, txt) in enumerate(kw_ev)) + "".join(
        f"Dialogue: 2,{ts(a, '.')},{ts(b, '.')},Cred,,0,0,0,,{txt}\n" for a, b, txt in cred_ev) + "".join(
        f"Dialogue: 3,{ts(a, '.')},{ts(b, '.')},{st},,0,0,0,,{txt}\n" for a, b, st, txt in rot_ev), encoding="utf-8")

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
        VOL = {"whoosh": 0.08, "swipe": 0.08, "pop": 0.22, "click": 0.25, "ding": 0.22, "caja": 0.24,
               "subida": 0.13, "tictac": 0.22}
        ultimo = {"v": None}
        def elegir(opciones):  # nunca el mismo sonido dos veces seguidas
            o = [x for x in opciones if x != ultimo["v"]] or opciones
            ultimo["v"] = random.choice(o); return ultimo["v"]
        def poner(nombre, t_seg):
            snd = lib[nombre] * VOL[nombre.rstrip("0123456789")]
            i0 = int(max(0, t_seg) * SR); i1 = min(total_n, i0 + len(snd))
            fx_buf[i0:i1] += snd[: i1 - i0]
        # "whoosh" solo en momentos clave: inicio de sección siempre; cambio de frase a veces (≥6 s de separación)
        ultimo_w = -99.0
        for p in planos[1:]:
            if p["tipo"] == "intro" or p.get("toma", 0) > 0:
                continue
            seccion = bool(p.get("bloque"))
            if seccion or (p["ini"] - ultimo_w >= 6 and random.random() < 0.35):
                poner(elegir(["whoosh1", "whoosh2", "whoosh3", "whoosh4", "swipe"]), p["ini"] - 0.12)
                ultimo_w = p["ini"]
        for a, _, _ in kw_ev:
            poner(elegir(["pop1", "pop2", "pop3", "click"]), a)
        for a, _, st, _ in rot_ev:
            if st == "Rot":
                poner("ding", a)
        for e in escenas:
            if e.get("recuadro"):
                poner(elegir(["pop1", "pop2", "pop3"]), e["ini"] + e["recuadro"].get("en", 0.5))
        for e in escenas:   # sonidos reales por frase (p. ej. un cuervo graznando), sincronizados con el clip
            if e.get("sfx"):
                fx = e["sfx"]; snd = cargar(fx["nombre"]) * fx.get("vol", 0.5)
                i0 = int((e["ini"] + fx.get("en", 0)) * SR); i1 = min(total_n, i0 + len(snd))
                fx_buf[i0:i1] += snd[: i1 - i0]
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
    video_fc = f"[0:v]ass={trabajo / 'subs.ass'}[vv]"
    if MARCO:
        mdir = trabajo / "marco"; n_in = len(entradas) // 2 + sum(1 for x in entradas if x == "-stream_loop") * 0
        n_in = sum(1 for x in entradas if x == "-i")
        def render_html(html, png, w, h):
            subprocess.run(["node", str(RAIZ / "render_html.js"), str(html), str(png), str(w), str(h)], check=True)
        if not (mdir / "marco.png").exists():
            MK.marco_png(mdir / "marco.png", MARCO, RAIZ.parent, render_html)
        B = MK.BARRA; capas = []          # (entrada extra, inicio, expresión de overlay)
        entradas += ["-i", str(mdir / "marco.png")]; i_marco = n_in; n_in += 1
        for k, e in enumerate(x for x in escenas if x.get("recuadro")):
            r = e["recuadro"]; png = mdir / f"recuadro_{k}.png"
            MK.recuadro(png, fotos_dir / f"{r.get('img', e.get('foto'))}.jpg", r)
            ini = e["ini"] + r.get("en", 0.5); d = e["ini"] + e["dur"] - ini - 0.05
            entradas += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.2f}", "-i", str(png)]
            capas.append((n_in, ini, f"format=rgba,fade=t=in:st=0:d=0.18:alpha=1,fade=t=out:st={d - 0.15:.2f}:d=0.15:alpha=1")); n_in += 1
        cortes = [e["ini"] for e in escenas[1:] if e.get("bloque")]
        for k, tc in enumerate(cortes):   # transición con logo en cada cambio de dato
            col = colores[k % len(colores)]; col2 = colores[(k + 2) % len(colores)]
            tdir = mdir / f"trans_{col.lstrip('#')}"
            MK.transicion(tdir, col, col2, RAIZ.parent / MARCO["logo"])
            entradas += ["-framerate", str(FPS), "-i", str(tdir / "%02d.png")]
            capas.append((n_in, max(0, tc - MK.MEDIO / FPS), "format=rgba")); n_in += 1
        fuente = MK.F_BLACK
        cuenta = (f"drawtext=fontfile={fuente}:fontsize=58:fontcolor=0x130F0E:x=1920-28-95-tw/2:y={B + 18 + 39}-th/2:"
                  f"text='%{{eif\\:max(0\\,trunc(({t:.2f}-t)/60))\\:d}}\\:%{{eif\\:max(0\\,mod(trunc({t:.2f}-t)\\,60))\\:d\\:2}}'")
        video_fc += f";[vv]pad={W}:1080:0:{B}:color=black[c0]"
        ult = "c0"
        for j, (idx, ini, pre) in enumerate(capas):
            video_fc += (f";[{idx}:v]{pre},setpts=PTS-STARTPTS+{ini:.3f}/TB[k{j}];"
                         f"[{ult}][k{j}]overlay=0:{B}:eof_action=pass[c{j + 1}]")
            ult = f"c{j + 1}"
        video_fc += f";[{ult}][{i_marco}:v]overlay=0:0,{cuenta}[vfin]"
    sh("ffmpeg", "-y", *entradas,
       "-filter_complex", f"{video_fc};{mezcla}", "-map", "[vfin]" if MARCO else "[vv]", "-map", "[a]",
       "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
       "-c:a", "aac", "-b:a", "192k", "-shortest", str(salida / "video.mp4"))
    caps = [(e["ini"], e["bloque"]) for e in escenas if e.get("bloque")]
    (salida / "capitulos.txt").write_text("".join(f"{int(a//60):02d}:{int(a%60):02d} {n}\n" for a, n in caps))
    print(f"OK: {salida / 'video.mp4'}  ({t/60:.1f} min, {len(escenas)} escenas)")


if __name__ == "__main__":
    main(sys.argv[1])
