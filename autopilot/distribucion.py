"""Distribución coordinada YouTube Shorts + TikTok de UNA aprobación (mismo vídeo, misma versión).

- YouTube se programa con publishAt (lo publica YouTube a la hora exacta).
- TikTok no admite programar por API: el PC lo sube cuando llega esa hora (comprobación cada 10 minutos)
  y se registra la diferencia real. NO es simultáneo al segundo, y no se dice que lo sea.
- Una fila por plataforma: si una falla, solo se reintenta esa (máximo 3 intentos), nunca la otra.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from . import tiktok as TT
from .nucleo import REPO, ahora, config, decision, fila, log


def preparar(con, v: dict, hora_utc: str, youtube_id: str | None):
    cfg = config()
    con.execute("INSERT OR IGNORE INTO publicaciones (video_id, plataforma, version, estado, id_externo, url, hora_prevista, actualizado) "
                "VALUES (?,?,?,?,?,?,?,?)", (v["id"], "youtube", v["version"], "programado", youtube_id,
                                             f"https://youtu.be/{youtube_id}" if youtube_id else None, hora_utc, ahora()))
    if v["formato"] == "short" and (cfg.get("tiktok", {}).get("activo") or TT.conectado()):
        con.execute("INSERT OR IGNORE INTO publicaciones (video_id, plataforma, version, estado, hora_prevista, actualizado) "
                    "VALUES (?,?,?,?,?,?)", (v["id"], "tiktok", v["version"], "pendiente", hora_utc, ahora()))


def titulo_tiktok(g: dict) -> str:
    """TikTok: texto con gancho + hashtags (sin #shorts)."""
    t = g["titulo"].replace("#shorts", "").replace("#Shorts", "").strip()
    tags = [x for x in (g.get("etiquetas") or [])[:4]]
    return f"{t} " + " ".join("#" + x.replace(" ", "") for x in tags) + " #curiosidades #shockmental"


def ejecutar(con, avisar):
    """Publica en TikTok lo que ya ha llegado a su hora; marca YouTube como publicado cuando pasa su hora."""
    ahora_dt = datetime.now(timezone.utc)
    for p in map(fila, con.execute("SELECT * FROM publicaciones WHERE estado IN ('pendiente','reintentar','programado')")):
        hora = datetime.fromisoformat(p["hora_prevista"].replace("Z", "+00:00"))
        if hora > ahora_dt:
            continue
        v = fila(con.execute("SELECT * FROM videos WHERE id=?", (p["video_id"],)).fetchone())
        if p["plataforma"] == "youtube":
            con.execute("UPDATE publicaciones SET estado='publicado', hora_real=?, actualizado=? WHERE video_id=? AND plataforma='youtube'",
                        (p["hora_prevista"], ahora(), p["video_id"]))
            continue
        if v["version"] != p["version"]:
            con.execute("UPDATE publicaciones SET estado='cancelado', error='la versión cambió tras la aprobación' "
                        "WHERE video_id=? AND plataforma='tiktok'", (p["video_id"],))
            continue
        if not TT.conectado():
            if p["estado"] != "reintentar":
                avisar("🔗 Hay un Short aprobado para TikTok y TikTok no está conectado (o la autorización caducó).\n"
                       "Cuando quieras, escribe /tiktok y te guío para conectarlo. YouTube no se ve afectado.")
            con.execute("UPDATE publicaciones SET estado='reintentar', error='TikTok sin conectar', actualizado=? "
                        "WHERE video_id=? AND plataforma='tiktok'", (ahora(), p["video_id"]))
            continue
        try:
            r = TT.publicar(REPO / v["carpeta"] / "salida" / "video.mp4", titulo_tiktok(v["guion"]))
            dif = round((datetime.now(timezone.utc) - hora).total_seconds() / 60)
            estado = "en_borradores" if r["modo"] == "inbox" else "publicado"
            con.execute("UPDATE publicaciones SET estado=?, id_externo=?, hora_real=?, intentos=intentos+1, error=NULL, actualizado=? "
                        "WHERE video_id=? AND plataforma='tiktok'", (estado, r["publish_id"], ahora(), ahora(), p["video_id"]))
            yt = con.execute("SELECT url FROM publicaciones WHERE video_id=? AND plataforma='youtube'", (p["video_id"],)).fetchone()
            avisar(f"📤 Distribución de «{v['titulo']}»\n• YouTube: ✅ {yt[0] if yt else ''}\n• TikTok: "
                   + ("📥 en tus borradores de TikTok: ábrelo y pulsa Publicar" if estado == "en_borradores" else "✅ publicado")
                   + f"\n⏱️ Diferencia con YouTube: {dif} min")
            log(con, f"TikTok {estado} ({dif} min tras YouTube)", agente="tiktok", video_id=p["video_id"])
        except Exception as e:
            intentos = p["intentos"] + 1
            nuevo = "reintentar" if intentos < 3 else "fallido"
            con.execute("UPDATE publicaciones SET estado=?, intentos=?, error=?, actualizado=? WHERE video_id=? AND plataforma='tiktok'",
                        (nuevo, intentos, str(e)[:500], ahora(), p["video_id"]))
            log(con, f"TikTok falló ({intentos}/3): {e}", agente="tiktok", nivel="error", video_id=p["video_id"])
            if nuevo == "fallido":
                decision(con, "distribucion", f"TikTok no publicado: «{v['titulo']}»", str(e)[:200], requiere_gerente=True)
                avisar(f"⚠️ TikTok ha fallado 3 veces con «{v['titulo']}» ({str(e)[:200]}). YouTube está bien publicado. "
                       "No reintento más: dime si lo vuelvo a intentar.")
