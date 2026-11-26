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

d["bloques"] = [gancho, intro, que_era, filisteos, cierre]
dest = R / ("shock08-prueba" if prueba else "shock08")
if prueba:
    shutil.copytree(R / "shock08" / "fotos", dest / "fotos", dirs_exist_ok=True)
    shutil.copy(R / "shock08" / "creditos_commons.json", dest / "creditos_commons.json")
(dest / "escenas.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
print("ok", dest, len(d["bloques"]), "bloques")
