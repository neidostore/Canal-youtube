"""Responsable de TikTok · Content Posting API oficial (developers.tiktok.com, leída el 28-nov-2026).

Limitaciones reales (no se pueden saltar):
- App SIN auditar: «Direct Post» solo publica en privado (SELF_ONLY), en cuentas privadas, con un máximo de 5 usuarios en 24 h.
- La API NO permite programar una hora: el PC publica cuando llega la hora (ciclo de distribución cada 10 minutos).
- Modo «inbox» (scope video.upload): el vídeo llega a tu bandeja de TikTok como borrador y tú lo publicas en la app con 2 toques.
  No necesita auditoría, sirve con la cuenta pública y cumple las reglas de la API: privacidad y avisos los eliges tú en la app.
  Es el modo POR DEFECTO hasta que la app pase la auditoría.
- Tokens: el de acceso dura 2 h y el de refresco 180 días. Cada refresco devuelve un token nuevo que sustituye al anterior.
Secretos en ~/.canales-youtube/tiktok.json (fuera del repositorio). Nunca en Telegram ni en el código.
"""
from __future__ import annotations

import json
import secrets
import time
import urllib.parse
from pathlib import Path

import requests

from .nucleo import PRIVADO

CONF = PRIVADO / "tiktok.json"
API = "https://open.tiktokapis.com/v2"


class SinConexion(Exception):
    pass


def conf() -> dict:
    return json.loads(CONF.read_text(encoding="utf-8")) if CONF.exists() else {}


def _guardar(c: dict):
    CONF.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")


def conectado() -> bool:
    c = conf()
    return bool(c.get("refresh_token")) and c.get("refresh_expira", 0) > time.time() + 86400


def url_autorizacion(redirect_uri: str) -> str:
    c = conf()
    if not c.get("client_key"):
        raise SinConexion("falta client_key: crea la app en developers.tiktok.com (docs/autopilot/05-tiktok.md)")
    c["state"] = secrets.token_urlsafe(16)
    c["redirect_uri"] = redirect_uri
    _guardar(c)
    alcance = "user.info.basic,video.upload" + (",video.publish" if c.get("modo") == "directo" else "")
    return "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode({
        "client_key": c["client_key"], "scope": alcance, "response_type": "code",
        "redirect_uri": redirect_uri, "state": c["state"]})


def _token(datos: dict) -> dict:
    c = conf()
    r = requests.post(f"{API}/oauth/token/", data={"client_key": c["client_key"], "client_secret": c["client_secret"], **datos},
                      headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=60).json()
    if "access_token" not in r:
        raise SinConexion(f"TikTok no da el token: {r.get('error_description') or r}")
    c.update(access_token=r["access_token"], expira=time.time() + r["expires_in"] - 120, refresh_token=r["refresh_token"],
             refresh_expira=time.time() + r["refresh_expires_in"], open_id=r.get("open_id"), scope=r.get("scope"))
    _guardar(c)   # el refresh_token cambia en cada refresco: se sustituye SIEMPRE
    return c


def canjear_codigo(code: str, state: str) -> dict:
    c = conf()
    if state != c.get("state"):
        raise SinConexion("el «state» no coincide: autorización rechazada por seguridad")
    c = _token({"code": code, "grant_type": "authorization_code", "redirect_uri": c["redirect_uri"]})
    info = requests.get(f"{API}/user/info/?fields=open_id,display_name", headers={"Authorization": f"Bearer {c['access_token']}"},
                        timeout=60).json()
    c["cuenta"] = (info.get("data", {}).get("user") or {}).get("display_name")
    _guardar(c)
    return c


def _acceso() -> str:
    c = conf()
    if not c.get("refresh_token"):
        raise SinConexion("TikTok no está conectado")
    if c.get("expira", 0) < time.time():
        if c.get("refresh_expira", 0) < time.time():
            raise SinConexion("la autorización de TikTok ha caducado: hay que volver a conectar")
        c = _token({"grant_type": "refresh_token", "refresh_token": c["refresh_token"]})
    return c["access_token"]


def _post(ruta: str, cuerpo: dict) -> dict:
    r = requests.post(f"{API}{ruta}", json=cuerpo, timeout=60,
                      headers={"Authorization": f"Bearer {_acceso()}", "Content-Type": "application/json; charset=UTF-8"}).json()
    err = r.get("error", {})
    if err.get("code") not in (None, "ok"):
        raise RuntimeError(f"TikTok {ruta}: {err.get('code')} · {err.get('message')}")
    return r.get("data", {})


def publicar(video: Path, titulo: str) -> dict:
    """Sube el MISMO archivo aprobado (sin marcas de agua). Devuelve {publish_id, modo}."""
    c = conf()
    tam = video.stat().st_size
    if tam > 64 * 1024 * 1024:
        raise RuntimeError("vídeo de más de 64 MB: hace falta subirlo por trozos")   # los Shorts del canal pesan ~20-30 MB
    fuente = {"source": "FILE_UPLOAD", "video_size": tam, "chunk_size": tam, "total_chunk_count": 1}
    if c.get("modo") == "directo":
        info = _post("/post/publish/creator_info/query/", {})
        privacidad = c.get("privacidad")        # la elige el gerente expresamente (sin valor por defecto)
        if privacidad not in info.get("privacy_level_options", []):
            raise RuntimeError(f"privacidad «{privacidad}» no permitida; opciones: {info.get('privacy_level_options')}")
        d = _post("/post/publish/video/init/", {"post_info": {"title": titulo[:2200], "privacy_level": privacidad,
                  "disable_comment": False, "disable_duet": False, "disable_stitch": False}, "source_info": fuente})
    else:
        d = _post("/post/publish/inbox/video/init/", {"source_info": fuente})
    with open(video, "rb") as fh:
        r = requests.put(d["upload_url"], data=fh, timeout=600, headers={
            "Content-Type": "video/mp4", "Content-Length": str(tam), "Content-Range": f"bytes 0-{tam - 1}/{tam}"})
    if r.status_code not in (200, 201):
        raise RuntimeError(f"subida a TikTok: HTTP {r.status_code} {r.text[:200]}")
    return {"publish_id": d["publish_id"], "modo": c.get("modo", "inbox")}


def estado(publish_id: str) -> dict:
    return _post("/post/publish/status/fetch/", {"publish_id": publish_id})
