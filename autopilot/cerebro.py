"""Interfaz del «cerebro» (modelo de IA) para los agentes que piensan: investigador, verificador, guionistas y corrector.

Proveedor elegido: «claude_programado». Una tarea programada de Claude en el PC ejecuta
    python -m autopilot cerebro siguiente      → recibe instrucciones + contexto + formato de respuesta
    python -m autopilot cerebro entregar ID f  → entrega el JSON; aquí se valida y se avanza el flujo
Así el código no depende de ninguna API de pago. Si más adelante se usa una API (Gemini o Claude),
solo hay que implementar `resolver_con_api` y el flujo no cambia.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import guion as G
from .nucleo import ahora, cerrar_tarea, config, estado_video, fila, js, lecciones, log, nueva_tarea

AGENTES = Path(__file__).with_name("agentes")
ORDEN = ["corrector", "verificador", "guionista_short", "guionista_largo", "investigador"]   # prioridad


def contexto(con) -> dict:
    hechos = [fila(r) for r in con.execute(
        "SELECT id, formato, tipo, categoria, tema, titulo, estado FROM videos ORDER BY creado DESC LIMIT 60")]
    ideas = [fila(r) for r in con.execute("SELECT tema, categoria, estado FROM ideas ORDER BY id DESC LIMIT 80")]
    metr = [fila(r) for r in con.execute(
        "SELECT v.titulo, v.formato, m.datos FROM metricas m JOIN videos v ON v.youtube_id = m.youtube_id "
        "ORDER BY m.fecha DESC LIMIT 30")]
    return {"lecciones": lecciones(con), "videos_recientes": hechos, "ideas_existentes": ideas, "metricas_recientes": metr,
            "titulos_publicados_antes_del_autopilot": TITULOS_PREVIOS}


TITULOS_PREVIOS = [
    "¿Han encontrado el Arca de Noé en Turquía?", "Cleopatra vivió más cerca del iPhone que de las pirámides",
    "Coches de policía más locos del mundo", "Los tiburones son más antiguos que los árboles", "¿Cuál es el animal más rápido del mundo?",
    "El animal más mortal del mundo", "El sonido más fuerte de la historia", "Objetos que NO deberían existir",
    "GTA 6 rompió TODOS los récords", "Pagó 6 millones por un plátano… y se lo comió", "El vídeo más visto de YouTube (no es Despacito)",
    "La perrita del meme que vale millones", "Células de 80 años que vuelven a tener 20", "El Arca de la Alianza", "En 1518 bailaron hasta caer",
]


def siguiente(con) -> dict | None:
    for agente in ORDEN:
        t = con.execute("SELECT * FROM tareas WHERE agente=? AND estado='pendiente' ORDER BY id LIMIT 1", (agente,)).fetchone()
        if t:
            t = fila(t)
            con.execute("UPDATE tareas SET estado='en_curso', actualizada=? WHERE id=?", (ahora(), t["id"]))
            v = fila(con.execute("SELECT * FROM videos WHERE id=?", (t["video_id"],)).fetchone()) if t["video_id"] else None
            idea = fila(con.execute("SELECT * FROM ideas WHERE id=?", (t["idea_id"],)).fetchone()) if t["idea_id"] else None
            return {"tarea_id": t["id"], "agente": agente,
                    "instrucciones": (AGENTES / f"{agente}.md").read_text(encoding="utf-8"),
                    "identidad": (AGENTES / "identidad.md").read_text(encoding="utf-8"),
                    "datos": t["datos"], "video": v, "idea": idea, "contexto": contexto(con)}
    return None


def entregar(con, tarea_id: int, resultado: dict) -> str:
    t = fila(con.execute("SELECT * FROM tareas WHERE id=?", (tarea_id,)).fetchone())
    if not t or t["estado"] not in ("en_curso", "pendiente"):
        raise ValueError(f"la tarea {tarea_id} no está abierta")
    cfg = config()
    a = t["agente"]
    if a == "investigador":
        n = 0
        for i in resultado.get("ideas", []):
            p = i.get("puntos", {})
            nota = (0.4 * p.get("interes", 5) + 0.25 * p.get("originalidad", 5) + 0.2 * p.get("facilidad", 5)
                    + 0.15 * (10 - p.get("riesgo_desinformacion", 5))) * 10
            if p.get("riesgo_desinformacion", 0) >= 7:
                continue   # veto: tema con alto riesgo de desinformación
            con.execute("INSERT INTO ideas (tema, formato, tipo, categoria, origen, notas, puntos, puntuacion, creada) "
                        "VALUES (?,?,?,?,?,?,?,?,?)", (i["tema"], i.get("formato", "short"), i.get("tipo", "ranking"),
                                                     i.get("categoria"), "investigador", i.get("notas"), js(p), round(nota, 1), ahora()))
            n += 1
        cerrar_tarea(con, tarea_id, {"ideas": n})
        log(con, f"{n} ideas nuevas", agente=a)
        return f"{n} ideas guardadas"

    v = fila(con.execute("SELECT * FROM videos WHERE id=?", (t["video_id"],)).fetchone())
    if a in ("guionista_short", "guionista_largo", "corrector"):
        g = resultado
        errores = G.validar(g, cfg)
        if errores:
            con.execute("UPDATE tareas SET datos=? WHERE id=?", (js({**(t["datos"] or {}), "errores_formato": errores}), tarea_id))
            if cerrar_tarea(con, tarea_id, error="; ".join(errores)) == "fallida":
                estado_video(con, v["id"], "bloqueado")
                log(con, "guion inválido tras varios intentos: bloqueado", agente=a, nivel="error", video_id=v["id"])
            return "RECHAZADO por formato: " + "; ".join(errores)
        estado_video(con, v["id"], "verificacion", guion=g, titulo=g["titulo"], descripcion=g["descripcion"],
                     comentario=g.get("comentario"), etiquetas=g.get("etiquetas", []), tipo=g["tipo"],
                     categoria=g.get("categoria"), fuentes=g["fuentes"])
        cerrar_tarea(con, tarea_id, {"titulo": g["titulo"]})
        nueva_tarea(con, "verificador", video_id=v["id"])
        log(con, f"guion listo: {g['titulo']}", agente=a, video_id=v["id"])
        return "guion aceptado; pasa a verificación"

    if a == "verificador":
        datos = resultado.get("datos", [])
        if not datos:
            raise ValueError("el verificador debe devolver la lista de datos comprobados")
        malos = [d for d in datos if d.get("estado") != "verificado" or not d.get("fuentes")]
        g = v["guion"]
        g["verificacion"] = resultado
        cerrar_tarea(con, tarea_id, {"verificados": len(datos) - len(malos), "dudosos": len(malos)})
        if malos:
            estado_video(con, v["id"], "guion", guion=g)
            nueva_tarea(con, "corrector", video_id=v["id"], datos={
                "instrucciones": [f"Dato no verificado: «{d.get('dato')}» — {d.get('nota', '')}. Corrígelo con la cifra "
                                  f"correcta o elimínalo." for d in malos], "origen": "verificador"})
            log(con, f"{len(malos)} dato(s) sin verificar → corrector", agente=a, video_id=v["id"])
            return f"{len(malos)} datos dudosos: vuelve al guionista"
        estado_video(con, v["id"], "produccion", guion=g)
        log(con, f"{len(datos)} datos verificados", agente=a, video_id=v["id"])
        return "todo verificado; pasa a producción"
    raise ValueError(f"agente desconocido {a}")


def resolver_con_api(tarea: dict) -> dict:   # interfaz preparada para Gemini / Claude API
    raise NotImplementedError("Proveedor de API no configurado. El cerebro actual es la tarea programada de Claude.")
