"""Genera produccion/ranking07/escenas.json: cosas más locas vendidas por millones (Short)."""
import copy, json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
base = json.loads((R / "ranking06" / "escenas.json").read_text(encoding="utf-8"))
cred = json.loads((R / "ranking07" / "creditos_commons.json").read_text(encoding="utf-8"))

d = {k: copy.deepcopy(base[k]) for k in ("tema", "voz", "estilo", "formato", "marca", "musica")}
d["titulo"] = "Pagó 6 millones por un plátano… y se lo comió 🍌 Ranking"
d["ranking"] = {"titulo": "LO MÁS LOCO VENDIDO POR MILLONES", "puestos": [5, 4, 3, 2, 1]}
d["videos"] = {
    "lluvia_dinero": 5912047, "dolares": 5466776, "contar": 855388, "contar2": 6700653,
    "martillo": 6101343, "subasta": 6664815, "movil": 854321, "cripto": 7578639,
    "diamantes": 5084332, "diamantes2": 5106444, "museo": 8771643, "museo2": 3960175,
    "yates": 856856, "sorpresa": 8626645, "sorpresa2": 8626657,
}


def autor(n):
    a = cred[n]["autor"].split(" (talk)")[0].split("\n")[0].strip()
    lic = cred[n]["licencia"]
    return f"Foto: {a} / dominio público" if "Public domain" in lic else f"Foto: {a} / {lic}"


d["fotos"] = {n: 0 for n in cred}
d["credito_fotos"] = {n: autor(n) for n in cred}
d["credito_fotos"]["salvator"] = "Leonardo da Vinci (atribuido) / dominio público"

ding = lambda v=0.25: {"nombre": "ding", "vol": v, "en": 0.1}
cifra = lambda t, en=2.0, color="#E53935": {"tipo": "texto", "texto": t, "pos": [0.5, 0.78], "tam": 60, "en": en, "fondo": color}
emoji = lambda e, en=1.0: {"tipo": "emoji", "emoji": e, "pos": [0.8, 0.4], "tam": 170, "en": en}

d["bloques"] = [{"nombre": "Ranking", "frases": [
    {"t": "Alguien pagó seis millones de dólares por un plátano pegado a la pared con cinta… y luego se lo comió.",
     "img": ["platano_cinta"], "marcas": [emoji("🍌")]},
    {"t": "Ranking: las cosas más locas que se han vendido por millones.",
     "vid": ["lluvia_dinero", "martillo"]},

    {"t": "Número cinco: un tuit. El primero de la historia de Twitter, escrito por su creador, Jack Dorsey. Se vendió en 2021 por dos millones novecientos mil dólares.",
     "rank": {"n": 5, "texto": "Un tuit · 2,9 M$", "emoji": "📱"}, "sfx": ding(),
     "img": ["dorsey"], "marcas": [cifra("2,9 M$", 4.0)]},
    {"t": "Un año después, su dueño intentó revenderlo… y la mejor oferta fue de unos doscientos ochenta dólares.",
     "vid": ["movil", "cripto"], "marcas": [cifra("280 $", 2.5, "#2E7D32"), emoji("😂", 3.0)]},

    {"t": "Número cuatro: el plátano. Es una obra de arte de Maurizio Cattelan, y en 2024 se subastó por seis millones doscientos mil dólares.",
     "rank": {"n": 4, "texto": "Un plátano · 6,2 M$", "emoji": "🍌"}, "sfx": ding(),
     "img": ["platano_cinta"], "marcas": [cifra("6,2 M$", 4.0)]},
    {"t": "Su comprador, el empresario de criptomonedas Justin Sun, se lo comió delante de la prensa. El plátano había costado menos de medio dólar.",
     "img": ["justin_sun"], "marcas": [emoji("😋", 1.5)]},

    {"t": "Número tres: una carta de Pokémon. Logan Paul compró esta Pikachu Illustrator por más de cinco millones de dólares…",
     "rank": {"n": 3, "texto": "Carta Pokémon · 16,5 M$", "emoji": "🃏"}, "sfx": ding(),
     "img": ["logan_paul", "logan_paul2"]},
    {"t": "Y en febrero de 2026 la vendió por dieciséis millones y medio. Es la carta de Pokémon más cara de la historia.",
     "vid": ["diamantes", "diamantes2"], "marcas": [cifra("16,5 M$", 0.8), emoji("🏆", 2.0)]},

    {"t": "Número dos: un cuadro que se destruyó a sí mismo. En 2018, justo cuando se vendía este Banksy, una trituradora escondida en el marco lo hizo tiras.",
     "rank": {"n": 2, "texto": "Banksy triturado · 25,4 M$", "emoji": "🎨"}, "sfx": ding(),
     "img": ["banksy_globo", "sothebys2"], "marcas": [emoji("😱", 4.5)]},
    {"t": "Tres años después, medio triturado, se volvió a subastar… por veinticinco millones cuatrocientos mil dólares.",
     "img": ["banksy_madrid", "banksy_globo"], "marcas": [cifra("25,4 M$", 2.5)]},

    {"t": "Y el número uno…", "vid": ["sorpresa", "dolares"]},
    {"t": "Salvator Mundi, atribuido a Leonardo da Vinci. Cuatrocientos cincuenta millones de dólares en 2017. El cuadro más caro jamás vendido.",
     "rank": {"n": 1, "texto": "Salvator Mundi · 450 M$", "emoji": "🏆"}, "sfx": ding(0.4),
     "img": ["salvator"], "marcas": [cifra("450 M$", 3.5), emoji("🤯", 1.0)]},
    {"t": "Y lo más loco: iba a exponerse en el Louvre de Abu Dabi, pero nunca llegó. Lleva años sin verse en público, y muchos expertos dudan de que lo pintara él.",
     "img": ["louvre_ad", "salvator"]},

    {"t": "¿Tú cuál habrías comprado? Te leo en los comentarios.", "vid": ["sorpresa2", "contar"]},
    {"t": "Sígueme para más rankings en Shock Mental.", "vid": ["lluvia_dinero", "yates"]},
]}]
(R / "ranking07" / "escenas.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
print("ok", d["credito_fotos"])
