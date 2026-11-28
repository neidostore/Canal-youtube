"""Núcleo del Autopilot: rutas, configuración, base de datos, registro, costes y límites.

La base de datos vive FUERA del repositorio (que es público): ~/.canales-youtube/autopilot.db
"""
from __future__ import annotations

import json
import sqlite3
import tomllib
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROD = REPO / "produccion"
PRIVADO = Path.home() / ".canales-youtube"
DATOS = PRIVADO / "datos"
DB_RUTA = PRIVADO / "autopilot.db"
CONFIG_RUTA = Path(__file__).with_name("config.toml")

ESTADOS_VIDEO = [
    "idea", "investigacion", "verificacion", "guion", "produccion", "calidad",
    "revision", "cambios", "aprobado", "programado", "publicado", "rechazado", "bloqueado",
]

ESQUEMA = """
CREATE TABLE IF NOT EXISTS ideas (
  id INTEGER PRIMARY KEY, tema TEXT NOT NULL, formato TEXT, tipo TEXT, categoria TEXT,
  origen TEXT, notas TEXT, puntos TEXT, puntuacion REAL, estado TEXT DEFAULT 'nueva',
  motivo TEXT, creada TEXT
);
CREATE TABLE IF NOT EXISTS videos (
  id TEXT PRIMARY KEY, idea_id INTEGER, formato TEXT, tipo TEXT, categoria TEXT, tema TEXT,
  estado TEXT, version INTEGER DEFAULT 1, carpeta TEXT, guion TEXT, fuentes TEXT,
  titulo TEXT, descripcion TEXT, comentario TEXT, etiquetas TEXT, puntuacion REAL, calidad TEXT,
  duracion REAL, fecha_sugerida TEXT, youtube_id TEXT, coste REAL DEFAULT 0, prueba INTEGER DEFAULT 1,
  creado TEXT, actualizado TEXT
);
CREATE TABLE IF NOT EXISTS tareas (
  id INTEGER PRIMARY KEY, agente TEXT NOT NULL, video_id TEXT, idea_id INTEGER,
  estado TEXT DEFAULT 'pendiente', intentos INTEGER DEFAULT 0, datos TEXT, resultado TEXT,
  error TEXT, creada TEXT, actualizada TEXT
);
CREATE TABLE IF NOT EXISTS costes (
  id INTEGER PRIMARY KEY, fecha TEXT, concepto TEXT, video_id TEXT, unidades REAL, euros REAL
);
CREATE TABLE IF NOT EXISTS registro (
  id INTEGER PRIMARY KEY, fecha TEXT, nivel TEXT, agente TEXT, video_id TEXT, mensaje TEXT
);
CREATE TABLE IF NOT EXISTS lecciones (
  id INTEGER PRIMARY KEY, fecha TEXT, video_id TEXT, origen TEXT, texto TEXT, activa INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS metricas (
  video_id TEXT, youtube_id TEXT, fecha TEXT, datos TEXT, PRIMARY KEY (youtube_id, fecha)
);
CREATE TABLE IF NOT EXISTS canal (
  fecha TEXT PRIMARY KEY, datos TEXT
);
CREATE TABLE IF NOT EXISTS publicaciones (      -- una fila por vídeo y plataforma: nunca se publica dos veces
  video_id TEXT, plataforma TEXT, version INTEGER, estado TEXT DEFAULT 'pendiente', id_externo TEXT, url TEXT,
  hora_prevista TEXT, hora_real TEXT, intentos INTEGER DEFAULT 0, error TEXT, actualizado TEXT,
  PRIMARY KEY (video_id, plataforma)
);
CREATE TABLE IF NOT EXISTS decisiones (         -- registro del CEO
  id INTEGER PRIMARY KEY, fecha TEXT, area TEXT, decision TEXT, motivo TEXT, requiere_gerente INTEGER DEFAULT 0, estado TEXT
);
CREATE TABLE IF NOT EXISTS comentarios (
  id TEXT PRIMARY KEY, youtube_id TEXT, autor TEXT, texto TEXT, fecha TEXT, tipo TEXT, borrador TEXT, estado TEXT DEFAULT 'nuevo'
);
CREATE TABLE IF NOT EXISTS ajustes (
  clave TEXT PRIMARY KEY, valor TEXT
);
"""


def decision(con, area: str, texto: str, motivo: str = "", requiere_gerente: bool = False):
    """Registro de decisiones importantes del CEO (se resumen en los informes)."""
    con.execute("INSERT INTO decisiones (fecha, area, decision, motivo, requiere_gerente, estado) VALUES (?,?,?,?,?,?)",
                (ahora(), area, texto, motivo, int(requiere_gerente), "pendiente" if requiere_gerente else "tomada"))


def ajuste(con, clave: str, valor=None):
    if valor is None:
        r = con.execute("SELECT valor FROM ajustes WHERE clave=?", (clave,)).fetchone()
        return json.loads(r[0]) if r else None
    con.execute("INSERT OR REPLACE INTO ajustes (clave, valor) VALUES (?,?)", (clave, json.dumps(valor, ensure_ascii=False)))


def ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def config() -> dict:
    return tomllib.loads(CONFIG_RUTA.read_text(encoding="utf-8"))


@contextmanager
def db(ruta: Path | None = None):
    ruta = ruta or DB_RUTA
    ruta.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(ruta)
    con.row_factory = sqlite3.Row
    con.executescript(ESQUEMA)
    try:
        yield con
        con.commit()
    finally:
        con.close()


def fila(r: sqlite3.Row | None) -> dict | None:
    if r is None:
        return None
    d = dict(r)
    for k in ("puntos", "guion", "fuentes", "calidad", "etiquetas", "datos", "resultado"):
        if isinstance(d.get(k), str) and d[k][:1] in "[{":
            try:
                d[k] = json.loads(d[k])
            except json.JSONDecodeError:
                pass
    return d


def js(o) -> str:
    return json.dumps(o, ensure_ascii=False)


def log(con, mensaje: str, agente: str = "director", nivel: str = "info", video_id: str | None = None):
    con.execute("INSERT INTO registro (fecha, nivel, agente, video_id, mensaje) VALUES (?,?,?,?,?)",
                (ahora(), nivel, agente, video_id, mensaje))
    print(f"[{nivel}] {agente}{' ' + video_id if video_id else ''}: {mensaje}")


# ---------- costes y límites ----------
class LimiteSuperado(Exception):
    pass


def gastado(con, desde: str) -> float:
    return con.execute("SELECT COALESCE(SUM(euros),0) FROM costes WHERE fecha >= ?", (desde,)).fetchone()[0]


def apuntar_coste(con, concepto: str, euros: float, video_id: str | None = None, unidades: float = 0):
    """Apunta un gasto. Si supera el límite diario o mensual, lanza LimiteSuperado ANTES de gastar."""
    lim = config()["limites"]
    hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    mes = hoy[:7]
    if gastado(con, hoy) + euros > lim["euros_dia"]:
        raise LimiteSuperado(f"límite diario de {lim['euros_dia']} € alcanzado")
    if gastado(con, mes) + euros > lim["euros_mes"]:
        raise LimiteSuperado(f"límite mensual de {lim['euros_mes']} € alcanzado")
    con.execute("INSERT INTO costes (fecha, concepto, video_id, unidades, euros) VALUES (?,?,?,?,?)",
                (ahora(), concepto, video_id, unidades, euros))
    if video_id:
        con.execute("UPDATE videos SET coste = coste + ? WHERE id = ?", (euros, video_id))


# ---------- tareas ----------
def nueva_tarea(con, agente: str, video_id: str | None = None, idea_id: int | None = None, datos: dict | None = None) -> int:
    ya = con.execute("SELECT id FROM tareas WHERE agente=? AND COALESCE(video_id,'')=COALESCE(?,'') AND "
                     "COALESCE(idea_id,0)=COALESCE(?,0) AND estado IN ('pendiente','en_curso')",
                     (agente, video_id, idea_id)).fetchone()
    if ya:
        return ya[0]   # evita duplicar trabajo
    cur = con.execute("INSERT INTO tareas (agente, video_id, idea_id, datos, creada, actualizada) VALUES (?,?,?,?,?,?)",
                      (agente, video_id, idea_id, js(datos or {}), ahora(), ahora()))
    return cur.lastrowid


def cerrar_tarea(con, tarea_id: int, resultado: dict | None = None, error: str | None = None):
    lim = config()["limites"]["reintentos"]
    t = fila(con.execute("SELECT * FROM tareas WHERE id=?", (tarea_id,)).fetchone())
    if error:
        intentos = t["intentos"] + 1
        estado = "pendiente" if intentos <= lim else "fallida"
        con.execute("UPDATE tareas SET estado=?, intentos=?, error=?, actualizada=? WHERE id=?",
                    (estado, intentos, error[:2000], ahora(), tarea_id))
        return estado
    con.execute("UPDATE tareas SET estado='hecha', resultado=?, error=NULL, actualizada=? WHERE id=?",
                (js(resultado or {}), ahora(), tarea_id))
    return "hecha"


def estado_video(con, video_id: str, estado: str, **campos):
    assert estado in ESTADOS_VIDEO, estado
    sets = ", ".join(f"{k}=?" for k in campos)
    vals = [js(v) if isinstance(v, (dict, list)) else v for v in campos.values()]
    con.execute(f"UPDATE videos SET estado=?, actualizado=?{', ' + sets if sets else ''} WHERE id=?",
                [estado, ahora(), *vals, video_id])


def lecciones(con) -> list[str]:
    return [r[0] for r in con.execute("SELECT texto FROM lecciones WHERE activa=1 ORDER BY id DESC LIMIT 30")]
