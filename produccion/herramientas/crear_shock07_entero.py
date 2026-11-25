"""Genera produccion/shock07/escenas.json (Dosis de Asombro #7: cosas que desafían el tiempo) a partir de la prueba."""
import copy, json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
pr = json.loads((R / "shock07-prueba" / "escenas.json").read_text(encoding="utf-8"))
cred = json.loads((R / "shock07" / "creditos_commons.json").read_text(encoding="utf-8"))


def credito(n):
    c = cred[n]; a = c["autor"].split(" from ")[0].split("\n")[0].split(",")[0].strip()
    return f"Foto: {a} · dominio público" if "Public domain" in c["licencia"] else f"Foto: {a} · {c['licencia']}"


d = copy.deepcopy(pr)
d["titulo"] = "11 cosas que desafían al tiempo (la primera es de este mes)"
d["videos"].update({
    "desierto": 4066466, "desierto2": 3059062, "ballena_mar": 4332083, "ballenas": 5608046, "cerebro_rm": 6010766,
    "astronauta": 5299577, "palmera": 855683, "mujer_mayor": 7261143, "via_lactea": 857134, "telescopio": 5428315,
    "tarta": 5529616,
})
d["fotos"] = {n: 0 for n in cred}
d["credito_fotos"] = {n: credito(n) for n in cred}
emoji = lambda e, y=0.5: {"tipo": "emoji", "emoji": e, "pos": [0.86, y], "tam": 200}
num = lambda n, tema: {"t": f"Número {['', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve', 'diez', 'once'][n]}.",
                       "card": {"tipo": "numero", "n": n, "tema": tema}}

gancho, intro, tiburon, medusa, cierre = pr["bloques"]
for f in tiburon["frases"]:            # la tortuga tapaba «AÑOS»
    for m in f.get("marcas", []):
        if m.get("emoji") == "🐢":
            m["pos"] = [0.86, 0.78]

medusa = copy.deepcopy(medusa)
medusa["nombre"] = "11 · La medusa inmortal"
medusa["frases"][0] = num(11, "Animales")
medusa["frases"][1]["t"] = "Y el número once: el animal que te prometí al principio. Esta medusa mide menos de medio centímetro… y puede hacer algo que ningún otro animal sabe hacer: volver a ser joven."

bloques = [gancho, intro, tiburon,
    {"nombre": "3 · Matusalén, el árbol de casi 5.000 años", "frases": [
        num(3, "Plantas"),
        {"t": "En lo alto de unas montañas de California hay un pino que ya estaba vivo cuando se construían las pirámides de Egipto.",
         "img": ["pino_viejo"], "kw": "las pirámides de Egipto", "marcas": [emoji("🌲")]},
        {"t": "Le llaman Matusalén. Es un pino de Bristlecone, y se calcula que tiene unos cuatro mil ochocientos cincuenta años.",
         "rotulo": {"arriba": "Pino de Bristlecone · California", "texto": "Unos 4.850 años"}, "img": ["pino_matusalen"]},
        {"t": "Vive a casi tres mil metros de altura, en un terreno seco y con un viento helado que retuerce sus troncos.",
         "img": ["pino_tronco"], "kw": "tres mil metros"},
        {"t": "Y su ubicación exacta es un secreto: el Servicio Forestal de Estados Unidos no la revela, para que nadie lo dañe.",
         "vid": ["desierto", "desierto2"], "kw": "un secreto", "marcas": [emoji("🤫")]},
    ]},
    {"nombre": "4 · La ballena con un arpón del siglo XIX", "frases": [
        num(4, "Animales"),
        {"t": "En 2007, frente a la costa de Alaska, unos cazadores capturaron una ballena… y dentro de su cuerpo encontraron algo increíble.",
         "vid": ["ballena_mar", "ballenas"], "kw": "algo increíble"},
        {"t": "La punta de un arpón explosivo fabricado entre 1879 y 1885. Llevaba más de cien años clavada en ella.",
         "img": ["ballena"], "kw": "entre 1879 y 1885", "marcas": [emoji("😱")]},
        {"t": "Era una ballena de Groenlandia, y calcularon que tenía entre ciento quince y ciento treinta años.",
         "rotulo": {"arriba": "Ballena de Groenlandia", "texto": "Entre 115 y 130 años"}, "img": ["ballena2"]},
        {"t": "Y no es la más vieja: se ha estimado que alguna llegó a los doscientos once años. Podrían ser los mamíferos más longevos del planeta.",
         "vid": ["ballenas", "ballena_mar"], "kw": "doscientos once años"},
    ]},
    {"nombre": "5 · Hay partes de ti tan viejas como tú", "frases": [
        num(5, "Cuerpo humano"),
        {"t": "Seguro que has oído que tu cuerpo se renueva entero cada siete años. Pues no es verdad.",
         "vid": ["mujer_mayor", "joven"], "kw": "no es verdad", "marcas": [emoji("❌")]},
        {"t": "Es cierto que muchas células cambian muy rápido. Los glóbulos rojos de tu sangre, por ejemplo, viven unos cuatro meses.",
         "vid": ["sangre", "microscopio"], "kw": "unos cuatro meses"},
        {"t": "Pero en 2005, unos científicos de Suecia calcularon la edad de células humanas usando el carbono que dejaron en el aire las pruebas nucleares de los años cincuenta y sesenta.",
         "vid": ["lab", "cientifica"], "kw": "pruebas nucleares"},
        {"t": "Y descubrieron que las neuronas de la corteza de tu cerebro tienen exactamente tu misma edad. Te acompañan desde que naciste.",
         "vid": ["cerebro_rm", "adn1"], "kw": "tu misma edad", "marcas": [emoji("🧠")]},
    ]},
    {"nombre": "6 · Los astronautas envejecen más despacio", "frases": [
        num(6, "Espacio"),
        {"t": "Los astronautas envejecen un poquito más despacio que nosotros. Y no es por la comida de la nave.",
         "vid": ["astronauta", "via_lactea"], "kw": "más despacio"},
        {"t": "Es la relatividad de Einstein: cuanto más rápido te mueves, más despacio pasa tu tiempo. Y la Estación Espacial va a unos veintiocho mil kilómetros por hora.",
         "img": ["scott_iss"], "kw": "veintiocho mil kilómetros por hora", "marcas": [emoji("🚀")]},
        {"t": "Después de seis meses allí arriba, un astronauta ha envejecido unas cinco milésimas de segundo menos que tú.",
         "vid": ["astronauta"], "kw": "cinco milésimas de segundo", "marcas": [emoji("⏱️")]},
        {"t": "La NASA lo estudió con dos gemelos: Scott Kelly pasó trescientos cuarenta días en el espacio, mientras su hermano Mark se quedaba en la Tierra.",
         "rotulo": {"arriba": "NASA · 2015-2016", "texto": "Scott y Mark Kelly"}, "img": ["gemelos_kelly"]},
        {"t": "Allí arriba, los extremos de los cromosomas de Scott, que se acortan al envejecer, se alargaron. Pero a los pocos meses de volver, todo regresó a la normalidad.",
         "img": ["scott_iss"], "kw": "se alargaron"},
    ]},
    {"nombre": "7 · La rata topo desnuda", "frases": [
        num(7, "Animales"),
        {"t": "Este animal tan raro tiene un superpoder: casi no envejece.",
         "img": ["rata_topo"], "kw": "casi no envejece", "marcas": [emoji("😬")]},
        {"t": "Es la rata topo desnuda. Vive bajo tierra en el este de África, pesa unos treinta gramos… y puede vivir más de treinta y siete años.",
         "rotulo": {"arriba": "Rata topo desnuda", "texto": "Más de 37 años"}, "img": ["rata_topo2"]},
        {"t": "Lo más raro es que su riesgo de morir no aumenta al hacerse mayor, como nos pasa a todos los demás. Y además, casi nunca tiene cáncer.",
         "img": ["rata_topo"], "kw": "casi nunca tiene cáncer"},
    ]},
    {"nombre": "8 · La palmera de una semilla de 2.000 años", "frases": [
        num(8, "Plantas"),
        {"t": "En los años sesenta, en las ruinas de Masada, en Israel, encontraron unas semillas de dátil guardadas en una vasija.",
         "img": ["masada"], "kw": "semillas de dátil"},
        {"t": "Tenían unos dos mil años. Y en 2005, una científica decidió plantarlas… a ver qué pasaba.",
         "vid": ["palmera", "desierto2"], "kw": "dos mil años", "marcas": [emoji("🌱")]},
        {"t": "Una germinó. La llamaron Matusalén, como el pino de antes, y hoy mide más de tres metros.",
         "rotulo": {"arriba": "Israel · Kibutz Ketura", "texto": "La palmera Matusalén"}, "img": ["palmera_cartel"]},
        {"t": "Y en 2021, con su polen, otra palmera resucitada dio dátiles: de una variedad que llevaba siglos desaparecida.",
         "img": ["palmera_matusalen"], "kw": "siglos desaparecida", "marcas": [emoji("🌴")]},
    ]},
    {"nombre": "9 · Jeanne Calment, 122 años", "frases": [
        num(9, "Historia"),
        {"t": "La persona más longeva de la que hay pruebas es una francesa, Jeanne Calment. Vivió ciento veintidós años y ciento sesenta y cuatro días.",
         "rotulo": {"arriba": "Arles, Francia", "texto": "122 años y 164 días"}, "img": ["arles"]},
        {"t": "Nació en 1875 y murió en 1997. Cuando nació, todavía no se había inventado la bombilla.",
         "vid": ["tarta", "mujer_mayor"], "kw": "la bombilla", "marcas": [emoji("💡")]},
        {"t": "Su edad se comprobó con catorce censos en los que aparecía desde que tenía un año.",
         "vid": ["mujer_mayor"], "kw": "catorce censos"},
        {"t": "En 2018, unos investigadores rusos dijeron que en realidad era su hija. Pero la mayoría de los expertos rechazan esa teoría.",
         "img": ["arles"], "kw": "la mayoría de los expertos"},
    ]},
    {"nombre": "10 · Mirar el cielo es mirar al pasado", "frases": [
        num(10, "Espacio"),
        {"t": "Esa mancha que se ve en el cielo en las noches muy oscuras… es Andrómeda. Otra galaxia.",
         "img": ["andromeda"], "kw": "Andrómeda"},
        {"t": "Está a unos dos millones y medio de años luz. O sea, su luz ha tardado dos millones y medio de años en llegar a tus ojos.",
         "vid": ["via_lactea"], "kw": "dos millones y medio de años"},
        {"t": "Así que cuando la miras, no la ves como es hoy: la ves como era cuando en la Tierra todavía no existía nuestra especie.",
         "vid": ["telescopio", "via_lactea"], "kw": "no existía nuestra especie", "marcas": [emoji("🤯")]},
    ]},
    medusa, cierre]
d["bloques"] = bloques
(R / "shock07" / "escenas.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
print("ok", len(bloques), "bloques")
