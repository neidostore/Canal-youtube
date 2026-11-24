#!/usr/bin/env python3
"""Sube un vídeo a YouTube a partir de su ficha de publicación (docs/shockmental/NN-*.md).

Se ejecuta en el PC del usuario. Las claves NUNCA van al repo: viven en
~/.canales-youtube/ (fuera del proyecto).

  ~/.canales-youtube/client_secret.json      ← el «ID de cliente OAuth» de Google Cloud (tipo «App de escritorio»)
  ~/.canales-youtube/tokens/<canal>.json     ← la autorización de cada canal (la crea «autorizar»)

Instalar una vez:
  pip install google-api-python-client google-auth-oauthlib

Uso:
  python subir_youtube.py autorizar shockmental
      Abre el navegador; eliges la cuenta y el canal y aceptas. Una vez por canal.

  python subir_youtube.py prueba shockmental docs/shockmental/11-ranking05.md
      Enseña lo que se subiría (título, descripción, etiquetas, ajustes) SIN subir nada.

  python subir_youtube.py subir shockmental docs/shockmental/11-ranking05.md --ok \\
        [--privacidad private|unlisted|public] [--programar 2026-11-25T18:00] [--miniatura img.jpg] [--video otro.mp4]
      Sube el vídeo. Sin --ok no sube: el OK lo da el usuario tras ver el vídeo en el móvil.
      Por defecto sube como PRIVADO. --programar (hora de España) lo deja privado y se publica solo a esa hora.

Notas:
  - Mientras Google no audite el proyecto de la API, todo lo subido queda privado
    aunque pidas «public». Se hace público a mano en la app de YouTube.
  - La API no deja fijar comentarios: el comentario fijado se publica con --comentar
    pero hay que fijarlo a mano.
  - Cuota gratis: 10.000 unidades/día; cada subida gasta 1.600 (≈6 vídeos al día).
"""
import argparse, datetime, json, os, re, sys, time
try:  # usa los certificados de Windows (el antivirus puede inspeccionar las conexiones)
    import truststore; truststore.inject_into_ssl()
except ImportError:
    pass
from pathlib import Path

BASE = Path.home() / ".canales-youtube"
SECRETO = BASE / "client_secret.json"
TOKENS = BASE / "tokens"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl"]  # force-ssl: para publicar el comentario
REPO = Path(__file__).resolve().parents[2]

CATEGORIAS = {  # nombre en la ficha → id de YouTube
    "cine y animación": 1, "autos y vehículos": 2, "música": 10, "mascotas y animales": 15,
    "deportes": 17, "viajes y eventos": 19, "videojuegos": 20, "gente y blogs": 22,
    "comedia": 23, "entretenimiento": 24, "noticias y política": 25, "consejos y estilo": 26,
    "educación": 27, "ciencia y tecnología": 28,
}


# ---------- ficha ----------
def secciones(md):
    out, actual = {}, None
    for linea in md.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", linea)
        if m:
            actual = m.group(1).strip().lower()
            out[actual] = []
        elif actual:
            out[actual].append(linea)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def si_no(txt):
    t = txt.strip().lower()
    return t.startswith("sí") or t.startswith("si")


def leer_ficha(ruta):
    md = Path(ruta).read_text(encoding="utf-8")
    s = secciones(md)
    for k in ("título", "descripción"):
        if not s.get(k):
            sys.exit(f"La ficha no tiene sección «## {k.capitalize()}»")
    titulo = s["título"].splitlines()[0].strip()
    desc = s["descripción"]
    m = re.search(r"^Vídeo:\s*(\S+)", md, re.M)
    video = (REPO / m.group(1)) if m else None

    # etiquetas: los hashtags de título y descripción, sin «#»
    etiquetas = []
    for h in re.findall(r"#([\wáéíóúñü]+)", titulo + " " + desc, re.I):
        if h.lower() not in [e.lower() for e in etiquetas]:
            etiquetas.append(h)

    ajustes = {}
    for linea in s.get("ajustes", "").splitlines():
        m = re.match(r"^\s*-\s*([^:]+):\s*(.+)$", linea)
        if m:
            ajustes[m.group(1).strip().lower()] = m.group(2).strip()

    cat_txt = ajustes.get("categoría", "entretenimiento").lower()
    categoria = CATEGORIAS.get(cat_txt)
    if categoria is None:
        sys.exit(f"Categoría desconocida en la ficha: «{cat_txt}». Válidas: {', '.join(CATEGORIAS)}")

    ninos = ajustes.get("público", "no")
    para_ninos = not ("no" in ninos.lower().split(",")[0])
    sintetico = si_no(ajustes.get("contenido alterado o sintético", "no"))
    comentario = ajustes.get("comentario fijado")

    if len(titulo) > 100:
        sys.exit(f"El título tiene {len(titulo)} caracteres (máx. 100)")
    if len(desc.encode("utf-8")) > 5000:
        sys.exit("La descripción pasa de 5.000 bytes")
    if "<" in titulo + desc or ">" in titulo + desc:
        sys.exit("YouTube no admite «<» ni «>» en título o descripción")

    return dict(titulo=titulo, descripcion=desc, etiquetas=etiquetas[:30], categoria=categoria,
                para_ninos=para_ninos, sintetico=sintetico, comentario=comentario, video=video)


# ---------- Google ----------
def credenciales(canal, crear=False):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow

    tok = TOKENS / f"{canal}.json"
    cred = Credentials.from_authorized_user_file(str(tok), SCOPES) if tok.exists() else None
    if cred and cred.expired and cred.refresh_token:
        cred.refresh(Request())
    if not cred or not cred.valid:
        if not crear:
            sys.exit(f"El canal «{canal}» no está autorizado. Ejecuta: subir_youtube.py autorizar {canal}")
        if not SECRETO.exists():
            sys.exit(f"Falta {SECRETO} (descárgalo de Google Cloud → Credenciales → ID de cliente OAuth, tipo App de escritorio)")
        cred = InstalledAppFlow.from_client_secrets_file(str(SECRETO), SCOPES).run_local_server(port=0)
    TOKENS.mkdir(parents=True, exist_ok=True)
    tok.write_text(cred.to_json(), encoding="utf-8")
    try:
        os.chmod(tok, 0o600)
    except OSError:
        pass
    return cred


def autorizar_movil(canal, vuelta=None):
    """Autorización sin navegador en el PC: se abre el enlace en el móvil y se pega la dirección de vuelta.

    Paso 1 (sin --vuelta): imprime el enlace. Paso 2: --vuelta "http://localhost:8765/?state=…&code=…"
    (la página de vuelta no carga en el móvil; es normal: basta con copiar su dirección)."""
    from google_auth_oauthlib.flow import Flow
    from urllib.parse import urlparse, parse_qs
    if not SECRETO.exists():
        sys.exit(f"Falta {SECRETO}")
    pendiente = BASE / f"autorizar-{canal}.json"
    redirect = "http://localhost:8765/"
    if not vuelta:
        flow = Flow.from_client_secrets_file(str(SECRETO), SCOPES, redirect_uri=redirect)
        url, state = flow.authorization_url(access_type="offline", prompt="consent", include_granted_scopes="true")
        pendiente.write_text(json.dumps({"state": state, "verifier": flow.code_verifier}), encoding="utf-8")
        print(url)
        return None
    d = json.loads(pendiente.read_text(encoding="utf-8"))
    flow = Flow.from_client_secrets_file(str(SECRETO), SCOPES, redirect_uri=redirect, state=d["state"])
    flow.code_verifier = d["verifier"]
    q = parse_qs(urlparse(vuelta.strip()).query)
    if "code" not in q:
        sys.exit("En esa dirección no viene el código («code=»). Copia la dirección completa de la página de vuelta.")
    flow.fetch_token(code=q["code"][0])
    TOKENS.mkdir(parents=True, exist_ok=True)
    (TOKENS / f"{canal}.json").write_text(flow.credentials.to_json(), encoding="utf-8")
    pendiente.unlink(missing_ok=True)
    return flow.credentials


def servicio(canal, crear=False):
    from googleapiclient.discovery import build
    return build("youtube", "v3", credentials=credenciales(canal, crear), cache_discovery=False)


def nombre_canal(yt):
    r = yt.channels().list(part="snippet", mine=True).execute()
    it = r.get("items") or []
    return it[0]["snippet"]["title"] if it else "?"


def hora_utc(txt):
    """'2026-11-25T18:00' en hora de España → ISO UTC."""
    from zoneinfo import ZoneInfo
    local = datetime.datetime.fromisoformat(txt)
    if local.tzinfo is None:
        local = local.replace(tzinfo=ZoneInfo("Europe/Madrid"))
    utc = local.astimezone(datetime.timezone.utc)
    if utc <= datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15):
        sys.exit("La hora programada tiene que ser al menos 15 minutos en el futuro")
    return utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def subir(yt, f, video, privacidad, programar, miniatura, comentar):
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError

    status = {"privacyStatus": privacidad, "selfDeclaredMadeForKids": f["para_ninos"],
              "containsSyntheticMedia": f["sintetico"], "embeddable": True}
    if programar:
        status["privacyStatus"] = "private"
        status["publishAt"] = hora_utc(programar)
    body = {"snippet": {"title": f["titulo"], "description": f["descripcion"], "tags": f["etiquetas"],
                        "categoryId": str(f["categoria"]), "defaultLanguage": "es", "defaultAudioLanguage": "es"},
            "status": status}

    media = MediaFileUpload(str(video), chunksize=8 * 1024 * 1024, resumable=True, mimetype="video/mp4")
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media, notifySubscribers=True)
    resp, fallos = None, 0
    while resp is None:
        try:
            st, resp = req.next_chunk()
            if st:
                print(f"  subiendo… {int(st.progress() * 100)} %", flush=True)
        except HttpError as e:
            if e.resp.status in (500, 502, 503, 504) and fallos < 6:
                fallos += 1; time.sleep(2 ** fallos); continue
            raise
        except (ConnectionError, TimeoutError, OSError):
            if fallos < 6:
                fallos += 1; time.sleep(2 ** fallos); continue
            raise
    vid = resp["id"]
    print(f"SUBIDO: https://youtu.be/{vid}  (estado: {resp['status']['privacyStatus']})")

    if miniatura:
        try:
            yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(miniatura))).execute()
            print("  miniatura puesta")
        except HttpError as e:
            print(f"  AVISO: no se pudo poner la miniatura ({e.resp.status}). En Shorts no se puede; en vídeos largos el canal debe estar verificado.")
    if comentar and f.get("comentario"):
        try:
            yt.commentThreads().insert(part="snippet", body={"snippet": {"videoId": vid,
                "topLevelComment": {"snippet": {"textOriginal": f["comentario"]}}}}).execute()
            print("  comentario publicado (fíjalo a mano en la app de YouTube)")
        except HttpError as e:
            print(f"  AVISO: no se pudo comentar ({e.resp.status}); con el vídeo privado es normal. Publícalo cuando esté público.")
    return vid


def main():
    p = argparse.ArgumentParser(description="Sube vídeos a YouTube desde la ficha de publicación")
    sub = p.add_subparsers(dest="orden", required=True)
    a = sub.add_parser("autorizar"); a.add_argument("canal")
    am = sub.add_parser("autorizar-movil", help="autorizar desde el móvil copiando y pegando la dirección de vuelta")
    am.add_argument("canal"); am.add_argument("--vuelta")
    for nombre in ("prueba", "subir"):
        s = sub.add_parser(nombre)
        s.add_argument("canal"); s.add_argument("ficha")
        s.add_argument("--video"); s.add_argument("--miniatura")
        s.add_argument("--privacidad", choices=["private", "unlisted", "public"], default="private")
        s.add_argument("--programar", help="fecha y hora de España, p. ej. 2026-11-25T18:00")
        s.add_argument("--comentar", action="store_true", help="publica el comentario fijado de la ficha")
        if nombre == "subir":
            s.add_argument("--ok", action="store_true", help="confirmación del usuario tras revisar el vídeo")
    args = p.parse_args()

    if args.orden == "autorizar-movil":
        if autorizar_movil(args.canal, args.vuelta):
            print(f"Autorizado «{args.canal}» → canal de YouTube: {nombre_canal(servicio(args.canal))}")
        return
    if args.orden == "autorizar":
        yt = servicio(args.canal, crear=True)
        print(f"Autorizado «{args.canal}» → canal de YouTube: {nombre_canal(yt)}")
        return

    f = leer_ficha(args.ficha)
    video = Path(args.video) if args.video else f["video"]
    if not video or not video.exists():
        sys.exit(f"No encuentro el vídeo: {video}")
    if args.miniatura and not Path(args.miniatura).exists():
        sys.exit(f"No encuentro la miniatura: {args.miniatura}")

    print(f"Vídeo:      {video}  ({video.stat().st_size / 1e6:.1f} MB)")
    print(f"Título:     {f['titulo']}")
    print(f"Etiquetas:  {', '.join(f['etiquetas'])}")
    print(f"Categoría:  {f['categoria']} · para niños: {'sí' if f['para_ninos'] else 'no'} · sintético: {'sí' if f['sintetico'] else 'no'}")
    print(f"Privacidad: {'programado ' + args.programar if args.programar else args.privacidad}")
    print("Descripción:\n" + "\n".join("  | " + l for l in f["descripcion"].splitlines()))

    if args.orden == "prueba":
        print("\n(prueba: no se ha subido nada)")
        return
    if not args.ok:
        sys.exit("\nNo subo sin --ok. El usuario tiene que dar el visto bueno tras ver el vídeo.")
    yt = servicio(args.canal)
    print(f"\nCanal de destino: {nombre_canal(yt)}")
    subir(yt, f, video, args.privacidad, args.programar, args.miniatura, args.comentar)


if __name__ == "__main__":
    main()
