"""Miniatura 1280x720 de la Dosis de Asombro #7."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R))
from marco import F_BLACK  # noqa: E402

F = R / "shock07" / "fotos"
W, H = 1280, 720


def foto(nombre, w, h):
    im = Image.open(F / nombre).convert("RGB")
    return ImageOps.fit(im, (w, h), Image.LANCZOS, centering=(0.5, 0.45))


lienzo = Image.new("RGB", (W, H))
lienzo.paste(foto("tiburon_okeanos.jpg", W // 2, H), (0, 0))
lienzo.paste(foto("medusa_inmortal.jpg", W // 2, H), (W // 2, 0))

# oscurecer la parte de abajo para el texto
sombra = Image.new("L", (W, H), 0)
ds = ImageDraw.Draw(sombra)
for y in range(H):
    ds.line([(0, y), (W, y)], fill=int(max(0, (y - H * 0.35) / (H * 0.65)) * 215))
lienzo = Image.composite(Image.new("RGB", (W, H)), lienzo, sombra)
d = ImageDraw.Draw(lienzo)
d.line([(W // 2, 0), (W // 2, H)], fill=(255, 255, 255), width=6)


def texto(t, y, tam, color, borde=10):
    f = ImageFont.truetype(str(F_BLACK), tam)
    w = d.textlength(t, font=f)
    d.text(((W - w) / 2, y), t, font=f, fill=color, stroke_width=borde, stroke_fill=(0, 0, 0))


texto("CÉLULAS DE 80 AÑOS", 400, 78, (255, 255, 255))
texto("¡VUELVEN A 20!", 495, 150, (255, 214, 0), 14)

# etiqueta superior
f = ImageFont.truetype(str(F_BLACK), 44)
t = "🧠⚡ +10 COSAS QUE DESAFÍAN AL TIEMPO"
t = "+10 COSAS QUE DESAFÍAN AL TIEMPO"
w = d.textlength(t, font=f)
x0, y0 = (W - w) / 2 - 24, 28
d.rounded_rectangle([x0, y0, x0 + w + 48, y0 + 70], 18, fill=(225, 30, 45))
d.text((x0 + 24, y0 + 8), t, font=f, fill=(255, 255, 255))

out = R / "shock07" / "salida" / "miniatura.jpg"
lienzo.save(out, quality=92)
print(out, out.stat().st_size // 1024, "KB")
