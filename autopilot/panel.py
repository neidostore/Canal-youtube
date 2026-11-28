"""Panel: progreso hacia los objetivos y la monetización, cola, costes y alertas.
Las métricas del canal llegan del Agente 10 (analista.py) cuando YouTube Analytics esté conectado."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

from .nucleo import config, fila

# Requisitos oficiales (leídos el 28-nov-2026; support.google.com/youtube/answer/72851, 13429240, 12843009)
YPP = {
    "ampliado": {"subs": 500, "horas": 3000, "shorts_90d": 3_000_000, "subidas_90d": 3},
    "completo_hasta_ene_2027": {"subs": 1000, "horas": 4000, "shorts_90d": 10_000_000},
    "completo_desde_feb_2027": {"subs": 1000, "horas": 8000, "shorts_90d": 20_000_000},
}


def _pct(a, b):
    return f"{min(100, 100 * (a or 0) / b):.1f} %"


def datos_canal(con) -> dict:
    r = con.execute("SELECT datos FROM canal ORDER BY fecha DESC LIMIT 1").fetchone()
    return json.loads(r[0]) if r else {}


def panel(con, html: bool = False) -> str:
    cfg = config()
    obj = cfg["objetivos"]
    c = datos_canal(con)
    subs = c.get("suscriptores", obj["suscriptores_hoy"])
    horas = c.get("horas_12m")
    shorts90 = c.get("vistas_shorts_90d")
    dias_meta = (date.fromisoformat(obj["fecha_meta_90"]) - date.today()).days
    estados = dict(con.execute("SELECT estado, COUNT(*) FROM videos GROUP BY estado").fetchall())
    mes = datetime.now(timezone.utc).strftime("%Y-%m")
    gasto_mes = con.execute("SELECT COALESCE(SUM(euros),0) FROM costes WHERE fecha >= ?", (mes,)).fetchone()[0]
    fijos = sum(v for v in cfg["costes"].values())
    publicados = estados.get("publicado", 0)
    ideas = con.execute("SELECT COUNT(*) FROM ideas WHERE estado='nueva'").fetchone()[0]
    pend = dict(con.execute("SELECT agente, COUNT(*) FROM tareas WHERE estado IN ('pendiente','en_curso') GROUP BY agente").fetchall())
    fall = con.execute("SELECT COUNT(*) FROM tareas WHERE estado='fallida'").fetchone()[0]
    sin_dato = "— (falta conectar YouTube Analytics)"
    L = [
        "📊 PANEL · SHOCK MENTAL",
        f"Suscriptores: {subs}  ·  meta {obj['meta_90_dias']} el {obj['fecha_meta_90']} ({dias_meta} días) → {_pct(subs, obj['meta_90_dias'])}",
        f"Visualizaciones de Shorts (90 días): {shorts90 if shorts90 is not None else sin_dato}",
        f"Horas públicas de vídeos largos (12 meses): {horas if horas is not None else sin_dato}",
        "Monetización:",
        f"  • Ampliado (500 suscriptores; fan funding y Shopping, SIN anuncios): suscriptores {_pct(subs, 500)}"
        + (f" · Shorts {_pct(shorts90, 3e6)}" if shorts90 is not None else "") + (f" · horas {_pct(horas, 3000)}" if horas is not None else ""),
        f"  • Completo con anuncios (desde el 1-feb-2027 para canales nuevos: 1.000 suscriptores + 8.000 h o 20 M de Shorts en 90 días): suscriptores {_pct(subs, 1000)}",
        f"Vídeos: publicados {publicados} · en revisión {estados.get('revision', 0)} · aprobados/programados "
        f"{estados.get('aprobado', 0) + estados.get('programado', 0)} · en producción "
        f"{sum(estados.get(e, 0) for e in ('guion', 'verificacion', 'produccion', 'calidad', 'cambios'))} · bloqueados {estados.get('bloqueado', 0)}",
        f"Media de visualizaciones por vídeo: {c.get('media_vistas', sin_dato)}",
        f"Ideas en reserva: {ideas} · tareas pendientes: {pend or 0} · tareas fallidas: {fall}",
        f"Coste este mes: {gasto_mes:.2f} € variables + {fijos:.2f} € fijos · coste por vídeo: "
        f"{(gasto_mes + fijos) / max(1, publicados):.2f} €",
        f"Ingresos: {c.get('ingresos', 'todavía sin monetización')}",
        f"Modo: {cfg['general']['modo'].upper()}",
    ]
    return "\n".join(L)
