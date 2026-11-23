# Subida automática a YouTube (desde el PC)

Script: `produccion/herramientas/subir_youtube.py`. Sube un vídeo usando su ficha
(`docs/shockmental/NN-*.md`, con el formato de las fichas 09–11: `Vídeo:`, `## Título`,
`## Descripción`, `## Ajustes`). Sirve para varios canales.

## Flujo
1. Claude monta el vídeo y escribe la ficha.
2. Claude manda el vídeo al móvil: «compruébalo».
3. El usuario da el OK.
4. Claude ejecuta `subir ... --ok` en el PC. Sin `--ok` el script no sube nada.

## Preparación (una sola vez)
1. **Programas en el PC:** Python 3.10 o superior, ffmpeg y
   `pip install google-api-python-client google-auth-oauthlib`.
2. **Google Cloud** (console.cloud.google.com), con la cuenta dueña de los canales:
   1. Crear un proyecto, por ejemplo «subidas-canales».
   2. «APIs y servicios» → Biblioteca → activar **YouTube Data API v3**.
   3. «Pantalla de consentimiento OAuth»: tipo Externo, y añadir tu correo como usuario de prueba.
      Después, **publicar la app** («En producción»). En modo prueba, la autorización caduca a los 7 días.
   4. «Credenciales» → Crear → **ID de cliente OAuth** → tipo **App de escritorio** → descargar el JSON.
   5. Guardarlo como `~/.canales-youtube/client_secret.json`. En Windows es
      `C:\Users\<tú>\.canales-youtube\client_secret.json`.
3. **Autorizar cada canal:** `python produccion/herramientas/subir_youtube.py autorizar shockmental`.
   Se abre el navegador; eliges el canal y aceptas. Para otro canal, otro nombre:
   `autorizar canal2`.

Las autorizaciones se guardan en `~/.canales-youtube/tokens/`, fuera del repo. **Nunca subirlas a GitHub.**

## Notas del PC con Windows
- Instalado con winget: Git (en `%LOCALAPPDATA%\Programs\Git`), Python 3.12, FFmpeg (Gyan), Node LTS y GitHub CLI.
  Playwright global (`npm i -g playwright` + `npx playwright install chromium`) y la variable de usuario `NODE_PATH` apuntando a `npm root -g`.
- Fuentes Inter Display y NotoColorEmoji instaladas para el usuario en `%LOCALAPPDATA%\Microsoft\Windows\Fonts`;
  `marco.py` las busca ahí si no están en `/usr/share/fonts`.
- Variable de usuario `PYTHONUTF8=1`: los scripts escriben archivos sin indicar UTF-8.
- `montar.py` usa el bash de Git for Windows para `clips/descargar.sh` y escapa las rutas `C:` en los filtros de ffmpeg.
- En Windows se llama `python`, no `python3`.

## Uso
```
python produccion/herramientas/subir_youtube.py prueba shockmental docs/shockmental/11-ranking05.md
python produccion/herramientas/subir_youtube.py subir  shockmental docs/shockmental/11-ranking05.md --ok --programar 2026-11-25T18:00
```
- `prueba` enseña el título, la descripción, las etiquetas y los ajustes sin subir nada.
- Por defecto sube como **privado**. También admite `--privacidad unlisted|public`.
- `--programar` usa la hora de España.
- `--miniatura img.jpg` pone la miniatura. No funciona en Shorts, y en vídeos largos el canal tiene que estar verificado.
- `--comentar` publica el comentario de la ficha. Fijarlo hay que hacerlo a mano.

## Límites
- **Hasta que Google audite el proyecto, todo lo subido queda privado.** Se hace público
  a mano en la app de YouTube. La auditoría se pide en el formulario «YouTube API Services – Audit and Quota Extension».
- **Cuota:** 10.000 unidades al día. Cada subida gasta 1.600, así que caben unos 6 vídeos al día entre todos los canales.
- **Varios canales:** cada uno necesita estilo y guiones propios. YouTube no monetiza el contenido
  repetitivo o «producido en masa».
