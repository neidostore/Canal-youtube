# Neido Studio · Etapa "imagenes" (se ejecuta en Kaggle con GPU T4).
# 1) Genera una imagen de referencia de cada personaje (retrato de frente).
# 2) Genera el fotograma clave de cada plano; si sale un personaje, usa IP-Adapter (cara) con su referencia
#    para mantener el mismo rostro entre planos.
# Salida: /kaggle/working/entrega/plano_NN.png y ref_<personaje>.png
#
# ⚠️ BORRADOR SIN PROBAR: se valida en la prueba técnica. Modelos y licencias a confirmar:
#   - Modelo base: SDXL fotorrealista (por defecto RealVisXL V5.0, derivado de SDXL; licencia a verificar)
#   - IP-Adapter Plus Face SDXL (h94/IP-Adapter, Apache 2.0)
import json, os, subprocess, sys, time
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "diffusers>=0.32", "transformers", "accelerate"], check=True)
import torch
from diffusers import StableDiffusionXLPipeline
from PIL import Image

PLANOS = json.loads(__PLANOS_JSON__)
MODELO = os.environ.get("NEIDO_MODELO_IMAGEN", "SG161222/RealVisXL_V5.0")
OUT = "/kaggle/working/entrega"; os.makedirs(OUT, exist_ok=True)
W, H = 1344, 768                      # ~16:9, resolución nativa de SDXL
PASOS, GUIA, SEMILLA = 30, 5.0, 404
t0 = time.time()

try:
    pipe = StableDiffusionXLPipeline.from_pretrained(MODELO, dtype=torch.float16).to("cuda")
except TypeError:
    pipe = StableDiffusionXLPipeline.from_pretrained(MODELO, torch_dtype=torch.float16).to("cuda")
# ahorro de memoria en la decodificación (el nombre de la función cambia según la versión de diffusers)
for f in (getattr(pipe, "enable_vae_slicing", None), getattr(pipe.vae, "enable_slicing", None)):
    if f:
        f(); break
estilo, negativo = PLANOS["estilo"], PLANOS["negativo"]
personajes = PLANOS["personajes"]


def generar(prompt, ip_imagen=None, semilla=SEMILLA, w=W, h=H):
    g = torch.Generator("cuda").manual_seed(semilla)
    extra = {"ip_adapter_image": ip_imagen} if ip_imagen is not None else {}
    return pipe(prompt=prompt, negative_prompt=negativo, width=w, height=h, num_inference_steps=PASOS,
                guidance_scale=GUIA, generator=g, **extra).images[0]


# 1) referencias de personaje (sin IP-Adapter)
refs = {}
for nombre, p in personajes.items():
    if "descripcion" not in p:
        continue
    img = generar(f"Close-up portrait, front view, of {p['descripcion']}, neutral expression, soft even studio light, "
                  f"plain grey background. {estilo}", w=1024, h=1024)
    img.save(f"{OUT}/ref_{nombre}.png")
    # solo la cara (recorte central) para que IP-Adapter copie el rostro y no el fondo gris de estudio
    refs[nombre] = img.crop((256, 128, 768, 640))
    print(f"referencia {nombre} · {time.time()-t0:.0f} s", flush=True)

# 2) planos SIN IP-Adapter: así el modelo respeta el escenario, la noche y el encuadre del prompt
#    (prueba del 25/11: con IP-Adapter en toda la imagen salían retratos de frente, de día y sin barco)
escenas = {}
for pl in PLANOS["planos"]:
    texto = pl["prompt"]
    for nombre, p in personajes.items():
        texto = texto.replace("{" + nombre + "}", p.get("descripcion", nombre))
    img = generar(f"{texto}. {estilo}", semilla=SEMILLA + pl["n"])
    escenas[pl["n"]] = img
    img.save(f"{OUT}/plano_{pl['n']:02d}.png")
    print(f"plano {pl['n']} · {time.time()-t0:.0f} s", flush=True)

# 3) cara: se localiza el rostro y se repinta SOLO esa zona con IP-Adapter y la referencia del personaje
import cv2, numpy as np
from PIL import ImageDraw, ImageFilter
from diffusers import StableDiffusionXLInpaintPipeline
detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
inpaint = StableDiffusionXLInpaintPipeline(**pipe.components)
inpaint.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models", weight_name="ip-adapter-plus-face_sdxl_vit-h.safetensors",
                        image_encoder_folder="models/image_encoder")
inpaint.set_ip_adapter_scale(0.7)
for pl in PLANOS["planos"]:
    caras = [c for c in pl.get("personajes", []) if c in refs]
    if not caras:
        continue
    img = escenas[pl["n"]]
    gris = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    encontradas = detector.detectMultiScale(gris, scaleFactor=1.1, minNeighbors=5, minSize=(48, 48))
    if len(encontradas) == 0:
        print(f"plano {pl['n']}: no se ve la cara de frente, se deja sin retocar", flush=True)
        continue
    x, y, w, h = max(encontradas, key=lambda r: r[2] * r[3])
    cx, cy, lado = x + w // 2, y + h // 2, int(max(w, h) * 2.2)
    x0, y0 = max(0, cx - lado // 2), max(0, cy - lado // 2)
    x1, y1 = min(img.width, x0 + lado), min(img.height, y0 + lado)
    recorte = img.crop((x0, y0, x1, y1)).resize((1024, 1024), Image.LANCZOS)
    mascara = Image.new("L", (1024, 1024), 0)
    k = 1024 / (x1 - x0)
    fx0, fy0 = (x - x0) * k, (y - y0) * k
    ImageDraw.Draw(mascara).ellipse((fx0 - 0.1 * w * k, fy0 - 0.25 * h * k, fx0 + 1.1 * w * k, fy0 + 1.15 * h * k), fill=255)
    mascara = mascara.filter(ImageFilter.GaussianBlur(24))
    g = torch.Generator("cuda").manual_seed(SEMILLA + pl["n"])
    cara = inpaint(prompt=f"close-up of the face of {personajes[caras[0]]['descripcion']}, {estilo}", negative_prompt=negativo,
                   image=recorte, mask_image=mascara, ip_adapter_image=refs[caras[0]], strength=0.75,
                   num_inference_steps=PASOS, guidance_scale=GUIA, generator=g).images[0]
    cara = cara.resize((x1 - x0, y1 - y0), Image.LANCZOS)
    m = mascara.resize((x1 - x0, y1 - y0), Image.LANCZOS)
    final = img.copy(); final.paste(cara, (x0, y0), m)
    img.save(f"{OUT}/plano_{pl['n']:02d}_sin_cara.png")
    final.save(f"{OUT}/plano_{pl['n']:02d}.png")
    print(f"plano {pl['n']} · cara retocada · {time.time()-t0:.0f} s", flush=True)

json.dump({"segundos_totales": round(time.time()-t0), "modelo": MODELO}, open(f"{OUT}/../metricas_imagenes.json", "w"))
print("FIN imagenes", round(time.time()-t0), "s")
