"""Genera produccion/ranking08/escenas.json: los vídeos más vistos de YouTube (Short). Cifras: Wikipedia, a 30-ago-2026."""
import copy, json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
base = json.loads((R / "ranking07" / "escenas.json").read_text(encoding="utf-8"))
cred = json.loads((R / "ranking08" / "creditos_commons.json").read_text(encoding="utf-8"))

d = {k: copy.deepcopy(base[k]) for k in ("tema", "voz", "estilo", "formato", "marca", "musica")}
d["titulo"] = "El vídeo más visto de YouTube (no es Despacito) 🦈 Ranking"
d["ranking"] = {"titulo": "LOS VÍDEOS MÁS VISTOS DE YOUTUBE", "puestos": [5, 4, 3, 2, 1]}
d["videos"] = {
    "ninos_tablet": 4961693, "ninos_youtube": 4961698, "bebe_dibujos": 4159203, "tiburon": 5548408, "tiburones": 5548357,
    "autobus": 4208077, "bano": 6975908, "bano2": 6968111, "ninos_baile": 8612634, "concierto": 3941289,
    "tierra": 7048711, "facebook": 5201209, "redes": 4232959,
}
nombres = {"babyshark": "Foxy1219", "babyshark_gel": "Donald Trung", "fonsi": "anokarina", "fonsi2": "Nicolas Lacoste",
           "yankee": "Apoxyomenus", "youtube_hq": "BrokenSphere"}
d["fotos"] = {n: 0 for n in cred}
d["credito_fotos"] = {n: f"Foto: {nombres[n]} / {cred[n]['licencia']}" for n in cred}

ding = lambda v=0.25: {"nombre": "ding", "vol": v, "en": 0.1}
cifra = lambda t, en=2.0, color="#E53935": {"tipo": "texto", "texto": t, "pos": [0.5, 0.78], "tam": 60, "en": en, "fondo": color}
emoji = lambda e, en=1.0: {"tipo": "emoji", "emoji": e, "pos": [0.8, 0.4], "tam": 170, "en": en}

d["bloques"] = [{"nombre": "Ranking", "frases": [
    {"t": "El vídeo más visto de YouTube tiene el doble de visitas que personas hay en la Tierra.",
     "vid": ["ninos_youtube", "tierra"], "marcas": [emoji("🤯")]},
    {"t": "Ranking: los vídeos más vistos de la historia de YouTube.",
     "img": ["youtube_hq"]},

    {"t": "Número cinco: Bath Song, de Cocomelon. Una canción infantil sobre la hora del baño. Más de siete mil seiscientos millones de visitas.",
     "rank": {"n": 5, "texto": "Bath Song · 7.600 M", "emoji": "🛁"}, "sfx": ding(),
     "vid": ["bano", "bano2"], "marcas": [cifra("+7.600 M", 4.5)]},

    {"t": "Número cuatro… un anuncio. Sí: un anuncio de Facebook, de 2022, que ya supera los ocho mil millones de visitas. Seguramente lo has visto sin darte cuenta.",
     "rank": {"n": 4, "texto": "Anuncio de Facebook · 8.000 M", "emoji": "📢"}, "sfx": ding(),
     "vid": ["facebook", "redes"], "marcas": [cifra("+8.000 M", 4.5), emoji("😅", 6.5)]},

    {"t": "Número tres: Despacito, de Luis Fonsi y Daddy Yankee. Más de nueve mil cien millones.",
     "rank": {"n": 3, "texto": "Despacito · 9.100 M", "emoji": "🎤"}, "sfx": ding(),
     "img": ["fonsi", "yankee"], "marcas": [cifra("+9.100 M", 3.0)]},
    {"t": "Fue el vídeo más visto del mundo durante más de tres años… hasta que llegó un tiburón.",
     "img": ["fonsi2", "yankee"], "marcas": [emoji("🦈", 3.0)]},

    {"t": "Número dos: Wheels on the Bus, otra vez de Cocomelon. Más de nueve mil trescientos millones.",
     "rank": {"n": 2, "texto": "Wheels on the Bus · 9.300 M", "emoji": "🚌"}, "sfx": ding(),
     "vid": ["autobus", "bebe_dibujos"], "marcas": [cifra("+9.300 M", 3.0)]},

    {"t": "Y el número uno…", "vid": ["tiburon", "tiburones"]},
    {"t": "Baby Shark Dance. Más de diecisiete mil millones de visitas. Es el único vídeo de la historia que ha pasado de diez mil millones.",
     "rank": {"n": 1, "texto": "Baby Shark · 17.000 M", "emoji": "🏆"}, "sfx": ding(0.4),
     "img": ["babyshark", "babyshark_gel"], "marcas": [cifra("+17.000 M", 2.5), emoji("🦈", 1.0)]},
    {"t": "En el planeta somos unos ocho mil millones de personas. Es como si cada una lo hubiera visto dos veces.",
     "vid": ["tierra", "ninos_baile"], "marcas": [cifra("x2", 3.0, "#2E7D32")]},

    {"t": "¿Cuántas veces lo has visto tú? Te leo en los comentarios.", "vid": ["ninos_tablet", "ninos_baile"]},
    {"t": "Sígueme para más rankings en Shock Mental.", "vid": ["concierto", "tiburones"]},
]}]
(R / "ranking08" / "escenas.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
print("ok", d["credito_fotos"])
