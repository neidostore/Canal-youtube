"""Agente 8 · Control de calidad automático (técnico + editorial medible) y puntuación 0-100 con vetos."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import numpy as np

# ---------- comprobaciones técnicas ----------


def _ff(args: list[str]) -> str:
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *args], capture_output=True, text=True).stderr


def duracion(video: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def _pcm(ruta: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ruta), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def _env(x: np.ndarray, ms: int = 20) -> np.ndarray:
    n = int(16000 * ms / 1000)
    k = len(x) // n
    return 20 * np.log10(np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(1)) + 1e-6)


def cortes_audio(narracion: Path, final: Path) -> list[float]:
    """Instantes (s) en que el audio final cae mientras la voz limpia suena: cortes de audio."""
    ev, ef = _env(_pcm(narracion)), _env(_pcm(final))
    m = min(len(ev), len(ef))
    return [round(k * 0.02, 2) for k in range(m) if ev[k] > -28 and ef[k] < ev[k] - 18]


def sonoridad(video: Path) -> float:
    s = _ff(["-i", str(video), "-af", "ebur128", "-f", "null", "-"])
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", s)
    return float(m[-1]) if m else 0.0


def negros(video: Path) -> list[tuple[float, float]]:
    s = _ff(["-i", str(video), "-vf", "blackdetect=d=0.5:pix_th=0.08", "-an", "-f", "null", "-"])
    return [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", s)]


# ---------- parecido con vídeos anteriores ----------
VACIAS = set("el la los las un una de del y en que por para con es al lo se su sus más mas como o a no ya shorts ranking".split())


def _bolsa(texto: str) -> set[str]:
    t = texto.lower().translate(str.maketrans("áéíóúñü", "aeiounu"))
    return {w for w in re.findall(r"[a-z0-9]{3,}", t) if w not in VACIAS}


def parecido(a: str, b: str) -> float:
    x, y = _bolsa(a), _bolsa(b)
    return len(x & y) / max(1, len(x | y))


# ---------- revisión completa ----------


def revisar(video_id: str, carpeta: Path, guion: dict, anteriores: list[dict], cfg: dict) -> dict:
    """Devuelve {ok, vetos, avisos, medidas, puntuacion, desglose}. Un veto bloquea siempre."""
    q = cfg["calidad"]
    vetos, avisos, medidas = [], [], {}
    video = carpeta / "salida" / "video.mp4"
    if not video.exists():
        return {"ok": False, "vetos": ["no se ha generado el vídeo"], "avisos": [], "medidas": {}, "puntuacion": 0}

    dur = medidas["duracion"] = round(duracion(video), 1)
    if guion["formato"] == "short" and dur > q["short_max_segundos"]:
        vetos.append(f"dura {dur:.0f} s; máximo {q['short_max_segundos']} s para un Short")
    if guion["formato"] == "largo" and dur < q["largo_min_segundos"]:
        vetos.append(f"dura {dur:.0f} s; mínimo {q['largo_min_segundos']} s para un vídeo largo")

    narr = carpeta / "trabajo" / "narracion.wav"
    if narr.exists():
        c = cortes_audio(narr, video)
        medidas["cortes_audio"] = len(c)
        if c:
            vetos.append(f"cortes de audio en {', '.join(map(str, c[:5]))} s")
    lufs = medidas["lufs"] = sonoridad(video)
    if not -18 <= lufs <= -11:
        avisos.append(f"volumen {lufs} LUFS fuera de -18…-11")
    n = negros(video)
    medidas["negros"] = n
    if any(b - a > 1.0 for a, b in n):
        vetos.append(f"pantalla en negro más de 1 s en {n}")

    # editorial medible
    cred_f = carpeta / "creditos_commons.json"
    cred = json.loads(cred_f.read_text(encoding="utf-8")) if cred_f.exists() else {}
    sin_credito = [x for x in guion.get("fotos", {}) if x not in cred]
    if sin_credito:
        vetos.append(f"fotos sin licencia verificada: {sin_credito}")
    fuentes = guion.get("fuentes", [])
    verificacion = guion.get("verificacion", {})
    dudosos = [d for d in verificacion.get("datos", []) if d.get("estado") != "verificado"]
    if not fuentes:
        vetos.append("sin fuentes")
    if dudosos:
        vetos.append(f"{len(dudosos)} dato(s) sin verificar: " + "; ".join(d.get("dato", "")[:60] for d in dudosos[:3]))
    if guion["formato"] == "short" and "#shorts" not in guion["titulo"].lower():
        avisos.append("al título del Short le falta #shorts")
    if len(guion["titulo"]) > 100:
        vetos.append("título de más de 100 caracteres")
    max_par, con_quien = 0.0, None
    for a in anteriores:
        p = max(parecido(guion["tema"], a.get("tema") or ""), parecido(guion["titulo"], a.get("titulo") or ""))
        if p > max_par:
            max_par, con_quien = p, a.get("titulo")
    medidas["parecido_max"] = round(max_par, 2)
    if max_par > q["similitud_maxima"]:
        vetos.append(f"demasiado parecido ({max_par:.0%}) a «{con_quien}»")

    punt, desglose = puntuar(guion, medidas, len(fuentes), len(dudosos), vetos, max_par)
    return {"ok": not vetos and punt >= q["nota_minima"], "vetos": vetos, "avisos": avisos,
            "medidas": medidas, "puntuacion": punt, "desglose": desglose}


def puntuar(guion: dict, medidas: dict, n_fuentes: int, n_dudosos: int, vetos: list, parecido_max: float):
    """0-100. Los criterios subjetivos los aporta el guionista en guion['autoevaluacion'] (0-10 cada uno);
    los medibles se calculan aquí y SIEMPRE mandan. Con vetos, la nota se corta a 0 (bloqueado)."""
    a = guion.get("autoevaluacion", {})
    f = lambda k: max(0, min(10, float(a.get(k, 5)))) / 10
    dur = medidas.get("duracion", 0)
    reten = 1.0 if (guion["formato"] == "short" and dur <= 60) or (guion["formato"] == "largo" and 240 <= dur <= 900) else 0.6
    from .guion import todas_frases
    gancho_pal = len(todas_frases(guion)[0]["t"].split())
    d = {
        "interes": 15 * f("interes"),
        "originalidad": 10 * (1 - min(1.0, parecido_max / 0.55)) * 0.5 + 10 * f("originalidad") * 0.5,
        "gancho": 15 * (0.5 * f("gancho") + 0.5 * (1.0 if gancho_pal <= 18 else 0.5)),
        "retencion": 15 * (0.5 * reten + 0.5 * f("retencion")),
        "valor": 10 * f("valor"),
        "verificabilidad": 15 * (0 if n_dudosos else min(1.0, n_fuentes / max(1, len(guion.get("verificacion", {}).get("datos", [])) or 1))),
        "calidad_av": 10 * (0 if medidas.get("cortes_audio") else (1.0 if -18 <= medidas.get("lufs", -14) <= -11 else 0.7)),
        "conversion": 10 * f("conversion"),
    }
    total = round(sum(d.values()), 1)
    return (0.0 if vetos else total), {k: round(v, 1) for k, v in d.items()}
