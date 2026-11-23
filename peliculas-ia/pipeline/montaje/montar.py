#!/usr/bin/env python3
"""Montaje automático de una película de Neido Studio.

Lee producciones/<id>/planos.json y los archivos generados, y produce la película terminada:
cortinilla → planos (vídeo o imagen fija con movimiento) → bandas 2,39:1, color de la casa,
grano, viñeteado → voces colocadas en cada plano → subtítulos .srt → fundido a negro.

Archivos que espera dentro de producciones/<id>/:
  clips/plano_01.mp4  o  clips/plano_01.png    (uno por plano; el vídeo tiene prioridad)
  audio/plano_01_1.wav, plano_01_2.wav ...      (una por línea de "audio" del plano, opcional)
  musica.mp3                                    (opcional)

Uso:  python3 montar.py <carpeta_produccion> [--sin-cortinilla]
Salida: <carpeta_produccion>/salida/pelicula.mp4 y pelicula.srt
"""
import json, subprocess, sys, shutil
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PIPE = AQUI.parent
FUENTES = PIPE / "fuentes"
F_TITULO = FUENTES / "CormorantGaramond-wght-600.ttf"
F_TEXTO = FUENTES / "Montserrat-wght-500.ttf"
CORTINILLA = PIPE / "cortinilla" / "cortinilla.mp4"
W, H, FPS = 1920, 1080, 24
BANDA = round((H - W / 2.39) / 2)          # alto de cada banda negra (≈138 px)
INICIO_VOZ = 0.3                           # segundos tras el inicio del plano en que entra la voz


def ff(*args):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *map(str, args)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"ffmpeg falló:\n{' '.join(cmd)}\n{r.stderr}")


def duracion(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(f)], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def esc(t):
    """Escapa texto para drawtext."""
    return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def preparar_plano(p, prod, tmp):
    n = p["n"]; d = float(p["duracion"])
    vid, img = prod / "clips" / f"plano_{n:02d}.mp4", prod / "clips" / f"plano_{n:02d}.png"
    out = tmp / f"p{n:02d}.mp4"
    base = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}"
    if vid.exists():
        # si el clip es más corto que el plano, se congela el último fotograma
        filtro = f"{base},tpad=stop_mode=clone:stop_duration={d},trim=duration={d}"
        entrada = ["-i", vid]
    elif img.exists():
        frames = int(d * FPS)
        zoom = {"acercamiento": "min(1+0.0009*on,1.12)", "leve": "min(1+0.0004*on,1.05)",
                "alejamiento": "max(1.12-0.0009*on,1)"}.get(p.get("movimiento", "leve"), "1")
        filtro = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
                  f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},setsar=1")
        entrada = ["-loop", "1", "-t", d, "-i", img]
    else:
        sys.exit(f"Falta el plano {n}: ni {vid.name} ni {img.name}")
    # textos sobre el plano: rótulo de lugar y fecha, o superposición (p. ej. la hora 4:04)
    extra = []
    if p.get("rotulo"):
        r = esc(PROD_DATOS["rotulo"])
        extra.append(f"drawtext=fontfile={F_TEXTO}:text='{r}':fontsize=34:fontcolor=0xEFEAE0:"
                     f"x=120:y=h-{BANDA}-90:alpha='min(1,max(0,(t-0.6)/0.8))*min(1,max(0,({d}-0.4-t)/0.6))'")
    if p.get("superposicion"):
        s = p["superposicion"]
        extra.append(f"drawtext=fontfile={F_TEXTO}:text='{esc(s['texto'])}':fontsize=96:fontcolor=white@0.92:x=(w-tw)/2:y=h/2-110")
        if s.get("subtexto"):
            extra.append(f"drawtext=fontfile={F_TEXTO}:text='{esc(s['subtexto'])}':fontsize=34:fontcolor=white@0.8:x=(w-tw)/2:y=h/2+10")
    if p.get("final") == "negro":
        extra.append(f"fade=t=out:st={d-0.8}:d=0.8")
    filtro = ",".join([filtro, *extra])
    ff(*entrada, "-vf", filtro, "-t", d, "-an", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", out)
    return out


def main():
    global PROD_DATOS
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    prod = Path(sys.argv[1]).resolve()
    con_cortinilla = "--sin-cortinilla" not in sys.argv
    PROD_DATOS = json.loads((prod / "planos.json").read_text())
    tmp = prod / "salida" / "tmp"; shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)

    # 1) cada plano a un clip uniforme
    planos = PROD_DATOS["planos"]
    clips = [preparar_plano(p, prod, tmp) for p in planos]

    # 2) unir: cortinilla (termina en luz) + fundido desde la luz al primer plano + resto por corte
    lista = tmp / "lista.txt"
    lista.write_text("".join(f"file '{c}'\n" for c in clips))
    cuerpo = tmp / "cuerpo.mp4"
    ff("-f", "concat", "-safe", 0, "-i", lista, "-c", "copy", cuerpo)
    desfase = 0.0
    union = tmp / "union.mp4"
    if con_cortinilla and CORTINILLA.exists():
        dc = duracion(CORTINILLA); fundido = 0.5
        ff("-i", CORTINILLA, "-i", cuerpo, "-filter_complex",
           f"[0:v]fps={FPS},scale={W}:{H},setsar=1,format=yuv420p,settb=1/{FPS}[a];[1:v]fps={FPS},format=yuv420p,settb=1/{FPS}[b];"
           f"[a][b]xfade=transition=fade:duration={fundido}:offset={dc-fundido}",
           "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", union)
        desfase = dc - fundido
    else:
        shutil.copy(cuerpo, union)

    # 3) acabado de la casa: color, grano, viñeteado y bandas 2,39:1
    acabado = (f"eq=saturation=0.88:contrast=1.04,curves=all='0/0.035 0.5/0.49 1/0.97',"
               f"noise=alls=7:allf=t,vignette=PI/5,"
               f"drawbox=x=0:y=0:w=iw:h={BANDA}:color=black:t=fill,"
               f"drawbox=x=0:y=ih-{BANDA}:w=iw:h={BANDA}:color=black:t=fill")

    # 4) audio: voces en su sitio + música opcional, y subtítulos
    entradas, retardos, srt, t0, k = [], [], [], desfase, 1
    for p in planos:
        for i, linea in enumerate(p.get("audio", []), 1):
            wav = prod / "audio" / f"plano_{p['n']:02d}_{i}.wav"
            inicio = t0 + INICIO_VOZ
            if wav.exists():
                entradas += ["-i", wav]; retardos.append(int(inicio * 1000))
                fin = inicio + duracion(wav)
                if fin > t0 + float(p["duracion"]) + 0.05:
                    print(f"⚠️  Plano {p['n']}: la voz {i} dura más que el plano ({fin - t0:.1f} s > {p['duracion']} s)")
            else:
                fin = inicio + max(1.5, len(linea["texto"]) / 15)
            texto = linea["texto"] if linea.get("tipo") != "pensamiento" else f"({linea['texto']})"
            srt.append(f"{k}\n{ts(inicio)} --> {ts(fin)}\n{texto}\n"); k += 1
        t0 += float(p["duracion"])
    total = t0
    musica = prod / "musica.mp3"
    filtros, etiquetas = [], []
    for j, r in enumerate(retardos):
        filtros.append(f"[{j+1}:a]aresample=48000,adelay={r}|{r},volume=1.0[v{j}]"); etiquetas.append(f"[v{j}]")
    if musica.exists():
        entradas += ["-i", musica]; m = len(retardos) + 1
        filtros.append(f"[{m}:a]aresample=48000,volume=0.18,afade=t=out:st={total-2}:d=2[mu]"); etiquetas.append("[mu]")
    salida = prod / "salida" / "pelicula.mp4"
    if etiquetas:
        filtros.append(f"{''.join(etiquetas)}amix=inputs={len(etiquetas)}:normalize=0,apad[aud]")
        ff("-i", union, *entradas, "-filter_complex", ";".join(filtros) + f";[0:v]{acabado}[vid]",
           "-map", "[vid]", "-map", "[aud]", "-t", total, "-c:v", "libx264", "-crf", "18",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", salida)
    else:
        ff("-i", union, "-vf", acabado, "-t", total, "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", salida)
    (prod / "salida" / "pelicula.srt").write_text("\n".join(srt), encoding="utf-8")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"Película lista: {salida} ({total:.1f} s)")


def ts(s):
    h, s = divmod(s, 3600); m, s = divmod(s, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"


if __name__ == "__main__":
    main()
