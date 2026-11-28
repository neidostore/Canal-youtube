"""SHOCK MENTAL THUMBNAIL DIRECTOR · conceptos, render (plantilla v2), prueba en tamaño móvil y elección.

Cada vídeo largo trae en su guion «miniaturas»: 3 conceptos DISTINTOS (no variaciones de color):
  {"id": "A", "idea": "...", "emocion": "misterio", "curiosidad": "¿qué hay dentro?", "layout": "heroe|centro|numero|comparacion|misterio",
   "categoria": "ranking|ciencia|historia|misterio|tecnologia|datos", "fondo": "nombre_foto" | "gemini",
   "fondo2": "...", "texto": "¿ESTÁ|*AQUÍ*?", "chip": "...", "pos": "70% 40%", "zoom": 1.1, "numero": "#1",
   "prompt_gemini": "... (si el fondo ideal es una ilustración)"}
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

from .nucleo import REPO

MOVIL = (246, 138)   # tamaño aproximado de una miniatura en la página de inicio del móvil


def _render(concepto: dict, fondo: Path, fondo2: Path | None, destino: Path, sin_texto=False) -> dict:
    q = {k: v for k, v in concepto.items() if k not in ("idea", "emocion", "curiosidad", "prompt_gemini", "id")}
    q["fondo"] = str(fondo)
    if fondo2:
        q["fondo2"] = str(fondo2)
    if sin_texto:
        q["sin_texto"] = True
    r = subprocess.run(["node", "generar-v2.js", str(destino), json.dumps(q, ensure_ascii=False)], cwd=REPO / "miniaturas",
                       capture_output=True, text=True, timeout=300)
    if r.returncode:
        raise RuntimeError(r.stderr[-400:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def _lum(rgb: np.ndarray) -> float:
    c = rgb / 255.0
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return float((0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]).mean())


def evaluar(concepto: dict, png: Path, fondo_png: Path, caja: dict) -> dict:
    """Pruebas medibles: legible en móvil, contraste del texto, brevedad, fondo con detalle (no plano)."""
    palabras = len(concepto.get("texto", "").replace("|", " ").replace("*", "").split())
    px_movil = caja["fuente_px"] * MOVIL[0] / 1280
    fondo = np.asarray(Image.open(fondo_png).convert("RGB"), dtype=np.float32)
    x0, y0 = max(0, int(caja["x"])), max(0, int(caja["y"]))
    x1, y1 = min(1280, int(caja["x"] + caja["w"])), min(720, int(caja["y"] + caja["h"]))
    L = _lum(fondo[y0:y1, x0:x1]) if x1 > x0 and y1 > y0 else 0.0
    contraste = 1.05 / (L + 0.05)
    detalle = float(np.asarray(Image.open(fondo_png).convert("L").resize((160, 90)), dtype=np.float32).std())
    checks = {
        "legible_movil": px_movil >= 13,          # texto de al menos 13 px en una miniatura de 246 px
        "contraste": contraste >= 3.0,            # texto blanco con sombra sobre el fondo real
        "texto_corto": palabras <= 4,
        "fondo_con_fuerza": detalle >= 35,        # una imagen plana o gris no destaca
        "honesta": bool(concepto.get("curiosidad")),   # el guionista explica qué promesa hace (se revisa en Telegram)
    }
    nota = 100 * sum(checks.values()) / len(checks)
    nota = round(min(100, nota * (0.85 + 0.15 * min(1.0, contraste / 7))), 1)
    movil = png.with_name(png.stem + "_movil.png")
    Image.open(png).resize(MOVIL, Image.LANCZOS).save(movil)
    return {"nota": nota, "checks": checks, "px_movil": round(px_movil, 1), "contraste": round(contraste, 1),
            "palabras": palabras, "detalle": round(detalle, 1), "movil": str(movil)}


def dirigir(guion: dict, carpeta: Path) -> dict:
    """Genera los 3 conceptos, los evalúa y elige. Devuelve {elegida, conceptos: [...]}."""
    carpeta = carpeta.resolve()   # el render corre en otra carpeta: rutas absolutas
    salida = carpeta / "salida"
    salida.mkdir(parents=True, exist_ok=True)
    resultados = []
    for c in guion.get("miniaturas", [])[:3]:
        fondo = carpeta / "miniatura_fondo.jpg" if c.get("fondo") == "gemini" else carpeta / "fotos" / f"{c.get('fondo')}.jpg"
        fondo2 = carpeta / "fotos" / f"{c['fondo2']}.jpg" if c.get("fondo2") else None
        if not fondo.exists():
            resultados.append({**c, "error": f"falta el fondo {fondo.name}" + (" (genera la ilustración con Gemini)" if c.get("fondo") == "gemini" else "")})
            continue
        png = salida / f"miniatura_{c['id']}.png"
        caja = _render(c, fondo, fondo2, png)
        fondo_png = salida / f"miniatura_{c['id']}_fondo.png"
        _render(c, fondo, fondo2, fondo_png, sin_texto=True)
        resultados.append({**c, "png": str(png), **evaluar(c, png, fondo_png, caja)})
    validas = [r for r in resultados if "png" in r]
    if not validas:
        return {"elegida": None, "conceptos": resultados}
    elegida = guion.get("miniatura_elegida") or max(validas, key=lambda r: r["nota"])["id"]
    e = next((r for r in validas if r["id"] == elegida), validas[0])
    Image.open(e["png"]).save(salida / "miniatura.png")
    return {"elegida": e["id"], "nota": e["nota"], "conceptos": resultados}
