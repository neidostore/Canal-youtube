import json
from pathlib import Path

R = Path(r"C:\Users\Neidostore\Desktop\Youtube\Canal-youtube\produccion")
base = json.loads((R / "shock06" / "escenas.json").read_text(encoding="utf-8"))
cred = json.loads((R / "shock07-prueba" / "creditos_commons.json").read_text(encoding="utf-8"))

def autor(n):
    a = cred[n]["autor"].split(" from ")[0].split("\n")[0].strip()
    return f"Foto: {a} · {cred[n]['licencia']}" if "Public domain" not in cred[n]["licencia"] else f"Foto: {a} · dominio público"

d = {k: base[k] for k in ("tema", "tarjetas", "intro", "musica", "estilo", "marco", "voz")}
d["titulo"] = "PRUEBA Dosis 7"
d["videos"] = {
    "r_shocked_woman": 8626657, "r_man_tv": 9883681,
    "microscopio": 4114797, "cientifica": 4121618, "adn1": 9837848, "adn2": 10661569, "adn3": 3191572,
    "lab": 4121354, "sangre": 4074364, "anciana": 4058254, "joven": 4832216, "reloj_arena": 6981614,
    "reloj_arena2": 6981615, "tiburon_agua": 5548358, "iceberg": 8318649, "hielo": 8016826,
    "medusa_azul": 2558530, "medusa_naranja": 2731905, 
}
d["videos_inicio"] = {"r_shocked_woman": 0.3, "r_man_tv": 3.5}
d["fotos"] = {n: 0 for n in cred}
d["credito_fotos"] = {n: autor(n) for n in cred}
emoji = lambda e: {"tipo": "emoji", "emoji": e, "pos": [0.86, 0.5], "tam": 200}
d["bloques"] = [
    {"nombre": "1 · Células de 80 años que vuelven a tener 20", "frases": [
        {"t": "Unos científicos han cogido células de la sangre de una persona de ochenta años… y las han convertido en células con una edad de menos de veinte.",
         "vid": ["sangre", "microscopio"], "kw": "menos de veinte", "marcas": [emoji("🧬")]},
        {"t": "No es ciencia ficción. Lo ha publicado hace unas semanas la Universidad de Bonn, en Alemania, en la revista científica Aging Cell.",
         "rotulo": {"arriba": "Universidad de Bonn · octubre de 2026", "texto": "Revista Aging Cell"}, "img": ["bonn_uni"]},
        {"t": "¿Y cómo se mide la edad de una célula? Con los llamados relojes epigenéticos: unas marcas diminutas en el ADN que se van acumulando según envejecemos.",
         "vid": ["adn2", "adn1"], "kw": "relojes epigenéticos"},
        {"t": "Al transformar esas células de la sangre en células madre del cerebro… el reloj fue hacia atrás. Sesenta años más jóvenes.",
         "vid": ["reloj_arena", "cientifica"], "kw": "sesenta años", "marcas": [emoji("⏪")]},
        {"t": "Y lo más curioso: no pasó de golpe. Fue tan lento que lo pudieron seguir durante más de cien días, para estudiar qué lo acelera y qué lo frena.",
         "vid": ["lab", "microscopio"], "kw": "más de cien días"},
        {"t": "Ojo: de momento es un experimento de laboratorio, no un tratamiento para personas. Pero podría ayudar a entender enfermedades como el alzhéimer.",
         "vid": ["anciana", "cientifica"], "kw": "alzhéimer"},
        {"t": "Y quédate hasta el final, porque hay un animal que hace algo parecido… con todo su cuerpo.",
         "vid": ["medusa_azul", "medusa_naranja"], "kw": "quédate hasta el final", "marcas": [emoji("👀")]},
    ]},
    {"nombre": "Intro", "intro": True},
    {"nombre": "2 · El tiburón de 400 años", "frases": [
        {"t": "Número dos.", "card": {"tipo": "numero", "n": 2, "tema": "Animales"}},
        {"t": "En las aguas heladas del Ártico vive un tiburón que podría haber nacido… hace casi cuatrocientos años.",
         "vid": ["hielo", "iceberg"], "kw": "cuatrocientos años"},
        {"t": "Es el tiburón de Groenlandia. Mide hasta seis metros y medio, y nada muy despacio, en aguas casi congeladas.",
         "rotulo": {"arriba": "Tiburón de Groenlandia", "texto": "Hasta 6,4 metros"}, "img": ["tiburon_okeanos"]},
        {"t": "En 2016, unos científicos calcularon su edad de una forma muy ingeniosa: midiendo el carbono del cristalino de sus ojos, que se forma antes de nacer.",
         "img": ["tiburon_perfil"], "kw": "cristalino de sus ojos", "marcas": [emoji("👁️")]},
        {"t": "El más viejo que estudiaron tenía entre doscientos setenta y unos quinientos años. Es el vertebrado más longevo que se conoce.",
         "vid": ["tiburon_agua", "hielo"], "kw": "el vertebrado más longevo"},
        {"t": "Y se lo toma con calma: no puede tener crías hasta que cumple unos ciento cincuenta años.",
         "img": ["tiburon_okeanos"], "kw": "ciento cincuenta años", "marcas": [emoji("🐢")]},
    ]},
    {"nombre": "3 · La medusa inmortal", "frases": [
        {"t": "Número tres.", "card": {"tipo": "numero", "n": 3, "tema": "Animales"}},
        {"t": "Esta medusa mide menos de medio centímetro… y puede hacer algo que ningún otro animal sabe hacer: volver a ser joven.",
         "rotulo": {"arriba": "Turritopsis dohrnii", "texto": "Menos de medio centímetro"}, "img": ["medusa_inmortal"]},
        {"t": "Cuando está herida, enferma, pasa hambre o se hace vieja, en vez de morir… vuelve a su fase de bebé, el pólipo. Y empieza su vida otra vez.",
         "img": ["medusa_kamo"], "kw": "vuelve a su fase de bebé", "marcas": [emoji("🔄")]},
        {"t": "Por eso la llaman la medusa inmortal. Aunque en la vida real, la mayoría acaba devorada por otros animales antes de poder hacerlo.",
         "vid": ["medusa_naranja", "medusa_azul"], "kw": "la medusa inmortal"},
        {"t": "Se descubrió en 1992 en Italia, casi por casualidad, y hoy los científicos la estudian para entender justo lo que vimos al principio: cómo rejuvenecer células.",
         "vid": ["medusa_azul", "microscopio"], "kw": "rejuvenecer células"},
    ]},
    {"nombre": "Cierre", "frases": [
        {"t": "¿Cuál te ha dejado con la boca abierta? Te leo en los comentarios.", "card": {"tipo": "final"}},
        {"t": "Y si quieres tu próxima dosis de asombro, suscríbete a Shock Mental.", "card": {"tipo": "final"}},
    ], "final": 1.0},
]
(R / "shock07-prueba" / "escenas.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
print("ok", d["credito_fotos"])
