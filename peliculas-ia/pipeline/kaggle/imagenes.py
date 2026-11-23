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

pipe = StableDiffusionXLPipeline.from_pretrained(MODELO, torch_dtype=torch.float16, variant=None).to("cuda")
pipe.enable_vae_slicing()
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
    img.save(f"{OUT}/ref_{nombre}.png"); refs[nombre] = img
    print(f"referencia {nombre} · {time.time()-t0:.0f} s", flush=True)

# 2) planos (con IP-Adapter de cara cuando hay personaje)
pipe.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models", weight_name="ip-adapter-plus-face_sdxl_vit-h.safetensors",
                     image_encoder_folder="models/image_encoder")
pipe.set_ip_adapter_scale(0.6)
for pl in PLANOS["planos"]:
    texto = pl["prompt"]
    for nombre, p in personajes.items():
        texto = texto.replace("{" + nombre + "}", p.get("descripcion", nombre))
    prompt = f"{texto}. {estilo}"
    caras = [refs[c] for c in pl.get("personajes", []) if c in refs]
    if caras:
        img = generar(prompt, ip_imagen=caras[0], semilla=SEMILLA + pl["n"])
    else:
        pipe.set_ip_adapter_scale(0.0)
        img = generar(prompt, ip_imagen=Image.new("RGB", (224, 224)), semilla=SEMILLA + pl["n"])
        pipe.set_ip_adapter_scale(0.6)
    img.save(f"{OUT}/plano_{pl['n']:02d}.png")
    print(f"plano {pl['n']} · {time.time()-t0:.0f} s", flush=True)

json.dump({"segundos_totales": round(time.time()-t0), "modelo": MODELO}, open(f"{OUT}/../metricas_imagenes.json", "w"))
print("FIN imagenes", round(time.time()-t0), "s")
