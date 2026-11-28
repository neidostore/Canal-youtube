"""Shock Mental Autopilot · órdenes

  python -m autopilot ciclo                      sincroniza con el bot, planifica, produce, revisa y envía a Telegram
  python -m autopilot cerebro siguiente          (lo usa la tarea programada de Claude) siguiente tarea de pensar, en JSON
  python -m autopilot cerebro entregar ID F.json entrega el resultado de esa tarea
  python -m autopilot idea "tema" [--formato short|largo] [--tipo ranking]   añade una idea a mano
  python -m autopilot panel                      estado del canal, la cola y los objetivos
  python -m autopilot probar GUION.json [--id X] produce un guion sin pasar por la cola (para pruebas)
  python -m autopilot enviar ID                  manda a Telegram un vídeo que ya pasó la calidad
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:  # certificados de Windows (el antivirus inspecciona las conexiones)
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

from . import calidad, cerebro, director, guion as G
from .nucleo import REPO, ahora, config, db, fila, js
from .panel import panel


def main():
    p = argparse.ArgumentParser(prog="autopilot")
    s = p.add_subparsers(dest="orden", required=True)
    s.add_parser("ciclo")
    c = s.add_parser("cerebro"); c.add_argument("accion", choices=["siguiente", "entregar", "liberar"])
    c.add_argument("tarea", nargs="?", type=int); c.add_argument("archivo", nargs="?")
    i = s.add_parser("idea"); i.add_argument("tema"); i.add_argument("--formato", default="short")
    i.add_argument("--tipo", default="ranking"); i.add_argument("--categoria")
    s.add_parser("panel")
    pr = s.add_parser("probar"); pr.add_argument("guion"); pr.add_argument("--id")
    e = s.add_parser("enviar"); e.add_argument("id")
    a = p.parse_args()

    with db() as con:
        if a.orden == "ciclo":
            print(json.dumps({"tareas_pendientes": director.ciclo(con)}, ensure_ascii=False))
        elif a.orden == "cerebro":
            if a.accion == "siguiente":
                t = cerebro.siguiente(con)
                print(json.dumps(t or {"nada": "no hay tareas de pensar pendientes"}, ensure_ascii=False, indent=1, default=str))
            elif a.accion == "entregar":
                res = json.loads(Path(a.archivo).read_text(encoding="utf-8-sig"))
                print(cerebro.entregar(con, a.tarea, res))
            else:   # liberar tareas que se quedaron «en curso» (la sesión se cortó)
                n = con.execute("UPDATE tareas SET estado='pendiente' WHERE estado='en_curso'").rowcount
                print(f"{n} tareas liberadas")
        elif a.orden == "idea":
            con.execute("INSERT INTO ideas (tema, formato, tipo, categoria, origen, puntuacion, creada) VALUES (?,?,?,?,?,?,?)",
                        (a.tema, a.formato, a.tipo, a.categoria, "dueño", 90, ahora()))
            print("idea guardada")
        elif a.orden == "panel":
            print(panel(con))
        elif a.orden == "probar":
            g = json.loads(Path(a.guion).read_text(encoding="utf-8-sig"))
            cfg = config()
            err = G.validar(g, cfg)
            if err:
                sys.exit("Guion no válido:\n- " + "\n- ".join(err))
            vid = a.id or "prueba-" + G.slug(g["tema"])
            con.execute("INSERT OR REPLACE INTO videos (id, formato, tipo, categoria, tema, estado, version, guion, titulo, "
                        "descripcion, fuentes, creado, actualizado) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (vid, g["formato"], g["tipo"], g.get("categoria"), g["tema"], "produccion", 1, js(g), g["titulo"],
                         g["descripcion"], js(g["fuentes"]), ahora(), ahora()))
            v = fila(con.execute("SELECT * FROM videos WHERE id=?", (vid,)).fetchone())
            director.producir(con, cfg, v, enviar=False)
            v = fila(con.execute("SELECT * FROM videos WHERE id=?", (vid,)).fetchone())
            print(json.dumps({"id": vid, "estado": v["estado"], "calidad": v["calidad"]}, ensure_ascii=False, indent=1))
        elif a.orden == "enviar":
            director.enviar_revision(con, config(), a.id)


if __name__ == "__main__":
    main()
