"""Agente 1 · Director: sincroniza con el bot, planifica según el calendario, encarga tareas,
ejecuta las partes automáticas (producción, calidad, envío) y vigila límites y errores."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from . import calidad, guion as G
from .nucleo import (PROD, REPO, ahora, cerrar_tarea, config, estado_video, fila, js, lecciones, log,
                     nueva_tarea)

sys.path.insert(0, str(PROD / "herramientas"))
import revision as RV  # noqa: E402  (bot de Telegram: conf, tg, bot, para_telegram, transcribir)

CEREBRO = {"investigador", "verificador", "guionista_short", "guionista_largo", "corrector"}
ACTIVOS = ("guion", "verificacion", "produccion", "calidad", "revision", "cambios", "aprobado", "programado")


# ---------- calendario ----------
def huecos(cfg: dict, dias: int = 7) -> list[tuple[str, datetime]]:
    """Huecos de publicación de los próximos días: [(formato, fecha_utc)]."""
    zona = ZoneInfo(cfg["general"]["zona"])
    hoy = datetime.now(zona).date()
    out = []
    for k in range(1, dias + 1):
        dia = hoy + timedelta(days=k)
        for formato, clave in (("short", "shorts"), ("largo", "largos")):
            for h in cfg["calendario"][clave]:
                if dia.weekday() in h["dias"]:
                    hh, mm = map(int, h["hora"].split(":"))
                    f = datetime(dia.year, dia.month, dia.day, hh, mm, tzinfo=zona).astimezone(timezone.utc)
                    if f.strftime("%Y-%m-%dT%H:%M:00.000Z") not in cfg["calendario"].get("reservados", []):
                        out.append((formato, f))
    return out


def calendario_para_bot(cfg: dict) -> dict:
    """Formato del Worker: {short: [[dow_js, h, m]], largo: [...]} con 0 = domingo."""
    out = {}
    for formato, clave in (("short", "shorts"), ("largo", "largos")):
        out[formato] = [[(d + 1) % 7, *map(int, h["hora"].split(":"))] for h in cfg["calendario"][clave] for d in h["dias"]]
    out["reservados"] = cfg["calendario"].get("reservados", [])
    return out


# ---------- sincronizar con el bot ----------
def sincronizar(con, cfg):
    try:
        c = RV.conf()
        RV.bot(c, "calendario", calendario_para_bot(cfg))
        items = {i["id"]: i for i in RV.bot(c, "items")["items"]}
        from . import voz as VZ
        elegida = (RV.bot(c, "ajustes").get("voz_elegida") or {}).get("letra")
        if elegida in VZ.PERFILES and elegida != VZ.perfil_actual().get("letra"):
            p = VZ.guardar_perfil(elegida)
            log(con, f"nuevo perfil oficial de locución: {elegida} ({p['nombre_perfil']})", agente="voz")
            avisar(f"🎙️ Perfil de voz oficial guardado: {elegida} · {p['nombre_perfil']}. Se usa desde el próximo vídeo.")
    except Exception as e:
        log(con, f"no puedo hablar con el bot: {e}", nivel="error")
        return {}
    for v in map(fila, con.execute("SELECT * FROM videos WHERE estado IN ('revision','cambios','aprobado','programado')")):
        it = items.get(v["id"])
        if not it or it.get("version") != v["version"]:
            continue
        e = it.get("estado")
        if e in ("programado", "aprobado") and v["estado"] != e:
            estado_video(con, v["id"], e, fecha_sugerida=it.get("fecha_utc"))
            log(con, f"aprobado por ti (versión {v['version']}) → {it.get('fecha_utc')}", video_id=v["id"])
        elif e == "publicado" and v["estado"] != "publicado":
            estado_video(con, v["id"], "publicado")
        elif e == "descartado" and v["estado"] != "rechazado":
            motivo = it.get("motivo_rechazo") or "sin motivo"
            estado_video(con, v["id"], "rechazado")
            con.execute("INSERT INTO lecciones (fecha, video_id, origen, texto) VALUES (?,?,?,?)",
                        (ahora(), v["id"], "rechazo", f"Rechazado «{v['titulo']}»: {motivo}"))
            log(con, f"rechazado: {motivo}", video_id=v["id"])
        elif e == "cambios" and v["estado"] != "cambios":
            instr = []
            for ch in it.get("cambios", []):
                if ch.get("voz"):
                    try:
                        info = RV.tg(c, "getFile", data={"file_id": ch["voz"]})
                        destino = RV.SY.BASE / "audios" / f"{v['id']}-{Path(info['file_path']).name}"
                        destino.parent.mkdir(parents=True, exist_ok=True)
                        if not destino.exists():
                            import requests
                            destino.write_bytes(requests.get(
                                f"https://api.telegram.org/file/bot{c['telegram_token']}/{info['file_path']}", timeout=120).content)
                        instr.append(RV.transcribir(destino))
                    except Exception as ex:
                        instr.append(f"(audio no transcrito: {ex})")
                else:
                    instr.append(ch.get("texto", ""))
            estado_video(con, v["id"], "cambios")
            nueva_tarea(con, "corrector", video_id=v["id"], datos={"instrucciones": instr, "version": v["version"]})
            RV.bot(c, "estado", {"id": v["id"], "estado": "rehaciendo", "nota": f"🛠️ Aplicando tus cambios a «{v['titulo']}»…"})
            log(con, f"cambios pedidos: {instr}", video_id=v["id"])
    return items


# ---------- planificar ----------
def planificar(con, cfg):
    hs = huecos(cfg, 7)
    activos = {f: con.execute("SELECT COUNT(*) FROM videos WHERE formato=? AND estado IN (%s)" % ",".join("?" * len(ACTIVOS)),
                              (f, *ACTIVOS)).fetchone()[0] for f in ("short", "largo")}
    necesarios = {f: max(0, sum(1 for x, _ in hs if x == f) - activos[f]) for f in ("short", "largo")}
    hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    creados_hoy = con.execute("SELECT COUNT(*) FROM videos WHERE creado >= ?", (hoy,)).fetchone()[0]
    cupo = max(0, cfg["limites"]["max_videos_dia"] - creados_hoy)
    ultimas = [r[0] for r in con.execute("SELECT categoria FROM videos ORDER BY creado DESC LIMIT ?",
                                         (cfg["calendario"]["separacion_temas"],))]
    for formato in ("largo", "short"):
        for _ in range(min(necesarios[formato], cupo)):
            idea = con.execute("SELECT * FROM ideas WHERE estado='nueva' AND (formato=? OR formato IS NULL) "
                               "AND COALESCE(categoria,'') NOT IN (%s) ORDER BY puntuacion DESC LIMIT 1"
                               % (",".join("?" * len(ultimas)) or "''"), (formato, *ultimas)).fetchone()
            if not idea:
                break
            idea = fila(idea)
            vid = nuevo_id(con, formato)
            con.execute("INSERT INTO videos (id, idea_id, formato, tipo, categoria, tema, estado, creado, actualizado, prueba) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?)", (vid, idea["id"], formato, idea["tipo"], idea["categoria"], idea["tema"],
                                                       "guion", ahora(), ahora(), 1 if cfg["general"]["modo"] == "prueba" else 0))
            con.execute("UPDATE ideas SET estado='elegida' WHERE id=?", (idea["id"],))
            nueva_tarea(con, "guionista_" + formato, video_id=vid, idea_id=idea["id"])
            ultimas.insert(0, idea["categoria"])
            cupo -= 1
            log(con, f"encargado {formato}: {idea['tema']}", video_id=vid)
    if con.execute("SELECT COUNT(*) FROM ideas WHERE estado='nueva'").fetchone()[0] < 15:
        nueva_tarea(con, "investigador", datos={"cuantas": 20})


def nuevo_id(con, formato: str) -> str:
    base = ("s" if formato == "short" else "l") + datetime.now().strftime("%y%m%d")
    n = con.execute("SELECT COUNT(*) FROM videos WHERE id LIKE ?", (base + "%",)).fetchone()[0]
    return f"{base}{n + 1:02d}"


# ---------- producción, calidad y envío (automático) ----------
def producir(con, cfg, v: dict, enviar: bool = True):
    g = v["guion"]
    errores = G.validar(g, cfg)
    if errores:
        return devolver(con, cfg, v, errores)
    try:
        carpeta = G.preparar(g, v["id"])
        r = subprocess.run([sys.executable, str(PROD / "montar.py"), str(carpeta)], capture_output=True, text=True,
                           timeout=3600, cwd=REPO)
        if r.returncode:
            raise RuntimeError(r.stderr[-1500:])
    except Exception as e:
        log(con, f"fallo al producir: {e}", agente="productor", nivel="error", video_id=v["id"])
        t = nueva_tarea(con, "productor", video_id=v["id"])
        if cerrar_tarea(con, t, error=str(e)) == "fallida":
            estado_video(con, v["id"], "bloqueado")
            avisar(f"⚠️ No consigo montar «{v['titulo']}» tras varios intentos:\n{str(e)[:400]}")
        return
    if g["formato"] == "largo":
        miniatura(con, g, carpeta, v["id"])
    from .cerebro import TITULOS_PREVIOS
    anteriores = [fila(x) for x in con.execute("SELECT tema, titulo FROM videos WHERE id != ? AND estado NOT IN ('rechazado')",
                                               (v["id"],))] + [{"tema": t, "titulo": t} for t in TITULOS_PREVIOS]
    rev = calidad.revisar(v["id"], carpeta, g, anteriores, cfg)
    estado_video(con, v["id"], "calidad", carpeta=str(carpeta.relative_to(REPO).as_posix()), calidad=rev,
                 puntuacion=rev["puntuacion"], duracion=rev["medidas"].get("duracion"))
    log(con, f"calidad {rev['puntuacion']}/100 · vetos {rev['vetos']} · avisos {rev['avisos']}", agente="calidad", video_id=v["id"])
    if not rev["ok"]:
        motivos = rev["vetos"] or [f"nota {rev['puntuacion']} < {cfg['calidad']['nota_minima']}"]
        return devolver(con, cfg, v, motivos)
    if enviar:
        enviar_revision(con, cfg, v["id"])


def miniatura(con, g: dict, carpeta: Path, vid: str):
    """Agente 7 · Diseñador: miniatura con la plantilla del canal. Fondo: miniatura_fondo.jpg si existe
    (por ejemplo, una ilustración que hagas con Gemini) o la foto de Commons indicada en guion.miniatura.fondo."""
    m = g.get("miniatura") or {}
    propio = carpeta / "miniatura_fondo.jpg"
    fondo = propio if propio.exists() else carpeta / "fotos" / f"{m.get('fondo', '')}.jpg"
    if not fondo.exists():
        log(con, "sin fondo para la miniatura", agente="disenador", nivel="aviso", video_id=vid)
        return
    datos = {"fondo": str(fondo), "l1": m.get("l1", ""), "l2": m.get("l2", ""), "chip": m.get("chip", ""),
             "fs": m.get("fs", "140px"), "zoom": m.get("zoom", "1"), "desplazar": m.get("desplazar", "0")}
    r = subprocess.run(["node", "generar-shock.js", str(carpeta / "salida" / "miniatura.png"), json.dumps(datos, ensure_ascii=False)],
                       cwd=REPO / "miniaturas", capture_output=True, text=True, timeout=300)
    log(con, "miniatura creada" if r.returncode == 0 else f"fallo miniatura: {r.stderr[-300:]}", agente="disenador",
        nivel="info" if r.returncode == 0 else "error", video_id=vid)


def devolver(con, cfg, v, motivos):
    if v["version"] >= cfg["limites"]["max_versiones"]:
        estado_video(con, v["id"], "bloqueado")
        avisar(f"⛔ «{v['titulo'] or v['tema']}» no supera el control de calidad tras {v['version']} versiones:\n• " +
               "\n• ".join(motivos[:5]) + "\nLo aparco. Si quieres salvarlo, dímelo.")
        return
    con.execute("UPDATE videos SET version = version + 1 WHERE id=?", (v["id"],))
    estado_video(con, v["id"], "guion")
    nueva_tarea(con, "corrector", video_id=v["id"], datos={"instrucciones": motivos, "origen": "control de calidad"})
    log(con, f"devuelto al guionista: {motivos}", agente="calidad", video_id=v["id"])


def enviar_revision(con, cfg, vid: str):
    v = fila(con.execute("SELECT * FROM videos WHERE id=?", (vid,)).fetchone())
    g, carpeta = v["guion"], REPO / v["carpeta"]
    video = carpeta / "salida" / "video.mp4"
    c = RV.conf()
    prueba = cfg["general"]["modo"] == "prueba"
    h = RV.bot(c, "hueco", tipo=v["formato"], id=vid)
    # portada: fotograma elegido (Shorts) o miniatura generada (largos)
    portada = carpeta / "salida" / "portada.jpg"
    seg = g.get("portada_segundo", 1)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(seg), "-i", str(video), "-frames:v", "1", "-q:v", "3", str(portada)])
    mini = carpeta / "salida" / "miniatura.png"
    foto = mini if mini.exists() else portada
    peq = RV.para_telegram(video)
    w, hh, dur = RV.medidas(peq)
    cab = "🧪 PRUEBA · " if prueba else ""
    with open(foto, "rb") as fh:
        RV.tg(c, "sendPhoto", data={"chat_id": c["dueno_id"], "caption": f"{cab}🖼️ Portada · segundo {seg}" if foto == portada
                                    else f"{cab}🖼️ Miniatura"}, files={"photo": fh})
    with open(peq, "rb") as fh:
        RV.tg(c, "sendVideo", data={"chat_id": c["dueno_id"], "caption": f"{cab}🎬 {v['titulo']}", "width": w, "height": hh,
                                    "duration": dur, "supports_streaming": "true"}, files={"video": fh})
    guion_txt = "\n".join(f["t"] for f in G.todas_frases(g))
    fuentes_txt = "\n".join(f"• {f.get('dato', '')[:80]} — {f.get('fuente', '')}: {f['url']}" for f in g["fuentes"])
    RV.bot(c, "revision", {
        "id": vid, "tipo": v["formato"], "version": v["version"], "titulo": g["titulo"], "descripcion": g["descripcion"],
        "etiquetas": g.get("etiquetas", []), "comentario": g.get("comentario"), "fecha_utc": h["fecha_utc"],
        "youtube_id": v.get("youtube_id"), "prueba": prueba, "duracion": round(v["duracion"] or dur),
        "puntuacion": v["puntuacion"], "coste": round(v["coste"] or 0, 2), "guion_texto": guion_txt[:3500],
        "fuentes_texto": fuentes_txt[:3500], "para_ninos": False, "sintetico": False,
        "avisos_calidad": (v["calidad"] or {}).get("avisos", []),
    })
    estado_video(con, vid, "revision", fecha_sugerida=h["fecha_utc"])
    log(con, f"enviado a Telegram (versión {v['version']}) para {h['fecha_texto']}", agente="publicador", video_id=vid)


def avisar(texto: str):
    try:
        RV.bot(RV.conf(), "avisar", {"texto": texto})
    except Exception as e:
        print("no puedo avisar por Telegram:", e)


# ---------- ciclo completo ----------
def ciclo(con):
    cfg = config()
    items = sincronizar(con, cfg) or {}
    from . import youtube
    for paso in (lambda: youtube.publicar_aprobados(con, cfg, items, avisar), lambda: youtube.analizar(con, cfg, avisar)):
        try:
            paso()
        except Exception as e:
            log(con, f"YouTube: {e}", agente="publicador/analista", nivel="error")
    planificar(con, cfg)
    for v in map(fila, con.execute("SELECT * FROM videos WHERE estado='produccion' ORDER BY creado").fetchall()):
        producir(con, cfg, v)
        con.commit()
    pend = con.execute("SELECT agente, COUNT(*) FROM tareas WHERE estado='pendiente' GROUP BY agente").fetchall()
    falladas = con.execute("SELECT COUNT(*) FROM tareas WHERE estado='fallida' AND actualizada >= ?",
                           ((datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),)).fetchone()[0]
    if falladas:
        avisar(f"⚠️ {falladas} tarea(s) han fallado en las últimas 24 h. Escribe /panel para ver el estado.")
    try:
        from .panel import panel
        RV.bot(RV.conf(), "panel", {"texto": panel(con)})
    except Exception as e:
        log(con, f"no pude actualizar el panel del bot: {e}", nivel="aviso")
    return {a: n for a, n in pend}
