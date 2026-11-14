"""Plantilla visual "marco": barras fijas, cuenta atrás, transición con logo, fondos animados y recuadros con flecha.

Se activa con la clave "marco" en escenas.json. Todo se genera aquí (PIL/numpy) y se guarda en trabajo/marco/.
"""
import math, random, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BARRA = 84                      # alto de cada barra (arriba y abajo)
W, HC = 1920, 1080 - 2 * BARRA  # zona central donde va el vídeo: 1920x912
COLORES = ["#1E8CFF", "#FF7A1A", "#8B3DFF", "#18B46B", "#FF3D7F", "#FFB800"]
F_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
F_BOLD = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"


def _rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _mix(c, k):   # aclara (k>0) u oscurece (k<0)
    t = 255 if k > 0 else 0; k = abs(k)
    return tuple(int(v + (t - v) * k) for v in c)


def logo_redondo(ruta, lado):
    im = Image.open(ruta).convert("RGB")
    s = min(im.size); im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width + s) // 2, (im.height + s) // 2))
    r = int(s * 0.425); c = s // 2                      # el logo es un círculo dentro del cuadrado
    im = im.crop((c - r, c - r, c + r, c + r)).resize((lado * 2, lado * 2), Image.LANCZOS)
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).ellipse((2, 2, im.width - 3, im.height - 3), fill=255)
    im.putalpha(m)
    return im.resize((lado, lado), Image.LANCZOS)


def marco_png(destino, cfg, raiz, render_html):
    """Barras de arriba y abajo + caja de la cuenta atrás + logo fijo. El centro queda transparente."""
    logo = destino.parent / "logo_fijo.png"
    logo_redondo(raiz / cfg["logo"], 300).save(logo)
    html = f"""<!doctype html><meta charset=utf-8><style>
*{{margin:0;box-sizing:border-box}}body{{width:1920px;height:1080px;background:transparent;font-family:'Inter Display';overflow:hidden}}
.b{{position:absolute;left:0;width:1920px;height:{BARRA}px;display:flex;align-items:center;justify-content:center;
 background:linear-gradient(90deg,#0B5FD9,#1E8CFF 30%,#FF7A1A 70%,#E0560A);color:#fff;font-weight:900;letter-spacing:.04em;
 text-shadow:0 3px 0 rgba(0,0,0,.45)}}
.t{{top:0;font-size:54px;border-bottom:6px solid #FFC400}}.t i{{color:#FFE14D;font-style:normal}}
.a{{bottom:0;font-size:42px;border-top:6px solid #FFC400;letter-spacing:.02em}}
.c{{position:absolute;right:28px;top:{BARRA + 18}px;width:190px;height:78px;border-radius:14px;background:#FFC400;
 border:5px solid #fff;box-shadow:0 6px 0 rgba(0,0,0,.35)}}
.l{{position:absolute;right:22px;bottom:{BARRA - 46}px;width:150px;height:150px;border-radius:50%;border:5px solid #fff;
 box-shadow:0 6px 14px rgba(0,0,0,.5)}}
</style><div class="b t">{cfg['titulo']}</div><div class="b a">{cfg['lema']}</div><div class=c></div>
<img class=l src="{logo.name}">"""
    f = destino.parent / "marco.html"; f.write_text(html, encoding="utf-8")
    render_html(f, destino, 1920, 1080)


def fondo_animado(destino, color, n=90, fps=30):
    """Bucle de 3 s: rayos de color girando + confeti flotando (para rellenar cuando la imagen no ocupa todo)."""
    if destino.exists():
        return
    w, h = W // 2, HC // 2
    c = _rgb(color); c1, c2 = _mix(c, -0.18), _mix(c, 0.16)
    yy, xx = np.mgrid[0:h, 0:w]; ang = np.arctan2(yy - h * 0.5, xx - w * 0.5); dist = np.hypot(yy - h * 0.5, xx - w * 0.5)
    rayos = 16; rnd = random.Random(color)
    conf = [(rnd.random() * w, rnd.random() * h, rnd.choice([1, 2]), rnd.uniform(5, 11), rnd.random() * 6.28,
             rnd.choice(["#FFFFFF", "#FFE14D", "#FF5DA2", "#6EE7FF", "#B5FF6E"]), rnd.choice([0, 1])) for _ in range(46)]
    tmp = destino.parent / f"_f_{destino.stem}"; tmp.mkdir(exist_ok=True)
    for i in range(n):
        ph = 2 * math.pi / rayos * i / n
        m = ((np.floor((ang + ph) / (math.pi / rayos)) % 2) == 0)
        vin = np.clip(1.08 - dist / (w * 0.9), 0.55, 1.0)[..., None]
        img = np.where(m[..., None], np.array(c2), np.array(c1)) * vin
        im = Image.fromarray(img.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
        d = ImageDraw.Draw(im)
        for (x, y, vueltas, t, rot, col, forma) in conf:
            py = (y - h * vueltas * i / n) % h; px = x + 9 * math.sin(2 * math.pi * i / n + rot)
            a = rot + 2 * math.pi * i / n
            if forma:
                d.ellipse((px - t / 2, py - t / 2, px + t / 2, py + t / 2), fill=col)
            else:
                dx, dy = math.cos(a) * t, math.sin(a) * t * 0.5
                d.polygon([(px - dx, py - dy), (px - dy, py + dx * .5), (px + dx, py + dy), (px + dy, py - dx * .5)], fill=col)
        im.save(tmp / f"{i:03d}.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", str(tmp / "%03d.png"),
                    "-vf", f"scale={W}:{HC}:flags=bicubic,format=yuv420p", "-c:v", "libx264", "-crf", "18", str(destino)], check=True)
    for f in tmp.iterdir():
        f.unlink()
    tmp.rmdir()


N_TRANS, MEDIO = 17, 8   # fotogramas de la transición y fotograma en el que tapa toda la imagen (ahí va el corte)


def transicion(carpeta, color, color2, logo_ruta):
    """Secuencia PNG con alfa (≈0,55 s): explosión de color que tapa la imagen, logo en el centro y se abre."""
    carpeta.mkdir(parents=True, exist_ok=True)
    if (carpeta / f"{N_TRANS - 1:02d}.png").exists():
        return
    logo = logo_redondo(logo_ruta, 520); cx, cy = W // 2, HC // 2; rmax = int(math.hypot(cx, cy)) + 30
    ease = lambda x: 1 - (1 - min(1, max(0, x))) ** 3
    for i in range(N_TRANS):
        im = Image.new("RGBA", (W, HC), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        if i <= MEDIO:      # se cierra: círculos que crecen desde el centro
            for k, col in enumerate([color2, "#FFFFFF", color]):
                r = rmax * ease((i + 1 - k * 0.9) / (MEDIO - 1.2))
                if r > 0:
                    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)
        else:               # se abre: un agujero que crece desde el centro
            im = Image.new("RGBA", (W, HC), _rgb(color) + (255,))
            r = rmax * ease((i - MEDIO) / (N_TRANS - 1 - MEDIO)) ** 1.3
            m = Image.new("L", (W, HC), 255); ImageDraw.Draw(m).ellipse((cx - r, cy - r, cx + r, cy + r), fill=0)
            ring = Image.new("RGBA", (W, HC), (255, 255, 255, 255))
            m2 = Image.new("L", (W, HC), 0); ImageDraw.Draw(m2).ellipse((cx - r - 26, cy - r - 26, cx + r + 26, cy + r + 26), fill=255)
            im = Image.composite(ring, im, m2); im.putalpha(m)
        esc = {3: .35, 4: .7, 5: 1.0, 6: 1.14, 7: 1.05, 8: 1.0, 9: 1.0, 10: .9, 11: .6}.get(i)
        if esc:
            l = logo.resize((int(520 * esc), int(520 * esc)), Image.LANCZOS)
            base = Image.new("RGBA", (W, HC), (0, 0, 0, 0)); base.paste(l, (cx - l.width // 2, cy - l.height // 2), l)
            if i > MEDIO:
                a = base.getchannel("A"); a = Image.eval(a, lambda v, f=(12 - i) / 4: int(v * max(0, min(1, f)))); base.putalpha(a)
            im = Image.alpha_composite(im, base)
        im.save(carpeta / f"{i:02d}.png")


def recuadro(destino, foto, cfg):
    """PNG transparente 1920x912 con un recuadro (detalle ampliado u otra imagen) y una flecha que señala un punto."""
    im = Image.open(foto).convert("RGB")
    if cfg.get("zona"):
        x, y, w, h = cfg["zona"]; im = im.crop((int(x * im.width), int(y * im.height), int((x + w) * im.width), int((y + h) * im.height)))
    ancho = cfg.get("ancho", 430); im = im.resize((ancho, round(im.height * ancho / im.width)), Image.LANCZOS)
    lienzo = Image.new("RGBA", (W, HC), (0, 0, 0, 0))
    px, py = cfg.get("pos", [0.82, 0.3]); cx, cy = int(px * W), int(py * HC)
    x0, y0 = cx - im.width // 2, cy - im.height // 2; b = 10
    sombra = Image.new("RGBA", (W, HC), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle((x0 - b + 8, y0 - b + 12, x0 + im.width + b + 8, y0 + im.height + b + 12), 18, fill=(0, 0, 0, 150))
    lienzo = Image.alpha_composite(lienzo, sombra.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(lienzo)
    d.rounded_rectangle((x0 - b, y0 - b, x0 + im.width + b, y0 + im.height + b), 18, fill="#FFC400", outline="#FFFFFF", width=4)
    lienzo.paste(im, (x0, y0))
    if cfg.get("titulo"):
        f = ImageFont.truetype(F_BLACK, 34); tw = d.textlength(cfg["titulo"], font=f)
        d.rounded_rectangle((cx - tw / 2 - 18, y0 + im.height + b - 6, cx + tw / 2 + 18, y0 + im.height + b + 46), 12, fill="#1E8CFF", outline="#FFFFFF", width=3)
        d.text((cx - tw / 2, y0 + im.height + b), cfg["titulo"], font=f, fill="#FFFFFF")
    if cfg.get("apunta"):
        tx, ty = int(cfg["apunta"][0] * W), int(cfg["apunta"][1] * HC)
        sx = x0 - b if tx < cx else x0 + im.width + b; sy = min(max(ty, y0), y0 + im.height)
        if abs(ty - cy) > abs(tx - cx):
            sx = cx; sy = y0 + im.height + b if ty > cy else y0 - b
        a = math.atan2(ty - sy, tx - sx); L = 46
        ex, ey = tx - math.cos(a) * L * 0.8, ty - math.sin(a) * L * 0.8
        for ancho_l, col in ((26, "#000000"), (16, "#FFC400")):
            d.line((sx, sy, ex, ey), fill=col, width=ancho_l)
            k = 1.0 if col == "#FFC400" else 1.25
            p = [(tx + math.cos(a) * (6 if k > 1 else 0), ty + math.sin(a) * (6 if k > 1 else 0)),
                 (ex + math.cos(a + 2.2) * L * k * .75, ey + math.sin(a + 2.2) * L * k * .75),
                 (ex + math.cos(a - 2.2) * L * k * .75, ey + math.sin(a - 2.2) * L * k * .75)]
            d.polygon(p, fill=col)
    lienzo.save(destino)


def marca_vertical(destino, logo_ruta, nombre="SHOCK MENTAL"):
    """Shorts: PNG 1080x1920 transparente con el logo y el nombre del canal arriba (fuera de los botones de YouTube)."""
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(F_BLACK, 54); tw = int(d.textlength(nombre, font=f)); L = 132
    ancho = L + 26 + tw + 44; x0 = (1080 - ancho) // 2; y0 = 150
    pill = Image.new("RGBA", (ancho, 104), (0, 0, 0, 0)); g = Image.new("RGBA", (ancho, 104))
    for x in range(ancho):
        k = x / ancho; c = tuple(int(a + (b - a) * k) for a, b in zip((30, 140, 255), (255, 122, 26)))
        ImageDraw.Draw(g).line((x, 0, x, 104), fill=c + (255,))
    m = Image.new("L", (ancho, 104), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, ancho - 1, 103), 52, fill=255)
    pill.paste(g, (0, 0), m); ImageDraw.Draw(pill).rounded_rectangle((0, 0, ancho - 1, 103), 52, outline="#FFFFFF", width=5)
    im.alpha_composite(pill, (x0, y0 + 14))
    d.text((x0 + L + 20 + 3, y0 + 14 + 20 + 3), nombre, font=f, fill=(0, 0, 0, 150)); d.text((x0 + L + 20, y0 + 14 + 20), nombre, font=f, fill="#FFFFFF")
    logo = logo_redondo(logo_ruta, L); aro = Image.new("RGBA", (L + 12, L + 12), (0, 0, 0, 0))
    ImageDraw.Draw(aro).ellipse((0, 0, L + 11, L + 11), fill="#FFFFFF"); aro.alpha_composite(logo, (6, 6))
    im.alpha_composite(aro, (x0 - 6, y0 - 6)); im.save(destino)


def cierre_vertical(destino, logo_ruta, texto="Suscríbete"):
    """Shorts: logo grande y botón rojo para la última frase."""
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    L = 520; logo = logo_redondo(logo_ruta, L); aro = Image.new("RGBA", (L + 24, L + 24), (0, 0, 0, 0))
    ImageDraw.Draw(aro).ellipse((0, 0, L + 23, L + 23), fill="#FFFFFF"); aro.alpha_composite(logo, (12, 12))
    sombra = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); ImageDraw.Draw(sombra).ellipse((270 - 20, 400, 810 + 20, 960 + 40), fill=(0, 0, 0, 170))
    im = Image.alpha_composite(im, sombra.filter(ImageFilter.GaussianBlur(30))); im.alpha_composite(aro, ((1080 - L - 24) // 2, 420))
    d = ImageDraw.Draw(im); f = ImageFont.truetype(F_BLACK, 64); tw = d.textlength(texto, font=f)
    d.rounded_rectangle((540 - tw / 2 - 50, 1010, 540 + tw / 2 + 50, 1124), 57, fill="#E62117", outline="#FFFFFF", width=5)
    d.text((540 - tw / 2, 1028), texto, font=f, fill="#FFFFFF"); im.save(destino)


F_EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"


def _emoji(txt, tam):
    f = ImageFont.truetype(F_EMOJI, 109)
    im = Image.new("RGBA", (140 * max(1, len(txt)), 140), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, 0), txt, font=f, embedded_color=True)
    im = im.crop(im.getbbox()); k = tam / im.height
    return im.resize((max(1, round(im.width * k)), tam), Image.LANCZOS)


def marca(destino, m, a_px):
    """Una anotación (contorno, círculo, flecha, etiqueta o emoji) en un PNG transparente 1920x912.
    a_px convierte coordenadas relativas (0-1) en píxeles de la pantalla."""
    im = Image.new("RGBA", (W, HC), (0, 0, 0, 0)); d = ImageDraw.Draw(im); t = m["tipo"]
    col = m.get("color", "#FFC400")
    if t == "contorno":
        pts = [a_px(*p) for p in m["puntos"]]; pts.append(pts[0])
        d.line(pts, fill="#000000", width=18, joint="curve"); d.line(pts, fill=col, width=10, joint="curve")
    elif t == "circulo":
        cx, cy = a_px(*m["c"]); ex, ey = a_px(m["c"][0] + m["r"][0], m["c"][1] + m["r"][1]); rx, ry = abs(ex - cx), abs(ey - cy)
        d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), outline="#000000", width=18)
        d.ellipse((cx - rx + 4, cy - ry + 4, cx + rx - 4, cy + ry - 4), outline=col, width=10)
    elif t == "flecha":
        (sx, sy), (tx, ty) = a_px(*m["de"]), a_px(*m["a"]); a = math.atan2(ty - sy, tx - sx); L = 50
        ex, ey = tx - math.cos(a) * L * 0.8, ty - math.sin(a) * L * 0.8
        for ancho_l, c, k in ((28, "#000000", 1.25), (16, col, 1.0)):
            d.line((sx, sy, ex, ey), fill=c, width=ancho_l)
            o = 7 if k > 1 else 0
            d.polygon([(tx + math.cos(a) * o, ty + math.sin(a) * o),
                       (ex + math.cos(a + 2.2) * L * k * .75, ey + math.sin(a + 2.2) * L * k * .75),
                       (ex + math.cos(a - 2.2) * L * k * .75, ey + math.sin(a - 2.2) * L * k * .75)], fill=c)
    elif t == "texto":
        f = ImageFont.truetype(F_BLACK, m.get("tam", 46)); x, y = a_px(*m["pos"]); tw = d.textlength(m["texto"], font=f); h = m.get("tam", 46)
        fondo = m.get("fondo", "#1E8CFF")
        d.rounded_rectangle((x - tw / 2 - 22, y - h / 2 - 14, x + tw / 2 + 22, y + h / 2 + 18), 16, fill=fondo, outline="#FFFFFF", width=4)
        d.text((x - tw / 2, y - h / 2 - 4), m["texto"], font=f, fill=m.get("tinta", "#FFFFFF"))
    elif t == "emoji":
        e = _emoji(m["emoji"], m.get("tam", 190)); x, y = a_px(*m["pos"])
        s = Image.new("RGBA", (W, HC), (0, 0, 0, 0)); s.paste((0, 0, 0, 150), (x - e.width // 2 + 6, y - e.height // 2 + 10), e)
        im = Image.alpha_composite(im, s.filter(ImageFilter.GaussianBlur(8))); im.alpha_composite(e, (x - e.width // 2, y - e.height // 2))
    im.save(destino)
