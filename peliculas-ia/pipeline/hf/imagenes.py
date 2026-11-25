#!/usr/bin/env python3
"""Neido Studio · imágenes con Qwen-Image (Apache 2.0) en la GPU gratuita de Hugging Face (ZeroGPU, ~5 min/día).
La clave de Hugging Face la añade el proxy de la sesión (nunca está aquí).
Uso: python3 imagenes.py <planos.json> <carpeta_salida> [n1 n2 ...]   (sin números = todos los planos)"""
import json, shutil, sys, time
from pathlib import Path
from gradio_client import Client

ESPACIO = "https://qwen-qwen-image.hf.space"
PASOS, GUIA, SEMILLA = 30, 4.0, 404


def main():
    planos = json.loads(Path(sys.argv[1]).read_text())
    out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    elegidos = {int(x) for x in sys.argv[3:]}
    c = Client(ESPACIO, token="hf_proxyinjected000000000000000000", verbose=False)
    for pl in planos["planos"]:
        if elegidos and pl["n"] not in elegidos:
            continue
        texto = pl["prompt"]
        for nombre, p in planos["personajes"].items():
            texto = texto.replace("{" + nombre + "}", p.get("descripcion", nombre))
        t = time.time()
        img, semilla = c.predict(prompt=f"{texto}. {planos['estilo']}", seed=SEMILLA + pl["n"], randomize_seed=False,
                                 aspect_ratio="16:9", guidance_scale=GUIA, num_inference_steps=PASOS,
                                 prompt_enhance=False, api_name="/infer")
        ruta = img["path"] if isinstance(img, dict) else img
        destino = out / f"plano_{pl['n']:02d}{Path(ruta).suffix or '.png'}"
        shutil.copy(ruta, destino)
        print(f"plano {pl['n']} · {time.time()-t:.0f} s · {destino}", flush=True)


if __name__ == "__main__":
    main()
