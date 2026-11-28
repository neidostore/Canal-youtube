"""SHOCK MENTAL CEO · Director general de IA.

Gobierna los departamentos (el ciclo de director.py es su «día de trabajo»), vigila retrasos, cola, fallos y
oportunidades, registra sus decisiones y te informa a ti, el GERENTE GENERAL, por Telegram.
Límites (no puede, por código): gastar fuera de config.limites, publicar sin tu ✅, borrar contenido, cambiar
contraseñas ni permisos, ni cambiar la identidad del canal. Esas decisiones se registran como «requiere_gerente».
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from .nucleo import ajuste, config, decision, fila

ORGANIGRAMA = {
    "Dirección": ["CEO (director.py + ceo.py): planificación, coordinación de tareas, prioridades, costes, informes"],
    "Contenido": ["Investigador", "Verificador de datos", "Guionista de Shorts (+ títulos y posicionamiento)", "Guionista de vídeos largos"],
    "Producción audiovisual": ["Productor (montar.py)", "Thumbnail Director", "Voice Director", "Control de calidad / editor"],
    "Marketing y distribución": ["Responsable de YouTube (publicador)", "Responsable de TikTok", "Community Manager (en modo borrador)"],
    "Analítica": ["Analista (YouTube; TikTok cuando haya permiso de métricas) + crecimiento y monetización"],
}


def vigilar(con, cfg, avisar):
    """Revisión proactiva de cada ciclo: solo avisa cuando hay algo que decidir o celebrar."""
    ahora = datetime.now(timezone.utc)
    # 1) tareas atascadas (el cerebro no ha terminado algo en 8 h)
    atasc = con.execute("SELECT agente, COUNT(*) FROM tareas WHERE estado='en_curso' AND actualizada < ? GROUP BY agente",
                        ((ahora - timedelta(hours=8)).isoformat(),)).fetchall()
    if atasc and ajuste(con, "aviso_atasco") != ahora.date().isoformat():
        con.execute("UPDATE tareas SET estado='pendiente' WHERE estado='en_curso' AND actualizada < ?", ((ahora - timedelta(hours=8)).isoformat(),))
        decision(con, "operaciones", f"liberadas tareas atascadas: {dict(atasc)}", "más de 8 h en curso")
        ajuste(con, "aviso_atasco", ahora.date().isoformat())
    # 2) agente que falla de forma repetida
    for agente, n in con.execute("SELECT agente, COUNT(*) FROM tareas WHERE estado='fallida' AND actualizada >= ? GROUP BY agente",
                                 ((ahora - timedelta(days=2)).isoformat(),)):
        clave = f"aviso_fallo_{agente}"
        if n >= 2 and ajuste(con, clave) != ahora.date().isoformat():
            avisar(f"🧯 El agente «{agente}» ha fallado {n} veces en 48 h. Lo dejo en pausa hasta revisarlo; el resto sigue trabajando.")
            decision(con, "operaciones", f"agente {agente} con {n} fallos", "requiere revisión técnica", requiere_gerente=True)
            ajuste(con, clave, ahora.date().isoformat())
    # 3) cola: ¿hay contenido aprobado para los próximos días?
    listos = con.execute("SELECT COUNT(*) FROM videos WHERE estado IN ('revision','aprobado','programado')").fetchone()[0]
    necesarios = cfg["calendario"]["cola_minima_dias"] * (len(cfg["calendario"]["shorts"]))
    if listos < necesarios and ajuste(con, "aviso_cola") != ahora.date().isoformat():
        decision(con, "planificacion", f"cola baja: {listos} vídeos listos (objetivo {necesarios})", "se prioriza producción de Shorts")
        ajuste(con, "aviso_cola", ahora.date().isoformat())


def informe(con, cfg, tipo: str = "diario") -> str:
    dias = 1 if tipo == "diario" else 7
    desde = (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()
    q = lambda sql, *a: con.execute(sql, a).fetchone()[0]
    producidos = q("SELECT COUNT(*) FROM videos WHERE creado >= ?", desde)
    pendientes = q("SELECT COUNT(*) FROM videos WHERE estado='revision'")
    publicados = q("SELECT COUNT(*) FROM publicaciones WHERE estado IN ('publicado','en_borradores') AND actualizado >= ?", desde)
    fallos = q("SELECT COUNT(*) FROM tareas WHERE estado='fallida' AND actualizada >= ?", desde)
    bloq = q("SELECT COUNT(*) FROM videos WHERE estado='bloqueado' AND actualizado >= ?", desde)
    coste = q("SELECT COALESCE(SUM(euros),0) FROM costes WHERE fecha >= ?", desde)
    pubs = con.execute("SELECT plataforma, estado, COUNT(*) FROM publicaciones WHERE actualizado >= ? GROUP BY plataforma, estado",
                       (desde,)).fetchall()
    canal = con.execute("SELECT datos FROM canal ORDER BY fecha DESC LIMIT 1").fetchone()
    c = json.loads(canal[0]) if canal else {}
    L = [f"🏢 <b>Informe {tipo} del CEO</b>",
         f"🎬 Producidos: {producidos} · ⏳ esperando tu revisión: {pendientes} · 📤 publicados: {publicados}",
         f"⛔ Bloqueados por calidad: {bloq} · 🧯 tareas fallidas: {fallos} · 💶 coste: {coste:.2f} €"]
    if pubs:
        L.append("Plataformas: " + ", ".join(f"{p} {e} ×{n}" for p, e, n in pubs))
    if c:
        L.append(f"📈 Suscriptores: {c.get('suscriptores')} · Shorts 90 días: {c.get('vistas_shorts_90d')} · horas 12 meses ≈ {c.get('horas_12m')}")
    else:
        L.append("📈 Métricas: pendientes de conectar YouTube Analytics")
    if tipo == "semanal":
        obj = cfg["objetivos"]
        subs = c.get("suscriptores", obj["suscriptores_hoy"])
        L.append(f"🎯 Objetivo 200 suscriptores: {subs}/200 · quedan {(datetime.fromisoformat(obj['fecha_meta_90']) - datetime.now()).days} días")
        top = con.execute("SELECT v.titulo, json_extract(m.datos,'$.vistas') AS vistas FROM metricas m JOIN videos v ON v.youtube_id=m.youtube_id "
                          "WHERE m.fecha >= ? ORDER BY vistas DESC LIMIT 3", (desde[:10],)).fetchall()
        if top:
            L.append("🏆 Mejores: " + " · ".join(f"«{t}» ({n})" for t, n in top))
        dec = con.execute("SELECT decision FROM decisiones WHERE requiere_gerente=1 AND estado='pendiente'").fetchall()
        if dec:
            L.append("🙋 Decisiones que necesitan al gerente:\n• " + "\n• ".join(d[0] for d in dec))
        L.append("💡 Recomendación: " + recomendacion(con, c))
    return "\n".join(L)


def recomendacion(con, c: dict) -> str:
    lec = con.execute("SELECT texto FROM lecciones WHERE origen='analista' ORDER BY id DESC LIMIT 1").fetchone()
    if lec:
        return lec[0]
    if not c:
        return "Conectar YouTube Analytics para decidir con datos (no hay suficientes métricas todavía)."
    return "Mantener la mezcla actual: aún no hay datos suficientes para afirmar que un estilo funciona mejor."


def informes_programados(con, cfg, avisar):
    """Diario a partir de las 21:00 (hora de España); semanal el domingo."""
    local = datetime.now(ZoneInfo(cfg["general"]["zona"]))
    if local.hour < 21:
        return
    hoy = local.date().isoformat()
    if ajuste(con, "informe_diario") != hoy:
        avisar(informe(con, cfg, "diario"))
        ajuste(con, "informe_diario", hoy)
    if local.weekday() == 6 and ajuste(con, "informe_semanal") != hoy:
        avisar(informe(con, cfg, "semanal"))
        ajuste(con, "informe_semanal", hoy)
