"""Medios con licencia: fotos de Wikimedia Commons (con autor y licencia) y clips de Pexels (catálogo sin conexión).

Commons limita las peticiones (error 429): se hacen pausas y reintentos. User-Agent genérico, sin datos personales.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

from .nucleo import DATOS, PROD

UA = {"User-Agent": "CuriosidadesBot/1.0 (generic research script; python-urllib)"}
LICENCIAS_OK = ("CC0", "Public domain", "PD", "CC BY", "CC BY-SA", "FAL", "No restrictions")
CATALOGO = DATOS / "pexels.parquet"


def _get(url: str, intentos: int = 5) -> bytes:
    for k in range(intentos):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read()
        except Exception as e:  # 429 u otros: espera creciente
            if k == intentos - 1:
                raise
            time.sleep(10 * (k + 1))
    raise RuntimeError("inalcanzable")


def buscar_commons(consulta: str, n: int = 7) -> list[dict]:
    """Busca fotos en Commons. Devuelve título, tamaño y licencia."""
    u = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "generator": "search", "gsrsearch": f"{consulta} filetype:bitmap",
        "gsrnamespace": 6, "gsrlimit": n, "prop": "imageinfo", "iiprop": "size|extmetadata",
        "iiextmetadatafilter": "LicenseShortName"})
    d = json.loads(_get(u))
    time.sleep(5)
    pages = sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    out = []
    for p in pages:
        ii = p["imageinfo"][0]
        out.append({"titulo": p["title"][5:], "ancho": ii["width"], "alto": ii["height"],
                    "licencia": ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "?")})
    return out


def licencia_valida(lic: str) -> bool:
    return any(lic.startswith(x) or x in lic for x in LICENCIAS_OK) and "NC" not in lic and "ND" not in lic


def bajar_commons(carpeta: Path, fotos: dict[str, str]) -> dict:
    """fotos = {nombre: "Titulo del archivo.jpg"}. Guarda en carpeta/fotos y anota créditos. Rechaza licencias no libres."""
    (carpeta / "fotos").mkdir(parents=True, exist_ok=True)
    cred_f = carpeta / "creditos_commons.json"
    cred = json.loads(cred_f.read_text(encoding="utf-8")) if cred_f.exists() else {}
    for nombre, titulo in fotos.items():
        if (carpeta / "fotos" / f"{nombre}.jpg").exists() and nombre in cred:
            continue
        u = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query", "format": "json", "titles": "File:" + titulo,
            "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 1600})
        p = next(iter(json.loads(_get(u))["query"]["pages"].values()))
        if "imageinfo" not in p:
            raise ValueError(f"no existe en Commons: {titulo}")
        ii = p["imageinfo"][0]
        m = ii["extmetadata"]
        lic = m.get("LicenseShortName", {}).get("value", "")
        if not licencia_valida(lic):
            raise ValueError(f"licencia no válida para {titulo}: {lic}")
        img = _get(ii.get("thumburl") or ii["url"])
        (carpeta / "fotos" / f"{nombre}.jpg").write_bytes(img)
        autor = re.sub(r"<[^>]+>", "", m.get("Artist", {}).get("value", "")).strip()
        autor = re.split(r"\(talk\)|\n| from |Wikimedia Commons|\.\(", autor)[0].strip(" ,.-") or "Wikimedia Commons"
        cred[nombre] = {"titulo": titulo, "autor": autor[:60], "licencia": lic, "url": ii["descriptionurl"]}
        time.sleep(5)
    cred_f.write_text(json.dumps(cred, ensure_ascii=False, indent=1), encoding="utf-8")
    return cred


def credito_texto(c: dict) -> str:
    lic = c["licencia"]
    return f"Foto: {c['autor']} / {'dominio público' if 'Public domain' in lic or lic == 'PD' else lic}"


def buscar_pexels(patron: str, n: int = 8, min_s: int = 5, max_s: int = 40) -> list[dict]:
    """Busca clips en el catálogo sin conexión (regex sobre el título), ordenados por popularidad."""
    import pandas as pd
    d = pd.read_parquet(CATALOGO)
    d["id"] = d["loc"].str.extract(r"-(\d+)/?$", expand=False)
    d["t"] = d.title.str.split(" · ").str[0]
    d["duration"] = pd.to_numeric(d.duration, errors="coerce")
    d["view_count"] = pd.to_numeric(d.view_count, errors="coerce")
    d = d[(d.duration >= min_s) & (d.duration <= max_s)]
    m = d[d.t.str.contains(patron, case=False, regex=True)].sort_values("view_count", ascending=False).head(n)
    return [{"id": int(r.id), "segundos": int(r.duration), "titulo": r.t[:90]} for r in m.itertuples()]


def _bash() -> str:
    for c in (shutil.which("bash"), r"C:\Program Files\Git\bin\bash.exe",
              str(Path.home() / r"AppData\Local\Programs\Git\bin\bash.exe")):
        if c and Path(c).exists():
            return c
    raise RuntimeError("no encuentro Git Bash")


def bajar_pexels(ids: list[int]) -> dict[int, bool]:
    """Descarga clips a produccion/clips con el script existente. Devuelve {id: ok}."""
    clips = PROD / "clips"
    faltan = [i for i in ids if not (clips / f"{i}.mp4").exists()]
    if faltan:
        subprocess.run([_bash(), "descargar.sh", *map(str, faltan)], cwd=clips, capture_output=True, text=True, timeout=900)
    return {i: (clips / f"{i}.mp4").exists() for i in ids}
