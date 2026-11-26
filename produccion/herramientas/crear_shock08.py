"""Dosis de Asombro #8 (Arca de la Alianza). `python crear_shock08.py prueba` → shock08-prueba (gancho + 2 bloques)."""
import json, shutil, sys
from pathlib import Path

R = Path(__file__).resolve().parents[1]
base = json.loads((R / "shock07" / "escenas.json").read_text(encoding="utf-8"))
cred = json.loads((R / "shock08" / "creditos_commons.json").read_text(encoding="utf-8"))
prueba = len(sys.argv) > 1 and sys.argv[1] == "prueba"


def credito(n):
    c = cred[n]; a = c["autor"].split(" from ")[0].split("\n")[0].split(",")[0].strip()
    if "Public domain" in c["licencia"]:
        return f"{a} · dominio público" if a in ("James Tissot", "Nicolas Poussin", "Erastus Salisbury Field") else f"Foto: {a} · dominio público"
    return f"Foto: {a} · {c['licencia']}"


d = {k: base[k] for k in base if k not in ("bloques", "videos", "fotos", "credito_fotos", "titulo")}
d["titulo"] = "PRUEBA Dosis 8" if prueba else "El Arca de la Alianza"
d["videos"] = {
    "r_shocked_woman": 8626657, "r_man_tv": 9883681,
    "vela": 3561988, "dunas": 855673, "desierto": 3018500, "fuego": 2908575, "fuego2": 4108548,
    "biblia": 3987756, "biblia2": 5199729, "rayo": 2657691, "tormenta": 3052162, "tormenta2": 856429,
    "rayo_color": 4073979, "ruinas": 3015501, "petra": 4253642, "bandera_etiopia": 3845346,
}
d["fotos"] = {n: 0 for n in cred}
d["credito_fotos"] = {n: credito(n) for n in cred}
d["credito_fotos"].update({"jeremias": "Rembrandt · dominio público", "jerusalen_arde": "Círculo de Juan de la Corte · dominio público",
                           "dagon": "Battista Franco · The Met (CC0)"})
emoji = lambda e, y=0.5: {"tipo": "emoji", "emoji": e, "pos": [0.86, y], "tam": 200}
num = lambda n, tema: {"t": f"Número {['', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho'][n]}.",
                       "card": {"tipo": "numero", "n": n, "tema": tema}}

gancho = {"nombre": "El guardián del Arca", "frases": [
    {"t": "En una pequeña capilla de Etiopía vive un monje que no puede salir nunca de allí. Nunca. Hasta el día de su muerte.",
     "img": ["capilla"], "kw": "no puede salir nunca", "marcas": [emoji("🔒")]},
    {"t": "Su única misión es vigilar un objeto que, según dicen, solo él puede ver. Ni el patriarca de su iglesia, ni un presidente, ni ningún científico.",
     "img": ["monje2"], "kw": "solo él puede ver"},
    {"t": "Ese objeto sería… el Arca de la Alianza. El tesoro más buscado de la Biblia, desaparecido hace unos dos mil quinientos años.",
     "img": ["arca_jordan", "arca_replica2"], "kw": "el Arca de la Alianza", "marcas": [emoji("😱")]},
    {"t": "Hoy te cuento las pistas reales de dónde podría estar. Y al final volvemos a esa capilla.",
     "vid": ["vela", "desierto"], "kw": "las pistas reales", "marcas": [emoji("👀")]},
]}
intro = {"nombre": "Intro", "intro": True}
que_era = {"nombre": "1 · Qué era el Arca", "frases": [
    num(1, "La Biblia"),
    {"t": "Según la Biblia, era un cofre de madera de acacia cubierto de oro, de algo más de un metro de largo, con dos querubines de oro en la tapa.",
     "rotulo": {"arriba": "Éxodo 25", "texto": "Madera y oro · algo más de 1 metro"}, "img": ["arca_replica2"]},
    {"t": "Dentro guardaba las tablas de piedra con los diez mandamientos.",
     "vid": ["biblia", "biblia2"], "kw": "los diez mandamientos"},
    {"t": "Se transportaba con dos varas, porque no se podía tocar.",
     "img": ["arca_jordan"], "kw": "no se podía tocar", "marcas": [emoji("🚫")]},
    {"t": "Y la Biblia cuenta que un hombre llamado Uzá la tocó para que no se cayera… y murió en el acto.",
     "vid": ["rayo", "tormenta"], "kw": "murió en el acto", "marcas": [emoji("⚡")]},
]}
filisteos = {"nombre": "2 · Los filisteos la robaron", "frases": [
    num(2, "La Biblia"),
    {"t": "Los israelitas la llevaban a la guerra. Y en una batalla la perdieron: los filisteos se la llevaron como trofeo y la pusieron en el templo de su dios, Dagón.",
     "img": ["dagon"], "kw": "su dios, Dagón"},
    {"t": "A la mañana siguiente, la estatua de Dagón estaba tirada en el suelo, boca abajo, delante del Arca. La levantaron… y al día siguiente apareció otra vez en el suelo, rota.",
     "img": ["dagon"], "kw": "otra vez en el suelo", "marcas": [emoji("😨")]},
    {"t": "Después llegaron las plagas.",
     "rotulo": {"arriba": "Nicolas Poussin · 1630", "texto": "La peste de Asdod"}, "img": ["ashdod"]},
    {"t": "A los siete meses, los filisteos la devolvieron en un carro tirado por vacas, sin nadie que lo guiara.",
     "img": ["carro_vacas"], "kw": "sin nadie que lo guiara", "marcas": [emoji("🐄")]},
]}
cierre = {"nombre": "Cierre", "frases": [
    {"t": "¿Tú qué crees: está en Etiopía, bajo Jerusalén… o ya no existe? Te leo en los comentarios.", "card": {"tipo": "final"}},
    {"t": "Y si te gustan los misterios de la Biblia, suscríbete a Shock Mental: el próximo es Sodoma y Gomorra.", "card": {"tipo": "final"}},
], "final": 1.0}

excavado = {"nombre": "3 · El lugar que han excavado", "frases": [
    num(3, "Arqueología"),
    {"t": "Tras volver, según la Biblia, el Arca pasó unos veinte años en un pueblo llamado Kiriath-Jearim, cerca de Jerusalén.",
     "img": ["kiryat"], "kw": "unos veinte años"},
    {"t": "Y ese lugar existe. En 2017, arqueólogos de la Universidad de Tel Aviv excavaron allí y encontraron una enorme plataforma de unos ciento cincuenta metros de largo, construida hacia el siglo octavo antes de Cristo.",
     "rotulo": {"arriba": "Kiriath-Jearim · 2017", "texto": "Plataforma de unos 150 metros"}, "img": ["kiryat"]},
    {"t": "El arqueólogo Israel Finkelstein cree que se levantó como santuario para recordar la historia del Arca.",
     "vid": ["ruinas", "desierto"], "kw": "santuario"},
    {"t": "Ojo: él duda de que el Arca existiera. Pero la historia era tan importante que le construyeron un monumento.",
     "img": ["arca_replica"], "kw": "un monumento", "marcas": [emoji("🏛️")]},
]}
desaparece = {"nombre": "4 · Desaparece sin dejar rastro", "frases": [
    num(4, "Historia"),
    {"t": "Después, el rey Salomón la colocó en el Templo de Jerusalén. Y la última vez que la Biblia la menciona es en tiempos del rey Josías, hacia el año seiscientos veinte antes de Cristo.",
     "img": ["monte_templo"], "kw": "la última vez"},
    {"t": "En el año 587 antes de Cristo, los babilonios arrasaron Jerusalén y saquearon el Templo.",
     "rotulo": {"arriba": "Jerusalén · 587 a. C.", "texto": "Los babilonios arrasan la ciudad"}, "img": ["jerusalen_arde"]},
    {"t": "La Biblia hace una lista de lo que se llevaron: objetos de oro, de plata, de bronce…",
     "img": ["ishtar"], "kw": "de oro, de plata, de bronce"},
    {"t": "Pero el Arca no aparece en esa lista. Simplemente, desaparece.",
     "vid": ["fuego", "fuego2"], "kw": "desaparece", "marcas": [emoji("❓")]},
]}
egipto = {"nombre": "5 · ¿Se la llevó Egipto?", "frases": [
    num(5, "Pista 1"),
    {"t": "Primera pista. Unos trescientos años antes, el faraón Sisac atacó Jerusalén y, según la Biblia, se llevó los tesoros del Templo.",
     "rotulo": {"arriba": "Templo de Karnak · Egipto", "texto": "La puerta del faraón Sisac"}, "img": ["bubastis"]},
    {"t": "Esa es la teoría de una película muy famosa: En busca del arca perdida, de Indiana Jones, donde aparece enterrada en la ciudad egipcia de Tanis.",
     "img": ["tanis"], "kw": "Indiana Jones", "marcas": [emoji("🎬")]},
    {"t": "El problema: la Biblia sigue hablando del Arca siglos después de Sisac.",
     "vid": ["dunas", "desierto"], "kw": "siglos después"},
]}
escondida = {"nombre": "6 · ¿En una cueva o bajo el Templo?", "frases": [
    num(6, "Pistas 2 y 3"),
    {"t": "Segunda pista. Un libro antiguo, el segundo de los Macabeos, cuenta que el profeta Jeremías la escondió en una cueva del monte Nebo, en la actual Jordania, antes de que llegaran los babilonios.",
     "img": ["jeremias", "nebo"], "kw": "monte Nebo"},
    {"t": "Pero se escribió unos cuatrocientos años después.",
     "img": ["nebo_vista"], "kw": "cuatrocientos años después"},
    {"t": "Tercera pista. Una tradición judía dice que nunca salió de Jerusalén: que la escondieron en túneles bajo el Monte del Templo.",
     "img": ["tunel", "tunel2"], "kw": "túneles", "marcas": [emoji("🕳️")]},
    {"t": "Y ahí nadie puede excavar: es uno de los lugares más sagrados y vigilados del planeta.",
     "img": ["monte_templo"], "kw": "nadie puede excavar", "marcas": [emoji("🚫")]},
]}
lemba = {"nombre": "7 · El tambor de los lemba", "frases": [
    num(7, "Pista 4"),
    {"t": "Cuarta pista, y la más sorprendente. En Zimbabue y Sudáfrica viven los lemba, un pueblo que siempre ha dicho que sus antepasados eran judíos.",
     "rotulo": {"arriba": "Zimbabue y Sudáfrica", "texto": "El pueblo lemba"}, "img": ["lemba"]},
    {"t": "Y los análisis genéticos han encontrado en ellos un origen en Oriente Próximo.",
     "img": ["lemba2"], "kw": "Oriente Próximo", "marcas": [emoji("🧬")]},
    {"t": "Su tradición cuenta que guardaban un objeto sagrado hecho con restos del Arca: un tambor llamado ngoma lungundu.",
     "vid": ["vela", "fuego"], "kw": "ngoma lungundu", "marcas": [emoji("🥁")]},
    {"t": "En 2007, el investigador Tudor Parfitt encontró ese tambor olvidado en el almacén de un museo de Harare. Las pruebas de carbono lo datan hacia el año 1350.",
     "vid": ["biblia2", "vela"], "kw": "hacia el año 1350"},
    {"t": "No es el Arca… pero podría ser una réplica de una réplica.",
     "img": ["arca_replica2"], "kw": "una réplica de una réplica", "marcas": [emoji("🤔")]},
]}
axum = {"nombre": "8 · Axum", "frases": [
    num(8, "Etiopía"),
    {"t": "Y volvemos a Etiopía. Un libro sagrado etíope cuenta que Menelik, hijo del rey Salomón y la reina de Saba, se llevó el Arca de Jerusalén a Etiopía.",
     "img": ["saba", "menelik_arca"], "kw": "la reina de Saba"},
    {"t": "Hoy, según la Iglesia ortodoxa etíope, está en la Capilla de la Tabla, en la ciudad de Axum.",
     "rotulo": {"arriba": "Axum · Etiopía", "texto": "La Capilla de la Tabla"}, "img": ["capilla"]},
    {"t": "Su guardián es un monje elegido de por vida por el anterior antes de morir. No puede salir del recinto. Y es el único que la puede ver.",
     "img": ["monje2", "iglesia_axum"], "kw": "el único que la puede ver", "marcas": [emoji("👁️")]},
    {"t": "Por eso nadie ha podido comprobarlo: ni medirla, ni fecharla, ni compararla con lo que dice la Biblia. Muchos historiadores lo dudan.",
     "img": ["obelisco", "capilla"], "kw": "Muchos historiadores lo dudan"},
    {"t": "Pero cada iglesia de Etiopía guarda una copia de las tablas, el tabot. Y una vez al año, en la fiesta de Timkat, salen en procesión, cubiertas con telas, ante miles de personas.",
     "img": ["timkat", "timkat2"], "kw": "Timkat", "marcas": [emoji("🙏")]},
]}

d["bloques"] = [gancho, intro, que_era, filisteos, cierre] if prueba else \
    [gancho, intro, que_era, filisteos, excavado, desaparece, egipto, escondida, lemba, axum, cierre]
dest = R / ("shock08-prueba" if prueba else "shock08")
if prueba:
    shutil.copytree(R / "shock08" / "fotos", dest / "fotos", dirs_exist_ok=True)
    shutil.copy(R / "shock08" / "creditos_commons.json", dest / "creditos_commons.json")
(dest / "escenas.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
print("ok", dest, len(d["bloques"]), "bloques")
