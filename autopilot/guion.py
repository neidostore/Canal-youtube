"""Formato estándar de guion de Shock Mental → escenas.json de montar.py.

Un guion es un JSON con esta forma (Short):
{
  "formato": "short", "tipo": "ranking" | "curiosidad" | "historia", "categoria": "dinero",
  "tema": "...", "titulo_ranking": "LO MÁS LOCO VENDIDO",          # solo rankings (≤ 30 caracteres)
  "titulo": "...", "descripcion": "...", "comentario": "...", "etiquetas": ["..."],
  "fotos": {"nombre": "Archivo de Commons.jpg"},                   # solo Commons con licencia libre
  "clips": {"nombre": 1234567},                                    # ids del catálogo de Pexels
  "frases": [
    {"t": "texto narrado", "img": ["nombre"] | "vid": ["nombre"],
     "rank": {"n": 5, "texto": "Algo · 2,9 M$", "emoji": "📱"},       # solo al presentar un puesto
     "cifra": "2,9 M$", "cifra_en": 3.0, "emoji": "😂", "emoji_en": 1.0, "kw": "palabra clave"}
  ],
  "fuentes": [{"dato": "...", "fuente": "Medio", "url": "https://..."}],
  "portada_segundo": 2
}
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

from . import medios
from .nucleo import PROD

BASE_ESTILO = {
    "tema": "shock",
    "voz": {"idioma": "es-US", "nombre": "es-US-Chirp3-HD-Achird", "velocidad": 1.15},
    "estilo": {"dinamico": True, "plano": 1.4},
    "formato": "vertical",
    "marca": {"logo": "marca/shockmental/perfil-sin-eslogan.png", "nombre": "SHOCK MENTAL"},
    "musica": {"archivo": "musica/wallpaper.mp3", "volumen": 0.09, "credito": '"Wallpaper" de Kevin MacLeod (incompetech.com)'},
}
PALABRAS_POR_SEGUNDO = 2.9   # voz del canal a 1,15x (medido en los rankings 07-09)
BASE_LARGO = {
    "tema": "shock", "tarjetas": "tarjetas-shock.html",
    "intro": {"video": "marca/shockmental/intro/intro.mp4", "audio": "marca/shockmental/intro/intro_audio.wav"},
    "musica": BASE_ESTILO["musica"], "estilo": {"dinamico": True, "plano": 1.6},
    "marco": {"titulo": "SHOCK&nbsp;<i>MENTAL</i>", "lema": "Tu dosis de asombro 🧠⚡", "logo": "marca/shockmental/perfil-sin-eslogan.png"},
    "voz": BASE_ESTILO["voz"], "videos_inicio": {},
}
NUMEROS = ["", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "once", "doce"]


def todas_frases(g: dict) -> list[dict]:
    """Frases de un Short (g.frases) o de un largo (g.bloques[].frases)."""
    if g.get("formato") == "largo":
        return [f for b in g.get("bloques", []) for f in b.get("frases", [])]
    return g.get("frases", [])


def duracion_estimada(g: dict) -> float:
    fr = todas_frases(g)
    return sum(len(f["t"].split()) for f in fr) / PALABRAS_POR_SEGUNDO + 0.4 * len(fr)


def validar(g: dict, cfg: dict | None = None) -> list[str]:
    """Errores que impiden producir. Lista vacía = válido."""
    e = []
    for k in ("formato", "tipo", "tema", "titulo", "descripcion", "fuentes", "bloques" if g.get("formato") == "largo" else "frases"):
        if not g.get(k):
            e.append(f"falta «{k}»")
    if e:
        return e
    nombres_img, nombres_vid = set(g.get("fotos", {})), set(g.get("clips", {}))
    frases = todas_frases(g)
    for i, f in enumerate(frases):
        if not f.get("t", "").strip():
            e.append(f"frase {i + 1} sin texto")
        img, vid = f.get("img"), f.get("vid")
        if not img and not vid:
            e.append(f"frase {i + 1} sin imagen ni clip")
        if img and vid:
            e.append(f"frase {i + 1}: usa img o vid, no las dos")
        for n in img or []:
            if n not in nombres_img:
                e.append(f"frase {i + 1}: foto «{n}» no declarada en fotos")
        for n in vid or []:
            if n not in nombres_vid:
                e.append(f"frase {i + 1}: clip «{n}» no declarado en clips")
    gancho = frases[0]["t"]
    if len(gancho.split()) > 30:
        e.append(f"gancho demasiado largo ({len(gancho.split())} palabras; máximo 30)")
    if g["formato"] == "largo":
        mn = (cfg or {}).get("calidad", {}).get("largo_min_segundos", 240)
        if duracion_estimada(g) < mn:
            e.append(f"duración estimada {duracion_estimada(g):.0f} s < {mn} s para un vídeo largo")
    if g["formato"] == "short" and g["tipo"] == "ranking":
        if not g.get("titulo_ranking"):
            e.append("falta titulo_ranking")
        elif len(g["titulo_ranking"]) > 32:
            e.append("titulo_ranking demasiado largo (no cabe en pantalla, máximo 32)")
        puestos = sorted(f["rank"]["n"] for f in frases if f.get("rank"))
        if puestos != [1, 2, 3, 4, 5]:
            e.append(f"el ranking debe tener los puestos 1-5 exactamente una vez (tiene {puestos})")
    if not all(f.get("url", "").startswith("http") for f in g["fuentes"]):
        e.append("todas las fuentes necesitan URL")
    max_s = (cfg or {}).get("calidad", {}).get("short_max_segundos", 75)
    if g["formato"] == "short" and duracion_estimada(g) > max_s:
        e.append(f"duración estimada {duracion_estimada(g):.0f} s > {max_s} s: recorta frases")
    return e


def _frase_larga(f: dict) -> dict:
    x = {"t": f["t"]}
    if f.get("img"):
        x["img"] = f["img"]
    else:
        x["vid"] = f["vid"]
    for k in ("kw", "rotulo"):
        if f.get(k):
            x[k] = f[k]
    if f.get("emoji"):
        x["marcas"] = [{"tipo": "emoji", "emoji": f["emoji"], "pos": [0.86, f.get("emoji_y", 0.5)], "tam": 200}]
    return x


def a_escenas_largo(g: dict, cred: dict) -> dict:
    """Vídeo largo horizontal con el estilo de las Dosis: gancho, intro, bloques numerados y cierre."""
    d = copy.deepcopy(BASE_LARGO)
    d["titulo"] = g["titulo"]
    d["videos"] = dict(g.get("clips", {}))
    d["fotos"] = {n: 0 for n in g.get("fotos", {})}
    d["credito_fotos"] = {n: medios.credito_texto(cred[n]) for n in g.get("fotos", {})}
    bloques = []
    for i, b in enumerate(g["bloques"]):
        frases = [_frase_larga(f) for f in b["frases"]]
        if b.get("numero"):
            n = b["numero"]
            frases.insert(0, {"t": f"Número {NUMEROS[n] if n < len(NUMEROS) else n}.",
                              "card": {"tipo": "numero", "n": n, "tema": b.get("etiqueta", "")}})
        bloques.append({"nombre": b["nombre"], "frases": frases})
        if i == 0:
            bloques.append({"nombre": "Intro", "intro": True})   # la intro va justo después del gancho
    bloques.append({"nombre": "Cierre", "final": 1.0, "frases": [
        {"t": g.get("cierre_pregunta", "¿Qué te ha sorprendido más? Te leo en los comentarios."), "card": {"tipo": "final"}},
        {"t": g.get("cierre_suscribete", "Y si quieres tu próxima dosis de asombro, suscríbete a Shock Mental."), "card": {"tipo": "final"}}]})
    d["bloques"] = bloques
    return d


def _voz_oficial(g: dict | None = None) -> dict:
    """Perfil oficial, o el elegido para este vídeo desde Telegram (🎙️ VOZ). «Regenerar» varía la velocidad un 1 %."""
    from .voz import PERFILES, perfil_actual
    p = dict(perfil_actual())
    if g and g.get("perfil_voz") in PERFILES:
        p["velocidad"] = PERFILES[g["perfil_voz"]]["velocidad"]
    if g and g.get("regenerar_voz"):
        p["velocidad"] = round(p["velocidad"] + (0.01 if g["regenerar_voz"] % 2 else -0.01), 2)
    return {"idioma": p["idioma"], "nombre": p["nombre"], "velocidad": p["velocidad"],
            **({"modelo": p["modelo"], "instruccion": p.get("instruccion", "")} if p.get("modelo") else {})}


def _texto_voz(frases_src: list[dict], frases_out: list[dict]):
    """El guionista puede escribir en «voz» la versión hablada (con pausas y dirección); los subtítulos usan «t»."""
    from .voz import perfil_actual
    if perfil_actual().get("estilo") == "actual":   # el gerente eligió la interpretación de siempre (A): sin dirección extra
        return
    for s, o in zip(frases_src, frases_out):   # misma cantidad y orden (las tarjetas de número se excluyen antes)
        if s.get("voz"):
            o["voz"] = s["voz"]


def a_escenas(g: dict, cred: dict) -> dict:
    """Convierte un guion validado en escenas.json para montar.py."""
    if g["formato"] == "largo":
        d = a_escenas_largo(g, cred)
        d["voz"] = _voz_oficial(g)
        for b_src in g["bloques"]:
            for b in d["bloques"]:
                if b.get("nombre") == b_src["nombre"]:
                    _texto_voz(b_src["frases"], [f for f in b["frases"] if "card" not in f])
        return d
    d = copy.deepcopy(BASE_ESTILO)
    d["voz"] = _voz_oficial(g)
    d["titulo"] = g["titulo"]
    if g["tipo"] == "ranking":
        d["ranking"] = {"titulo": g["titulo_ranking"].upper(), "puestos": [5, 4, 3, 2, 1], "desde_frase": 1}
    d["videos"] = dict(g.get("clips", {}))
    d["fotos"] = {n: 0 for n in g.get("fotos", {})}
    d["credito_fotos"] = {n: medios.credito_texto(cred[n]) for n in g.get("fotos", {})}
    frases = []
    for f in g["frases"]:
        x = {"t": f["t"]}
        if f.get("img"):
            x["img"] = f["img"]
        else:
            x["vid"] = f["vid"]
        marcas = []
        if f.get("rank"):
            x["rank"] = f["rank"]
            x["sfx"] = {"nombre": "ding", "vol": 0.4 if f["rank"]["n"] == 1 else 0.25, "en": 0.1}
        if f.get("cifra"):
            marcas.append({"tipo": "texto", "texto": f["cifra"], "pos": [0.5, 0.78], "tam": 60,
                           "en": f.get("cifra_en", 2.0), "fondo": f.get("cifra_color", "#E53935")})
        if f.get("emoji"):
            marcas.append({"tipo": "emoji", "emoji": f["emoji"], "pos": [0.8, 0.4], "tam": 170, "en": f.get("emoji_en", 1.0)})
        if marcas:
            x["marcas"] = marcas
        if f.get("kw") and g["tipo"] != "ranking":
            x["kw"] = f["kw"]
        frases.append(x)
    _texto_voz(g["frases"], frases)
    if g.get("portada_texto"):   # titular grande sobre la imagen del gancho: sirve de portada del Short
        frases[0].setdefault("marcas", []).insert(0, {"tipo": "texto", "texto": g["portada_texto"], "pos": [0.5, 0.30],
                                                      "tam": 96, "en": 0.0, "fondo": "#FFD21F", "tinta": "#0B0B10"})
    bloque = {"nombre": "Ranking" if g["tipo"] == "ranking" else g["tema"], "frases": frases}
    if g["tipo"] != "ranking":
        bloque["final"] = 0.4
    d["bloques"] = [bloque]
    return d


def preparar(g: dict, video_id: str) -> Path:
    """Descarga fotos y clips, y escribe produccion/auto/<id>/escenas.json. Devuelve la carpeta."""
    carpeta = PROD / "auto" / video_id
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "guion.json").write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
    cred = medios.bajar_commons(carpeta, g.get("fotos", {})) if g.get("fotos") else {}
    ok = medios.bajar_pexels(list(g.get("clips", {}).values()))
    faltan = [n for n, i in g.get("clips", {}).items() if not ok.get(i)]
    if faltan:
        raise ValueError(f"clips de Pexels no disponibles: {faltan} (elige otros ids)")
    (carpeta / "escenas.json").write_text(json.dumps(a_escenas(g, cred), ensure_ascii=False, indent=1), encoding="utf-8")
    return carpeta


def slug(texto: str) -> str:
    t = re.sub(r"[^a-z0-9]+", "-", texto.lower().translate(str.maketrans("áéíóúñü", "aeiounu"))).strip("-")
    return t[:40]
