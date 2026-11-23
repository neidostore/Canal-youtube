# Neido Studio · Etapa "labios" (Kaggle, GPU T4).
# Sincroniza los labios de los planos de tipo "lipsync" con su voz, usando LatentSync 1.5 (ByteDance).
# Entradas: salidas de "video" (plano_NN.mp4) y "voces" (plano_NN_1.wav). Salida: /kaggle/working/entrega/plano_NN.mp4
#
# ⚠️ BORRADOR SIN PROBAR. Licencia de los pesos (OpenRAIL++) a revisar antes de monetizar.
#   Se usa la versión 1.5 porque la 1.6 (512 px) pide más memoria de la que tiene una T4.
import glob, json, os, subprocess, sys, time

PLANOS = json.loads(__PLANOS_JSON__)
OUT = "/kaggle/working/entrega"; os.makedirs(OUT, exist_ok=True)
t0 = time.time()
sh = lambda c: subprocess.run(c, shell=True, check=True)

sh("git clone -q https://github.com/bytedance/LatentSync.git /kaggle/working/LatentSync")
os.chdir("/kaggle/working/LatentSync")
sh(f"{sys.executable} -m pip install -q -r requirements.txt")
sh("huggingface-cli download ByteDance/LatentSync-1.5 --local-dir checkpoints --exclude '*.git*' 'README.md'")

videos = {os.path.basename(f): f for f in glob.glob("/kaggle/input/**/entrega/plano_*.mp4", recursive=True)}
audios = {os.path.basename(f): f for f in glob.glob("/kaggle/input/**/entrega/plano_*_1.wav", recursive=True)}
for pl in PLANOS["planos"]:
    if pl["tipo"] != "lipsync":
        continue
    v, a = f"plano_{pl['n']:02d}.mp4", f"plano_{pl['n']:02d}_1.wav"
    if v not in videos or a not in audios:
        print("faltan entradas para el plano", pl["n"]); continue
    ti = time.time()
    sh(f"{sys.executable} -m scripts.inference --unet_config_path configs/unet/stage2.yaml "
       f"--inference_ckpt_path checkpoints/latentsync_unet.pt --inference_steps 20 --guidance_scale 1.5 "
       f"--video_path {videos[v]} --audio_path {audios[a]} --video_out_path {OUT}/{v}")
    print(f"plano {pl['n']} · {time.time()-ti:.0f} s", flush=True)

print("FIN labios", round(time.time()-t0), "s")
