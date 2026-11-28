"""Agente 9 · Publicador y Agente 10 · Analista (API oficial de YouTube).

Requisitos: ~/.canales-youtube/client_secret.json y la autorización del canal (docs/autopilot/03-google-oauth.md).
Sin ellos, todo queda en espera y el panel lo indica; no se rompe nada.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .nucleo import PROD, REPO, ahora, estado_video, fila, js, log

sys.path.insert(0, str(PROD / "herramientas"))
import subir_youtube as SY  # noqa: E402

CATEGORIA = {"short": 24, "largo": 27}   # 24 = Entretenimiento, 27 = Educación


def conectado() -> bool:
    return SY.SECRETO.exists() and (SY.TOKENS / "shockmental.json").exists()


def _credenciales():
    return SY.credenciales("shockmental")


# ---------- Publicador ----------
def publicar_aprobados(con, cfg, items_bot: dict, avisar):
    """Sube en PRIVADO y programa SOLO lo que tú aprobaste en Telegram (vídeo + versión). Nunca dos veces."""
    if cfg["general"]["modo"] != "produccion":
        return
    if not conectado():
        log(con, "hay vídeos aprobados pero YouTube no está conectado", agente="publicador", nivel="aviso")
        return
    from .director import RV
    yt = SY.servicio("shockmental")
    for v in map(fila, con.execute("SELECT * FROM videos WHERE estado='aprobado' AND prueba=0 AND youtube_id IS NULL")):
        it = items_bot.get(v["id"])
        if not it or it.get("estado") != "aprobado" or str(it.get("version_aprobada")) != str(v["version"]):
            continue   # sin aprobación inequívoca de ESTA versión no se sube nada
        carpeta = REPO / v["carpeta"]
        g = v["guion"]
        desc = g["descripcion"]
        cap = carpeta / "salida" / "capitulos.txt"
        if v["formato"] == "largo" and cap.exists() and "00:00" not in desc:
            desc = desc.split("\n\n", 1)[0] + "\n\n" + cap.read_text(encoding="utf-8").strip() + "\n\n" + desc.split("\n\n", 1)[-1]
        f = {"titulo": g["titulo"], "descripcion": desc, "etiquetas": g.get("etiquetas", []), "categoria": CATEGORIA[v["formato"]],
             "para_ninos": False, "sintetico": False, "comentario": g.get("comentario")}
        local = datetime.fromisoformat(it["fecha_utc"].replace("Z", "+00:00")).astimezone(ZoneInfo(cfg["general"]["zona"]))
        mini = carpeta / "salida" / "miniatura.png"
        try:
            vid = SY.subir(yt, f, carpeta / "salida" / "video.mp4", "private", local.strftime("%Y-%m-%dT%H:%M"),
                           mini if (v["formato"] == "largo" and mini.exists()) else None, False)
        except SystemExit as e:   # hora demasiado próxima
            avisar(f"⚠️ No subo «{g['titulo']}»: {e}. Pulsa 📅 Cambiar fecha.")
            continue
        estado_video(con, v["id"], "programado", youtube_id=vid)
        from .distribucion import preparar
        preparar(con, v, it["fecha_utc"], vid)   # misma aprobación → YouTube (programado) + TikTok (a su hora)
        con.commit()   # se guarda YA: así nunca se sube dos veces
        RV.bot(RV.conf(), "programado", {"id": v["id"], "version": v["version"], "youtube_id": vid})
        log(con, f"subido y programado https://youtu.be/{vid} para {local:%d/%m %H:%M}", agente="publicador", video_id=v["id"])


# ---------- Analista ----------
def _analytics():
    from googleapiclient.discovery import build
    return build("youtubeAnalytics", "v2", credentials=_credenciales(), cache_discovery=False)


def analizar(con, cfg, avisar):
    """Una vez al día: suscriptores, Shorts 90 días, horas 12 meses, rendimiento por vídeo y alertas."""
    hoy = date.today().isoformat()
    if not conectado() or con.execute("SELECT 1 FROM canal WHERE fecha=?", (hoy,)).fetchone():
        return
    yt, ya = SY.servicio("shockmental"), _analytics()
    stats = yt.channels().list(part="statistics", mine=True).execute()["items"][0]["statistics"]
    q = lambda **kw: ya.reports().query(ids="channel==MINE", endDate=hoy, **kw).execute()
    tipo = q(startDate=(date.today() - timedelta(days=90)).isoformat(), metrics="views", dimensions="creatorContentType")
    shorts90 = sum(r[1] for r in tipo.get("rows", []) if r[0] == "SHORTS")
    largo = q(startDate=(date.today() - timedelta(days=365)).isoformat(), metrics="estimatedMinutesWatched", dimensions="creatorContentType")
    horas = round(sum(r[1] for r in largo.get("rows", []) if r[0] != "SHORTS") / 60, 1)
    porvideo = q(startDate=cfg["objetivos"]["inicio"], metrics="views,averageViewDuration,averageViewPercentage,subscribersGained",
                 dimensions="video", sort="-views", maxResults=200)
    filas = porvideo.get("rows", [])
    media = round(sum(r[1] for r in filas) / max(1, len(filas)))
    datos = {"suscriptores": int(stats.get("subscriberCount", 0)), "vistas_totales": int(stats.get("viewCount", 0)),
             "videos": int(stats.get("videoCount", 0)), "vistas_shorts_90d": int(shorts90),
             "horas_12m": horas, "horas_nota": "aproximadas (minutos de vídeos no-Shorts); YouTube Studio da las «horas válidas» exactas",
             "media_vistas": media}
    con.execute("INSERT OR REPLACE INTO canal (fecha, datos) VALUES (?,?)", (hoy, js(datos)))
    for r in filas:
        con.execute("INSERT OR REPLACE INTO metricas (video_id, youtube_id, fecha, datos) VALUES "
                    "((SELECT id FROM videos WHERE youtube_id=?),?,?,?)",
                    (r[0], r[0], hoy, js({"vistas": r[1], "duracion_media": r[2], "porcentaje_visto": r[3], "subs": r[4]})))
    # alertas
    for r in filas[:5]:
        if media and r[1] > 2.5 * media:
            t = con.execute("SELECT titulo FROM videos WHERE youtube_id=?", (r[0],)).fetchone()
            avisar(f"🚀 Un vídeo va muy por encima de la media ({r[1]} vistas vs {media}): "
                   f"{t[0] if t else 'https://youtu.be/' + r[0]}\n¿Hacemos una segunda parte? Responde /idea segunda parte de …")
            con.execute("INSERT INTO lecciones (fecha, origen, texto) VALUES (?,?,?)",
                        (ahora(), "analista", f"ÉXITO: «{t[0] if t else r[0]}» hizo {r[1]} vistas ({r[3]:.0f} % visto). Repite tema, gancho y formato."))
    log(con, f"métricas: {datos}", agente="analista")
    leer_comentarios(con, yt)


# ---------- Community Manager (borradores; publicar requiere tu ✅) ----------
def leer_comentarios(con, yt):
    from .nucleo import nueva_tarea
    canal_id = yt.channels().list(part="id", mine=True).execute()["items"][0]["id"]
    r = yt.commentThreads().list(part="snippet", allThreadsRelatedToChannelId=canal_id, maxResults=50, order="time").execute()
    nuevos = 0
    for th in r.get("items", []):
        s = th["snippet"]["topLevelComment"]["snippet"]
        if th["snippet"].get("totalReplyCount", 0) or s.get("authorChannelId", {}).get("value") == canal_id:
            continue
        if con.execute("INSERT OR IGNORE INTO comentarios (id, youtube_id, autor, texto, fecha) VALUES (?,?,?,?,?)",
                       (th["id"], s.get("videoId"), s.get("authorDisplayName"), s.get("textOriginal", "")[:1000], s.get("publishedAt"))).rowcount:
            nuevos += 1
    if nuevos:
        nueva_tarea(con, "community", datos={"nuevos": nuevos})


def publicar_respuestas(con, aprobadas: list[str], avisar):
    if not aprobadas or not conectado():
        return []
    yt = SY.servicio("shockmental")
    hechas = []
    for cid in aprobadas:
        c = fila(con.execute("SELECT * FROM comentarios WHERE id=? AND estado='enviado' AND tipo IN ('rutinario','idea')", (cid,)).fetchone())
        if not c or not c["borrador"]:
            continue
        yt.comments().insert(part="snippet", body={"snippet": {"parentId": cid, "textOriginal": c["borrador"]}}).execute()
        con.execute("UPDATE comentarios SET estado='respondido' WHERE id=?", (cid,))
        hechas.append(cid)
    if hechas:
        avisar(f"💬 Publicadas {len(hechas)} respuestas que aprobaste.")
    return hechas
