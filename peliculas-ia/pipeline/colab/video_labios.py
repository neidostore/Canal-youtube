# Neido Studio · Etapas "voces" + "video" + "labios" en Google Colab (GPU T4 gratuita).
# 0) Voces con Chatterbox Multilingual (MIT) a partir de voces semilla de Kokoro (Apache 2.0), en un entorno
#    aparte (uv, Python 3.11) porque Chatterbox fija versiones antiguas de torch y diffusers.
# 1) Wan 2.2 TI2V-5B (Apache 2.0) anima el fotograma clave de cada plano "video" / "lipsync".
#    Para que quepa en la T4 (16 GB de vídeo, 12 GB de RAM): primero se calculan los textos con el
#    codificador T5 y se libera; luego se carga solo el modelo de vídeo en fp16.
# 2) LatentSync 1.5 (ByteDance, pesos OpenRAIL++) sincroniza los labios de los planos "lipsync" con su voz.
#    Va en un entorno aparte (uv, Python 3.10) porque fija sus propias versiones de librerías.
# Los fotogramas y las voces vienen incrustados en el cuaderno (__DATOS__). Salida: /content/entrega
import base64, gc, json, os, subprocess, sys, time, traceback
T0 = time.time(); LIMITE = 2.6 * 3600          # Colab gratis corta sesiones largas: paramos a tiempo
OUT = "/content/entrega"; IN = "/content/entrada"; os.makedirs(OUT, exist_ok=True); os.makedirs(IN, exist_ok=True)
DATOS = json.loads(base64.b64decode(__DATOS__))
PLANOS = DATOS["planos"]
for nombre, b64 in DATOS["archivos"].items():
    open(f"{IN}/{nombre}", "wb").write(base64.b64decode(b64))
log = lambda *a: print(f"[{(time.time()-T0)/60:5.1f} min]", *a, flush=True)
sh = lambda c: subprocess.run(c, shell=True, check=True)

# ---------------- 0) voces ----------------
VOCES = f"{OUT}/audio"; os.makedirs(VOCES, exist_ok=True)
SCRIPT_VOCES = r"""
import json, os, sys, time, torch, torchaudio, soundfile as sf
PLANOS = json.load(open(sys.argv[1])); OUT = sys.argv[2]; REFS = OUT + "/refs"; os.makedirs(REFS, exist_ok=True)
from kokoro import KPipeline
kp = KPipeline(lang_code="e", repo_id="hexgrad/Kokoro-82M")
SEMILLAS = {"narrador": "em_alex", "santi": "em_santa", "margaret": "ef_dora"}
frase = "Buenas noches. Esta es una muestra de voz para la película, leída con calma y claridad, sin prisa."
for quien, voz in SEMILLAS.items():
    audio = [a for _, _, a in kp(frase, voice=voz)]
    sf.write(f"{REFS}/{quien}.wav", torch.cat([torch.as_tensor(a) for a in audio]).numpy(), 24000)
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
tts = ChatterboxMultilingualTTS.from_pretrained(device="cuda")
AJ = {"narrador": dict(exaggeration=0.35, cfg_weight=0.5), "santi": dict(exaggeration=0.65, cfg_weight=0.4),
      "margaret": dict(exaggeration=0.5, cfg_weight=0.5)}
for pl in PLANOS["planos"]:
    for i, l in enumerate(pl.get("audio", []), 1):
        torch.manual_seed(404 + pl["n"])
        wav = tts.generate(l["texto"], language_id="es", audio_prompt_path=f"{REFS}/{l['quien']}.wav", **AJ[l["quien"]])
        torchaudio.save(f"{OUT}/plano_{pl['n']:02d}_{i}.wav", wav.cpu(), tts.sr)
        print("voz", pl["n"], i, l["quien"], round(wav.shape[-1] / tts.sr, 1), "s", flush=True)
"""
try:
    log("preparando voces")
    sh("apt-get -qq install -y espeak-ng > /dev/null")
    sh(f"{sys.executable} -m pip install -q uv")
    sh("uv venv -q -p 3.11 /content/vz && uv pip install -q -p /content/vz/bin/python 'chatterbox-tts>=0.1.4' 'kokoro>=0.9' soundfile")
    open("/content/voces.py", "w").write(SCRIPT_VOCES)
    json.dump(PLANOS, open("/content/planos.json", "w"))
    sh(f"/content/vz/bin/python /content/voces.py /content/planos.json {VOCES}")
    log("voces listas")
except Exception:
    traceback.print_exc()
def dur_wav(f):
    import wave
    try:
        with wave.open(f) as w: return w.getnframes() / w.getframerate()
    except Exception:
        return 0

# ---------------- 1) vídeo ----------------
sh(f"{sys.executable} -m pip install -q -U 'diffusers>=0.35' 'transformers>=4.51' accelerate ftfy 'imageio[ffmpeg]'")
import torch, html, re, ftfy
from transformers import UMT5EncoderModel, AutoTokenizer
from diffusers import WanImageToVideoPipeline, WanTransformer3DModel, AutoencoderKLWan
from diffusers.utils import export_to_video
from PIL import Image
M = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
W, H, FPS = 1024, 576, 24
NEG = ("static, frozen, blurry, distorted face, deformed hands, extra fingers, extra limbs, flicker, morphing, "
       "text, subtitles, watermark, logo, cartoon, low quality")
trabajos = []
for pl in PLANOS["planos"]:
    if pl["tipo"] not in ("video", "lipsync") or not os.path.exists(f"{IN}/plano_{pl['n']:02d}.jpg"):
        continue
    p = f"{pl.get('movimiento_video', 'subtle natural movement')}. {pl['prompt']}"
    for nom, c in PLANOS["personajes"].items():
        p = p.replace("{" + nom + "}", c.get("descripcion", nom))
    trabajos.append((pl, p + ". Cinematic, realistic, natural motion, film grain."))
trabajos.sort(key=lambda x: x[0]["tipo"] != "lipsync")     # primero los que luego llevan labios

def limpiar(t):
    t = ftfy.fix_text(t); t = html.unescape(html.unescape(t)); return re.sub(r"\s+", " ", t).strip()
log("calculando textos con T5")
tok = AutoTokenizer.from_pretrained(M, subfolder="tokenizer")
te = UMT5EncoderModel.from_pretrained(M, subfolder="text_encoder", torch_dtype=torch.bfloat16, device_map="cuda")
@torch.no_grad()
def embed(t, L=512):
    x = tok([limpiar(t)], padding="max_length", max_length=L, truncation=True, add_special_tokens=True,
            return_attention_mask=True, return_tensors="pt")
    e = te(x.input_ids.cuda(), x.attention_mask.cuda()).last_hidden_state
    n = int(x.attention_mask.sum()); e[:, n:] = 0
    return e.to(torch.float16).cpu()
neg = embed(NEG); embs = {pl["n"]: embed(p) for pl, p in trabajos}
del te; gc.collect(); torch.cuda.empty_cache()

log("cargando Wan 2.2")
try:
    tr = WanTransformer3DModel.from_pretrained(M, subfolder="transformer", torch_dtype=torch.float16, device_map="cuda")
except Exception:
    tr = WanTransformer3DModel.from_pretrained(M, subfolder="transformer", torch_dtype=torch.float16, low_cpu_mem_usage=True).to("cuda")
vae = AutoencoderKLWan.from_pretrained(M, subfolder="vae", torch_dtype=torch.float32).to("cuda")
try: vae.enable_tiling()
except Exception: pass
pipe = WanImageToVideoPipeline.from_pretrained(M, transformer=tr, vae=vae, text_encoder=None, tokenizer=None,
                                               torch_dtype=torch.float16).to("cuda")
metricas = {}
for pl, p in trabajos:
    n = pl["n"]
    if time.time() - T0 > LIMITE:
        log("sin tiempo: me salto el plano", n); continue
    try:
        img = Image.open(f"{IN}/plano_{n:02d}.jpg").convert("RGB")
        s = max(W / img.width, H / img.height)
        img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
        l, t = (img.width - W) // 2, (img.height - H) // 2
        img = img.crop((l, t, l + W, t + H))
        dur = max(float(pl["duracion"]), dur_wav(f"{VOCES}/plano_{n:02d}_1.wav") + 0.3 if pl["tipo"] == "lipsync" else 0)
        frames = int(min(dur, 5) * FPS) // 4 * 4 + 1
        ti = time.time()
        v = pipe(image=img, prompt_embeds=embs[n].cuda(), negative_prompt_embeds=neg.cuda(), height=H, width=W,
                 num_frames=frames, num_inference_steps=25, guidance_scale=5.0,
                 generator=torch.Generator("cuda").manual_seed(404 + n)).frames[0]
        export_to_video(v, f"{OUT}/plano_{n:02d}.mp4", fps=FPS)
        brillo = float(sum(f.mean() for f in v[::8]) / len(v[::8]))
        metricas[n] = {"segundos": round(time.time() - ti), "fotogramas": frames, "brillo_medio": round(brillo, 3)}
        log(f"plano {n} listo", metricas[n])
    except Exception:
        traceback.print_exc(); metricas[n] = {"error": traceback.format_exc()[-800:]}
json.dump(metricas, open(f"{OUT}/metricas_video.json", "w"), indent=1)
del pipe, tr, vae; gc.collect(); torch.cuda.empty_cache()

# ---------------- 2) labios ----------------
try:
    lip = [pl for pl in PLANOS["planos"] if pl["tipo"] == "lipsync"
           and os.path.exists(f"{OUT}/plano_{pl['n']:02d}.mp4") and os.path.exists(f"{VOCES}/plano_{pl['n']:02d}_1.wav")]
    if lip and time.time() - T0 < LIMITE + 1800:
        log("preparando LatentSync 1.5")
        LS = "/content/LatentSync"
        if not os.path.exists(LS):
            sh(f"git clone -q https://github.com/bytedance/LatentSync.git {LS}")
        sh(f"{sys.executable} -m pip install -q uv")
        sh(f"cd {LS} && uv venv -q -p 3.10 /content/lsenv && uv pip install -q -p /content/lsenv/bin/python "
           f"--index-strategy unsafe-best-match -r requirements.txt")
        sh(f"cd {LS} && /content/lsenv/bin/python -c \"from huggingface_hub import hf_hub_download as d; "
           f"[d('ByteDance/LatentSync-1.5', f, local_dir='checkpoints') for f in ('latentsync_unet.pt', 'whisper/tiny.pt')]\"")
        for pl in lip:
            n = pl["n"]; ti = time.time()
            try:
                sh(f"cd {LS} && /content/lsenv/bin/python -m scripts.inference --unet_config_path configs/unet/stage2.yaml "
                   f"--inference_ckpt_path checkpoints/latentsync_unet.pt --inference_steps 20 --guidance_scale 1.5 "
                   f"--video_path {OUT}/plano_{n:02d}.mp4 --audio_path {VOCES}/plano_{n:02d}_1.wav "
                   f"--video_out_path {OUT}/plano_{n:02d}_labios.mp4")
                log(f"labios plano {n} · {time.time()-ti:.0f} s")
            except Exception:
                traceback.print_exc()
except Exception:
    traceback.print_exc()
log("FIN")
