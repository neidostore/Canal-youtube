# Neido Studio · Etapa "video" (Kaggle, GPU T4).
# Anima el fotograma clave de cada plano de tipo "video" o "lipsync" con Wan 2.2 TI2V-5B (Apache 2.0).
# Entrada: la salida de la etapa "imagenes" (kernel_sources). Salida: /kaggle/working/entrega/plano_NN.mp4
#
# ⚠️ BORRADOR SIN PROBAR. La T4 tiene 16 GB y el modelo pide oficialmente 24 GB a 720p:
#   se usa descarga a CPU y resolución reducida (480p). Tiempos por clip: a medir en la prueba técnica.
import glob, json, os, subprocess, sys, time
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "diffusers>=0.35", "transformers", "accelerate", "ftfy", "imageio[ffmpeg]"], check=True)
import torch
from diffusers import WanImageToVideoPipeline, AutoencoderKLWan
from diffusers.utils import export_to_video
from PIL import Image

PLANOS = json.loads(__PLANOS_JSON__)
OUT = "/kaggle/working/entrega"; os.makedirs(OUT, exist_ok=True)
MODELO = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
W, H, FPS = 832, 480, 24
NEG = "static, blurry, distorted face, deformed hands, extra limbs, flicker, text, watermark"
t0 = time.time()

# localizar los fotogramas de la etapa anterior
entrada = {os.path.basename(f): f for f in glob.glob("/kaggle/input/**/entrega/plano_*.png", recursive=True)}
vae = AutoencoderKLWan.from_pretrained(MODELO, subfolder="vae", torch_dtype=torch.float32)
pipe = WanImageToVideoPipeline.from_pretrained(MODELO, vae=vae, torch_dtype=torch.float16)
pipe.enable_model_cpu_offload()
tiempos = {}
for pl in PLANOS["planos"]:
    if pl["tipo"] not in ("video", "lipsync"):
        continue
    nombre = f"plano_{pl['n']:02d}.png"
    if nombre not in entrada:
        print("falta", nombre); continue
    img = Image.open(entrada[nombre]).convert("RGB").resize((W, H))
    frames = int(min(pl["duracion"], 5) * FPS) // 4 * 4 + 1          # Wan necesita 4k+1 fotogramas
    prompt = f"{pl.get('movimiento_video', 'subtle natural movement')}. {pl['prompt']}"
    for nom, p in PLANOS["personajes"].items():
        prompt = prompt.replace("{" + nom + "}", p.get("descripcion", nom))
    ti = time.time()
    video = pipe(image=img, prompt=prompt, negative_prompt=NEG, height=H, width=W, num_frames=frames,
                 num_inference_steps=30, guidance_scale=5.0, generator=torch.Generator("cuda").manual_seed(404)).frames[0]
    export_to_video(video, f"{OUT}/plano_{pl['n']:02d}.mp4", fps=FPS)
    tiempos[pl["n"]] = round(time.time() - ti)
    print(f"plano {pl['n']} · {tiempos[pl['n']]} s", flush=True)

json.dump({"segundos_totales": round(time.time()-t0), "por_plano": tiempos}, open("/kaggle/working/metricas_video.json", "w"))
print("FIN video", round(time.time()-t0), "s")
