#!/usr/bin/env python3
"""Instala (o actualiza) el bot de revisión de Shock Mental en Cloudflare Workers.

Necesita:
  - Variable de entorno CLOUDFLARE_API_TOKEN (y CLOUDFLARE_ACCOUNT_ID si la cuenta tiene varias).
  - wrangler instalado (npm i -g wrangler).
  - El token de Telegram: --telegram-token la primera vez (luego se recuerda).
  - Opcional: la autorización de YouTube en ~/.canales-youtube/tokens/shockmental.json
    (si aún no existe, el bot funciona igual pero el botón ✅ no podrá programar hasta volver a ejecutar esto).

Guarda la configuración del PC en ~/.canales-youtube/shockmental-bot.json (fuera del repo).
  python desplegar.py --telegram-token 123:ABC [--dueno-id 111] [--solo-secretos]
"""
import argparse, json, re, secrets, shutil, subprocess, sys
from pathlib import Path

import requests

AQUI = Path(__file__).resolve().parent
BASE = Path.home() / ".canales-youtube"
CONF = BASE / "shockmental-bot.json"
TOKEN_YT = BASE / "tokens" / "shockmental.json"
TOML = AQUI / "wrangler.toml"


def wrangler(*args, entrada=None):
    exe = shutil.which("wrangler") or sys.exit("No encuentro wrangler (npm i -g wrangler)")
    r = subprocess.run([exe, *args], cwd=AQUI, input=entrada, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        sys.exit(f"wrangler {' '.join(args)} falló:\n{r.stdout}\n{r.stderr}")
    return r.stdout + r.stderr


def tg(token, metodo, **datos):
    return requests.post(f"https://api.telegram.org/bot{token}/{metodo}", json=datos, timeout=60).json()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--telegram-token"); p.add_argument("--dueno-id")
    p.add_argument("--solo-secretos", action="store_true", help="solo actualiza los secretos (p. ej. tras autorizar YouTube)")
    a = p.parse_args()

    BASE.mkdir(parents=True, exist_ok=True)
    c = json.loads(CONF.read_text(encoding="utf-8")) if CONF.exists() else {}
    if a.telegram_token:
        c["telegram_token"] = a.telegram_token.strip()
    if not c.get("telegram_token"):
        sys.exit("Falta --telegram-token")
    me = tg(c["telegram_token"], "getMe")
    if not me.get("ok"):
        sys.exit(f"Ese token de Telegram no funciona: {me}")
    print(f"Bot: @{me['result']['username']} ({me['result']['first_name']})")

    if a.dueno_id:
        c["dueno_id"] = str(a.dueno_id)
    if not c.get("dueno_id"):
        tg(c["telegram_token"], "deleteWebhook")
        ups = tg(c["telegram_token"], "getUpdates").get("result", [])
        ids = {u["message"]["from"]["id"]: u["message"]["from"].get("first_name", "") for u in ups if "message" in u}
        if len(ids) != 1:
            sys.exit(f"No sé cuál es tu ID de Telegram (he visto: {ids or 'nadie'}). Escribe /start al bot y repite, o usa --dueno-id.")
        (i, nombre), = ids.items()
        c["dueno_id"] = str(i)
        print(f"Dueño: {nombre} (ID {i})")
    c.setdefault("clave", secrets.token_urlsafe(32))
    c.setdefault("webhook_secreto", secrets.token_urlsafe(32))
    CONF.write_text(json.dumps(c, indent=1), encoding="utf-8")

    toml = TOML.read_text(encoding="utf-8")
    if 'id = "PENDIENTE"' in toml:
        out = wrangler("kv", "namespace", "create", "DATOS")
        m = re.search(r'id\s*=\s*"([0-9a-f]{32})"', out) or re.search(r'"id":\s*"([0-9a-f]{32})"', out)
        if not m:
            sys.exit("No he entendido la respuesta al crear el almacén KV:\n" + out)
        TOML.write_text(toml.replace('id = "PENDIENTE"', f'id = "{m.group(1)}"'), encoding="utf-8")
        print("Almacén KV creado")

    if not a.solo_secretos:
        out = wrangler("deploy")
        m = re.search(r"https://[\w.-]+\.workers\.dev", out)
        if not m:
            sys.exit("No encuentro la dirección del bot en la salida de wrangler:\n" + out)
        c["url"] = m.group(0)
        CONF.write_text(json.dumps(c, indent=1), encoding="utf-8")
        print(f"Bot en la nube: {c['url']}")

    sec = {"TELEGRAM_TOKEN": c["telegram_token"], "DUENO_ID": c["dueno_id"],
           "WEBHOOK_SECRETO": c["webhook_secreto"], "PC_CLAVE": c["clave"]}
    if TOKEN_YT.exists():
        t = json.loads(TOKEN_YT.read_text(encoding="utf-8"))
        sec.update(GOOGLE_CLIENT_ID=t["client_id"], GOOGLE_CLIENT_SECRET=t["client_secret"], GOOGLE_REFRESH_TOKEN=t["refresh_token"])
    else:
        print("AVISO: YouTube aún no está autorizado; el botón ✅ no podrá programar todavía.")
    for nombre, valor in sec.items():
        wrangler("secret", "put", nombre, entrada=valor)
    print(f"Secretos puestos: {', '.join(sec)}")

    r = tg(c["telegram_token"], "setWebhook", url=c["url"] + "/telegram", secret_token=c["webhook_secreto"],
           allowed_updates=["message", "callback_query"], drop_pending_updates=False)
    if not r.get("ok"):
        sys.exit(f"Telegram no acepta el webhook: {r}")
    tg(c["telegram_token"], "setMyCommands", commands=[
        {"command": "idea", "description": "Guardar una idea para próximos vídeos"},
        {"command": "ideas", "description": "Ver la lista de ideas"},
        {"command": "pendientes", "description": "Lo que espera tu revisión"},
        {"command": "calendario", "description": "Lo que ya está programado"},
        {"command": "ayuda", "description": "Cómo funciona el bot"}])
    print("Listo: el bot responde 24 h desde la nube.")


if __name__ == "__main__":
    main()
