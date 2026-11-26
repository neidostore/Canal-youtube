# Crea el cuaderno de Colab "video + labios" con los fotogramas y las voces incrustados.
# Uso: python hacer_cuaderno.py <carpeta_produccion> <carpeta_imagenes> <carpeta_voces> <salida.ipynb>
import base64, json, subprocess, sys
RAW = "https://raw.githubusercontent.com/neidostore/Canal-youtube/ccr-00644e8b-14b4ji/peliculas-ia/"

from pathlib import Path
raiz = Path(__file__).resolve().parents[2]
prod, imgs, voces, salida = map(Path, sys.argv[1:5])
planos = json.loads((prod / "planos.json").read_text())
archivos, dur_voz = {}, {}  # dur_voz ya no se usa: se mide en Colab
for pl in planos["planos"]:
    n = pl["n"]
    if pl["tipo"] in ("video", "lipsync"):
        archivos[f"plano_{n:02d}.jpg"] = RAW + (imgs / f"plano_{n:02d}.jpg").resolve().relative_to(raiz).as_posix()
for w in sorted(voces.glob("plano_*_*.wav")) if voces.exists() else []:
    archivos[w.name] = RAW + w.resolve().relative_to(raiz).as_posix()
datos = base64.b64encode(json.dumps({"planos": planos, "archivos": archivos, "dur_voz": dur_voz}).encode()).decode()
codigo = (Path(__file__).parent / "video_labios.py").read_text().replace("__DATOS__", repr(datos))
celda = lambda t, s: {"cell_type": t, "metadata": {}, "source": s.splitlines(True), **({"outputs": [], "execution_count": None} if t == "code" else {})}
nb = {"nbformat": 4, "nbformat_minor": 0,
      "metadata": {"accelerator": "GPU", "colab": {"gpuType": "T4", "provenance": []},
                   "kernelspec": {"name": "python3", "display_name": "Python 3"}},
      "cells": [
          celda("markdown", "# Neido Studio · Voces, movimiento y labios (prueba técnica)\n"
                "1. Comprueba arriba a la derecha que pone **T4**.\n"
                "2. **Entorno de ejecución → Ejecutar todo**.\n"
                "3. Tarda entre 1 y 2 horas. No cierres la pestaña ni dejes que el PC se suspenda.\n"
                "4. Al final se descarga **neido-video.zip**: mándaselo a Claude.\n"),
          celda("code", codigo),
          celda("code", "import shutil\nshutil.make_archive('/content/neido-video', 'zip', '/content/entrega')\n"
                "from google.colab import files\nfiles.download('/content/neido-video.zip')\n"
                "print('LISTO: se descarga neido-video.zip')\n")]}
salida.write_text(json.dumps(nb, ensure_ascii=False))
print(salida, round(salida.stat().st_size / 1e6, 1), "MB")
