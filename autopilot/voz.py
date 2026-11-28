"""SHOCK MENTAL VOICE DIRECTOR · perfiles de locución con la MISMA voz (Google «Achird»).

Herramienta actual: Google Cloud Text-to-Speech, voz es-US-Chirp3-HD-Achird.
Qué permite Chirp 3 HD (docs oficiales, nov-2026): velocidad (0,25-2,0), pausas en «markup» ([pause short], [pause],
[pause long]), SSML básico y pronunciaciones. NO tiene control de emoción ni de estilo.
La entonación se dirige con la escritura: puntuación, frases cortas, preguntas y pausas antes de cada revelación.
Gemini-TTS ofrece la misma voz «Achird» con una instrucción de estilo en lenguaje natural, pero tiene coste
(unos 10 $ por millón de tokens de audio, unos 2 €/mes al ritmo actual) → SOLO con autorización del dueño.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from .nucleo import PRIVADO, PROD

sys.path.insert(0, str(PROD))
sys.path.insert(0, str(PROD / "herramientas"))

PERFIL_OFICIAL = PRIVADO / "perfil_voz.json"
BASE = {"idioma": "es-US", "nombre": "es-US-Chirp3-HD-Achird"}

PERFILES = {
    "A": {"nombre_perfil": "Actual", "velocidad": 1.15, "estilo": "actual",
          "explica": "La de ahora: mismo texto de siempre, a 1,15x, sin pausas dirigidas."},
    "B": {"nombre_perfil": "Dinámica", "velocidad": 1.22, "estilo": "dinamico",
          "explica": "Más rápida, con exclamaciones y una pausa corta antes de cada revelación."},
    "C": {"nombre_perfil": "Equilibrada", "velocidad": 1.12, "estilo": "equilibrado",
          "explica": "Algo más pausada, con preguntas retóricas, pausas antes del dato y remate final."},
}
# Perfil expresivo con Gemini-TTS (misma voz «Achird»). Tiene coste: el gerente autorizó la PRUEBA el 28-nov-2026.
GEMINI = {"nombre_perfil": "Gemini expresiva", "velocidad": 1.0, "estilo": "actual", "modelo": "gemini-2.5-flash-tts",
          "idioma_gemini": "es-419",
          "instruccion": ("Eres el narrador de un canal de curiosidades en español latinoamericano neutro. Habla con curiosidad y "
                          "entusiasmo natural, como un comentarista agradable que disfruta contando cada dato; ritmo ágil pero "
                          "claro, pequeña pausa antes de cada cifra sorprendente, sin gritar ni exagerar."),
          "explica": "La misma voz Achird con Gemini-TTS e instrucción de estilo (curiosidad y entusiasmo natural). Tiene coste."}

# Mismo contenido para las tres pruebas; cambia solo la DIRECCIÓN (puntuación, pausas y velocidad).
MUESTRA = {
    "actual": [
        "Alguien pagó seis millones de dólares por un plátano pegado a la pared con cinta… y luego se lo comió.",
        "Ranking: las cosas más locas que se han vendido por millones.",
        "Número cinco: un tuit. El primero de la historia de Twitter. Se vendió por dos millones novecientos mil dólares.",
        "Un año después, su dueño intentó revenderlo… y la mejor oferta fue de unos doscientos ochenta dólares.",
    ],
    "dinamico": [
        "¡Alguien pagó seis millones de dólares por un plátano pegado a la pared con cinta! [pause short] Y luego… se lo comió.",
        "Ranking: ¡las cosas más locas que se han vendido por millones!",
        "Número cinco: [pause short] un tuit. ¡El primero de la historia de Twitter! Se vendió por… dos millones novecientos mil dólares.",
        "Un año después, su dueño intentó revenderlo. ¿Y la mejor oferta? [pause short] ¡Unos doscientos ochenta dólares!",
    ],
    "equilibrado": [
        "Alguien pagó seis millones de dólares… por un plátano pegado a la pared con cinta. [pause short] Y luego se lo comió.",
        "Ranking: las cosas más locas que se han vendido por millones.",
        "Número cinco: un tuit. [pause short] El primero de la historia de Twitter. Se vendió por dos millones novecientos mil dólares.",
        "Un año después, su dueño intentó revenderlo. ¿Y la mejor oferta? [pause short] Unos doscientos ochenta dólares.",
    ],
}


def perfil_actual() -> dict:
    """Configuración de voz oficial (la elegida en Telegram) o la de siempre."""
    if PERFIL_OFICIAL.exists():
        return json.loads(PERFIL_OFICIAL.read_text(encoding="utf-8"))
    return {**BASE, "velocidad": 1.15, "estilo": "actual", "letra": "A"}


def guardar_perfil(letra: str):
    p = {**BASE, **{k: v for k, v in PERFILES[letra].items() if k in ("velocidad", "estilo")}, "letra": letra,
         "nombre_perfil": PERFILES[letra]["nombre_perfil"]}
    PERFIL_OFICIAL.write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def generar_pruebas(destino: Path) -> dict[str, Path]:
    import montar as M
    key = M.clave() if hasattr(M, "clave") else os.environ["GOOGLE_TTS_API_KEY"]
    destino.mkdir(parents=True, exist_ok=True)
    out = {}
    for letra, p in PERFILES.items():
        trozos = []
        for i, frase in enumerate(MUESTRA[p["estilo"]]):
            w = destino / f"{letra}_{i}.wav"
            M.tts(frase, {**BASE, "velocidad": p["velocidad"]}, w, key)
            trozos.append(w)
        lista = destino / f"{letra}.txt"
        lista.write_text("".join(f"file '{t.as_posix()}'\n" for t in trozos), encoding="utf-8")
        mp3 = destino / f"prueba_voz_{letra}.mp3"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista),
                        "-af", "apad=pad_dur=0.25,loudnorm=I=-14", "-c:a", "libmp3lame", "-b:a", "160k", str(mp3)], check=True)
        out[letra] = mp3
    return out


def enviar_pruebas(rutas: dict[str, Path]):
    import revision as RV
    c = RV.conf()
    RV.tg(c, "sendMessage", data={"chat_id": c["dueno_id"], "parse_mode": "HTML", "text":
          "🎙️ <b>Prueba de locución</b>: la MISMA voz y el mismo texto, con tres interpretaciones.\n"
          "Escúchalas y elige la que será la voz oficial de Shock Mental."})
    for letra, ruta in rutas.items():
        p = PERFILES[letra]
        with open(ruta, "rb") as fh:
            RV.tg(c, "sendAudio", data={"chat_id": c["dueno_id"], "title": f"{letra} · {p['nombre_perfil']}",
                                        "performer": "Shock Mental", "caption": f"{letra} · {p['nombre_perfil']}: {p['explica']}"},
                  files={"audio": (ruta.name, fh, "audio/mpeg")})
    RV.tg(c, "sendMessage", data={"chat_id": c["dueno_id"], "text": "¿Cuál prefieres?", "reply_markup": json.dumps(
        {"inline_keyboard": [[{"text": f"{l} · {PERFILES[l]['nombre_perfil']}", "callback_data": f"vz:{l}"} for l in PERFILES]]})})
