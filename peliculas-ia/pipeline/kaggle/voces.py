# Neido Studio · Etapa "voces" (Kaggle, GPU T4).
# Genera cada línea de diálogo, pensamiento y narración con Chatterbox Multilingual (licencia MIT).
# Cada personaje tiene una voz fija: se crea a partir de una voz de referencia de Kokoro (Apache 2.0),
# así no se clona la voz de ninguna persona real. Salida: /kaggle/working/entrega/plano_NN_K.wav
#
# ⚠️ BORRADOR SIN PROBAR: nombres de paquetes, voces y parámetros se validan en la prueba técnica.
import json, os, subprocess, sys, time
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "chatterbox-tts", "kokoro>=0.9", "soundfile"], check=True)
import soundfile as sf, torch, torchaudio

PLANOS = json.loads(__PLANOS_JSON__)
OUT = "/kaggle/working/entrega"; os.makedirs(OUT, exist_ok=True)
REFS = "/kaggle/working/refs"; os.makedirs(REFS, exist_ok=True)
t0 = time.time()

# 1) voces semilla con Kokoro (español): una por personaje
from kokoro import KPipeline
kp = KPipeline(lang_code="e")
SEMILLAS = {"narrador": "em_alex", "santi": "em_santa", "margaret": "ef_dora"}
frase = "Buenas noches. Esta es una muestra de voz para la película, leída con calma y claridad, sin prisa."
for quien, voz in SEMILLAS.items():
    audio = [a for _, _, a in kp(frase, voice=voz)]
    sf.write(f"{REFS}/{quien}.wav", torch.cat([torch.as_tensor(a) for a in audio]).numpy(), 24000)

# 2) líneas con Chatterbox, usando la voz semilla de cada personaje
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
tts = ChatterboxMultilingualTTS.from_pretrained(device="cuda")
AJUSTES = {  # exageración = expresividad; cfg = ritmo/fidelidad
    "narrador": dict(exaggeration=0.35, cfg_weight=0.5),
    "santi": dict(exaggeration=0.65, cfg_weight=0.4),
    "margaret": dict(exaggeration=0.5, cfg_weight=0.5),
}
for pl in PLANOS["planos"]:
    for i, linea in enumerate(pl.get("audio", []), 1):
        quien = linea["quien"]
        wav = tts.generate(linea["texto"], language_id="es", audio_prompt_path=f"{REFS}/{quien}.wav", **AJUSTES[quien])
        torchaudio.save(f"{OUT}/plano_{pl['n']:02d}_{i}.wav", wav.cpu(), tts.sr)
        print(f"plano {pl['n']} línea {i} ({quien}) · {time.time()-t0:.0f} s", flush=True)

json.dump({"segundos_totales": round(time.time()-t0)}, open("/kaggle/working/metricas_voces.json", "w"))
print("FIN voces", round(time.time()-t0), "s")
