#!/usr/bin/env python3
"""Lanza una etapa de generación en Kaggle (GPU T4 gratuita), espera a que termine y descarga el resultado.

Etapas (cada una es un script en pipeline/kaggle/<etapa>.py):
  imagenes  → clips/plano_NN.png (+ hojas de personaje)
  voces     → audio/plano_NN_K.wav
  video     → clips/plano_NN.mp4   (anima las imágenes; usa la salida de "imagenes")
  labios    → clips/plano_NN.mp4   (sincroniza labios en los planos "lipsync"; usa "video" y "voces")

Uso:  python3 lanzar.py <etapa> <carpeta_produccion>
Requisitos: Kaggle CLI (pip install kaggle), token en ~/.kaggle/access_token y acceso de red a api.kaggle.com.

Cómo funciona: copia el script de la etapa y planos.json a una carpeta temporal, escribe kernel-metadata.json
(GPU e internet activados), hace `kaggle kernels push`, consulta `kaggle kernels status` hasta que termina
y baja la salida con `kaggle kernels output` a la carpeta de la producción.
"""
import json, shutil, subprocess, sys, time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DEPENDE = {"video": ["imagenes"], "labios": ["video", "voces"]}
DESTINO = {"imagenes": "clips", "voces": "audio", "video": "clips", "labios": "clips"}


def kaggle(*a):
    r = subprocess.run(["kaggle", *a], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"kaggle {' '.join(a)} falló:\n{r.stdout}\n{r.stderr}")
    return r.stdout


def usuario():
    # el CLI resuelve el usuario a partir del token
    salida = kaggle("config", "view")
    for l in salida.splitlines():
        if l.strip().startswith("- username:"):
            return l.split(":", 1)[1].strip()
    sys.exit("No se pudo saber el usuario de Kaggle (¿token configurado?)")


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    etapa, prod = sys.argv[1], Path(sys.argv[2]).resolve()
    user = usuario()
    slug = f"neido-{etapa}"
    tmp = prod / "salida" / f"kaggle-{etapa}"
    shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
    # el script lleva incrustado planos.json para no depender de datasets
    planos = (prod / "planos.json").read_text(encoding="utf-8")
    codigo = (AQUI / f"{etapa}.py").read_text(encoding="utf-8").replace("__PLANOS_JSON__", json.dumps(planos))
    (tmp / f"{slug}.py").write_text(codigo, encoding="utf-8")
    meta = {
        "id": f"{user}/{slug}", "title": slug, "code_file": f"{slug}.py",
        "language": "python", "kernel_type": "script", "is_private": True,
        "enable_gpu": True, "enable_internet": True,
        "dataset_sources": [], "competition_sources": [],
        "kernel_sources": [f"{user}/neido-{d}" for d in DEPENDE.get(etapa, [])],
    }
    (tmp / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))
    print(kaggle("kernels", "push", "-p", str(tmp), "--accelerator", "NvidiaTeslaT4"))
    inicio = time.time()
    while True:
        time.sleep(60)
        estado = kaggle("kernels", "status", f"{user}/{slug}").strip()
        print(f"[{(time.time()-inicio)/60:5.1f} min] {estado}")
        if "complete" in estado.lower():
            break
        if "error" in estado.lower() or "cancel" in estado.lower():
            kaggle("kernels", "output", f"{user}/{slug}", "-p", str(tmp / "salida"))
            sys.exit(f"La etapa {etapa} falló. Registro en {tmp/'salida'}")
    kaggle("kernels", "output", f"{user}/{slug}", "-p", str(tmp / "salida"))
    destino = prod / DESTINO[etapa]; destino.mkdir(exist_ok=True)
    n = 0
    for f in (tmp / "salida").rglob("*"):
        if f.suffix in (".png", ".mp4", ".wav") and f.parent.name == "entrega":
            shutil.copy(f, destino / f.name); n += 1
    print(f"Etapa {etapa}: {n} archivos en {destino} · {(time.time()-inicio)/60:.1f} min")


if __name__ == "__main__":
    main()
