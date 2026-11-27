# Neido Studio · Etapa "labios" sola en Colab (GPU T4): LatentSync 1.5 sobre los planos ya animados.
# Baja de GitHub los vídeos (video-colab/) y las voces (audio/) de los planos "lipsync". Salida: /content/entrega
import json, os, subprocess, sys, time, traceback, urllib.request
os.environ["MPLBACKEND"] = "Agg"          # Colab pone un backend de matplotlib que LatentSync no entiende
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
T0 = time.time(); OUT = "/content/entrega"; IN = "/content/entrada"
os.makedirs(OUT, exist_ok=True); os.makedirs(IN, exist_ok=True)
RAW = "https://raw.githubusercontent.com/neidostore/Canal-youtube/ccr-00644e8b-14b4ji/peliculas-ia/producciones/prueba-tecnica/"
PLANOS = __PLANOS__
log = lambda *a: print(f"[{(time.time()-T0)/60:5.1f} min]", *a, flush=True)
def sh(c, salida="/content/log_comandos.txt"):
    subprocess.run(f"{c} > {salida} 2>&1", shell=True, check=True, env={**os.environ, "MPLBACKEND": "Agg"})
for n in PLANOS:
    urllib.request.urlretrieve(f"{RAW}video-colab/plano_{n:02d}.mp4", f"{IN}/plano_{n:02d}.mp4")
    urllib.request.urlretrieve(f"{RAW}audio/plano_{n:02d}_1.wav", f"{IN}/plano_{n:02d}_1.wav")
LS = "/content/LatentSync"
try:
    log("instalando LatentSync 1.5 (unos 10 min)")
    if not os.path.exists(LS):
        sh(f"git clone -q https://github.com/bytedance/LatentSync.git {LS}")
    sh(f"{sys.executable} -m pip install -q uv")
    sh(f"cd {LS} && uv venv -q -p 3.10 /content/lsenv && uv pip install -q -p /content/lsenv/bin/python "
       f"--index-strategy unsafe-best-match -r requirements.txt")
    sh(f"cd {LS} && /content/lsenv/bin/python -c \"from huggingface_hub import hf_hub_download as d; "
       f"[d('ByteDance/LatentSync-1.5', f, local_dir='checkpoints') for f in ('latentsync_unet.pt', 'whisper/tiny.pt')]\"")
except Exception:
    traceback.print_exc(); os.system(f"cp /content/log_comandos.txt {OUT}/log_instalacion.txt")
for n in PLANOS:
    ti = time.time()
    try:
        sh(f"cd {LS} && /content/lsenv/bin/python -m scripts.inference --unet_config_path configs/unet/stage2.yaml "
           f"--inference_ckpt_path checkpoints/latentsync_unet.pt --inference_steps 20 --guidance_scale 1.5 "
           f"--video_path {IN}/plano_{n:02d}.mp4 --audio_path {IN}/plano_{n:02d}_1.wav "
           f"--video_out_path {OUT}/plano_{n:02d}_labios.mp4", salida=f"{OUT}/log_labios_{n:02d}.txt")
        log(f"labios plano {n} listo · {time.time()-ti:.0f} s")
    except Exception:
        log(f"labios plano {n} ha fallado (ver log_labios_{n:02d}.txt)")
log("FIN")
