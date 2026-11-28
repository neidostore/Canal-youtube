"""Genera produccion/ranking09/escenas.json: los memes más famosos y quién hay detrás (Short).
Solo fotos libres de las personas/animales reales (Commons), nunca las imágenes de los memes."""
import copy, json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
base = json.loads((R / "ranking07" / "escenas.json").read_text(encoding="utf-8"))
cred = json.loads((R / "ranking09" / "creditos_commons.json").read_text(encoding="utf-8"))

d = {k: copy.deepcopy(base[k]) for k in ("tema", "voz", "estilo", "formato", "marca", "musica")}
d["titulo"] = "La perrita del meme que vale millones 🐕 Ranking"
d["ranking"] = {"titulo": "LOS MEMES MÁS FAMOSOS", "puestos": [5, 4, 3, 2, 1]}
d["videos"] = {"movil": 4232959, "facebook": 5201209, "ninos_youtube": 4961698, "concierto": 3941289, "ninos_baile": 8612634}
nombres = {"kabosu": "Asanagi", "kabosu2": "Asanagi", "kabosu_sentada": "Asanagi", "kabosu_estatua": "Fred Cherrygarden",
           "dogecoin": "Cyril Ernst", "grumpy": "Gage Skidmore", "grumpy2": "Gage Skidmore", "harold": "Eifert János",
           "laina": "Gage Skidmore", "laina_grumpy": "Gage Skidmore", "rick": "Wjack12", "rick2": "Andrew Hurley"}
d["fotos"] = {n: 0 for n in cred}
d["credito_fotos"] = {n: f"Foto: {nombres[n]} / {cred[n]['licencia']}" for n in cred}

ding = lambda v=0.25: {"nombre": "ding", "vol": v, "en": 0.1}
cifra = lambda t, en=2.0, color="#E53935": {"tipo": "texto", "texto": t, "pos": [0.5, 0.78], "tam": 60, "en": en, "fondo": color}
emoji = lambda e, en=0.3: {"tipo": "emoji", "emoji": e, "pos": [0.8, 0.4], "tam": 170, "en": en}

d["bloques"] = [{"nombre": "Ranking", "frases": [
    {"t": "Esta perrita inspiró una criptomoneda que llegó a valer más de ochenta mil millones de dólares.",
     "img": ["kabosu"], "marcas": [emoji("🤯"), cifra("80.000 M$", 2.5)]},
    {"t": "Los memes más famosos de internet… y quién hay detrás.", "vid": ["movil", "facebook"]},

    {"t": "Número cinco: Harold. Es András Arató, un ingeniero húngaro jubilado que posó para un banco de fotos.",
     "rank": {"n": 5, "texto": "Harold · Hungría", "emoji": "🙂"}, "sfx": ding(), "img": ["harold"]},

    {"t": "Número cuatro: la novia obsesiva. Laina Morris vendió su meme en 2021 por más de cuatrocientos mil dólares.",
     "rank": {"n": 4, "texto": "La novia obsesiva · 411.000 $", "emoji": "👀"}, "sfx": ding(),
     "img": ["laina", "laina_grumpy"], "marcas": [cifra("411.000 $", 3.0)]},

    {"t": "Número tres: el rickroll, la broma del enlace que acaba en esta canción de Rick Astley.",
     "rank": {"n": 3, "texto": "Rickroll · Rick Astley", "emoji": "🎤"}, "sfx": ding(), "img": ["rick", "rick2"]},
    {"t": "Gracias a ella, el vídeo pasó de mil millones de visitas.",
     "img": ["rick2"], "marcas": [cifra("+1.000 M", 1.5)]},

    {"t": "Número dos: Grumpy Cat. Su cara de enfado era real: tenía enanismo felino.",
     "rank": {"n": 2, "texto": "Grumpy Cat · 710.000 $", "emoji": "😾"}, "sfx": ding(), "img": ["grumpy", "grumpy2"]},
    {"t": "Y su dueña ganó un juicio de setecientos diez mil dólares a una marca de café.",
     "img": ["grumpy2", "laina_grumpy"], "marcas": [cifra("710.000 $", 2.0), emoji("☕", 1.0)]},

    {"t": "Y el número uno…", "img": ["kabosu2"]},
    {"t": "Doge. Es Kabosu, una perrita de Japón. Su foto inspiró el Dogecoin, y se vendió como NFT por unos cuatro millones de dólares.",
     "rank": {"n": 1, "texto": "Doge · Kabosu", "emoji": "🏆"}, "sfx": ding(0.4),
     "img": ["kabosu", "dogecoin"], "marcas": [cifra("4 M$", 4.5), emoji("🐕", 0.5)]},
    {"t": "Kabosu murió en 2024. Y en su ciudad, Sakura, tiene su propia estatua.",
     "img": ["kabosu_estatua", "kabosu_sentada"], "marcas": [emoji("🥹", 1.5)]},

    {"t": "¿Cuál es tu meme favorito? Te leo en los comentarios.", "vid": ["ninos_youtube", "movil"]},
    {"t": "Sígueme para más rankings en Shock Mental.", "img": ["kabosu_sentada"]},
]}]
(R / "ranking09" / "escenas.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
print("ok")
