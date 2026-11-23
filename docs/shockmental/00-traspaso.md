# Traspaso — SHOCK MENTAL (para seguir en una conversación nueva)

Léelo entero antes de hacer nada. Todo el trabajo está en la rama `ccr-19a9f894-tb9pz5`.

## El canal
- **SHOCK MENTAL** («Tu dosis de asombro»), @shockmental_tv. Canal sin cara en español, de curiosidades con datos comprobados y fuentes. Identidad en `01-identidad-y-canal.md`.
- El usuario sube todo a YouTube; Claude no tiene acceso a YouTube.
- Formatos:
  - **«Dosis de Asombro #N»:** vídeos largos horizontales de 11–12 curiosidades. Carpetas `produccion/shock01..06`.
  - **Shorts** de cada Dosis: `produccion/shorts-shock*`.
  - **Rankings verticales top 5** (5→1, una lista a la izquierda que se va rellenando), inspirados en Xiro Ranks. Funcionan muy bien. Carpetas `produccion/ranking01..05`.
- Fichas de publicación (título, descripción, hashtags, ajustes, comentario fijado): `docs/shockmental/NN-*.md`.

## Normas del usuario (siempre)
- **Antes de montar algo entero, una prueba corta** (gancho y 2 puestos) para que la vea. Nada de trabajo desperdiciado.
- **Clips de vídeo reales** de cada cosa siempre que existan. Fotos solo cuando no haya vídeo, animadas y con emojis, etiquetas, flechas y círculos.
- **Voz latina** `es-US-Chirp3-HD-Achird` a 1.15. No le gustó Puck.
- **Temas de actualidad y virales.** Nada de tragedias ni política como gancho. Si una idea es mala para la monetización o el copyright, decírselo y proponer una alternativa.
- **Datos verificados** (Wikipedia, NOAA, Guinness…) y matices honestos en el guion. Créditos obligatorios en la descripción cuando la licencia es CC BY / CC BY-SA.
- Shorts con marca del canal: el logo arriba y el logo grande con «Suscríbete» al final.
- Escribirle en español, claro y corto. Usa el móvil.

## Cómo se monta
- `produccion/montar.py <carpeta>` lee `<carpeta>/escenas.json` y produce `salida/video.mp4`. Hace la voz (Google TTS), clips y fotos, subtítulos, efectos, música, ranking y marca.
- La clave de Google TTS está en la variable de entorno `GOOGLE_TTS_API_KEY` del entorno «Predeterminado». No está en el repo y **nunca** debe subirse.
- Claves de `escenas.json`:
  - **Globales:** `formato: "vertical"`, `marca`, `ranking{titulo,puestos}`, `videos{nombre: id_pexels}`, `fotos{nombre: 0}` (0 = archivo local `fotos/nombre.jpg`), `credito_fotos`, `videos_inicio`.
  - **Por frase:**
    - Texto e imagen: `t` (texto y voz), `vid` [lista] o `img` [lista]. **Si pones las dos, solo sale el vídeo.**
    - Ranking y anotaciones: `rank{n,texto,emoji}`, `marcas` [emoji / texto / flecha / círculo / contorno, con `pos` relativa a la pantalla, `tam`, `en` (segundo de aparición) y `fondo`].
    - Sonido: `sfx{nombre:"ding",vol,en}`, `respiro` (pausa extra), `sonido` (volumen del audio real del clip), `sonido_de` (usar el audio de otro clip), `sonido_archivo` + `sonido_inicio` (un mp3 de `clips/`).
- Clips de Pexels: `produccion/clips/descargar.sh ID...`. Los .mp4 no se suben al repo; se vuelven a descargar.
- Buscar clips: el catálogo offline de Pexels (358.000 títulos) es el parquet del dataset de Hugging Face `ITOCJ/pexelvideos` (`/api/datasets/ITOCJ/pexelvideos/parquet/default/train/0.parquet`). Script de ejemplo: `produccion/herramientas/pexels_catalogo.py`.
- Fotos libres:
  - `produccion/herramientas/openverse.py "consulta" prefijo N [flickr]` descarga a tamaño completo a través de Openverse y guarda los créditos en `creditos.json`.
  - `produccion/herramientas/commons_buscar.py` busca en Wikimedia Commons.
  - `produccion/herramientas/wiki.py "Título" "regex"` comprueba datos en Wikipedia.
- Sonidos libres: la API de Openverse (`/v1/audio/`) da sonidos CC0 de Freesound.
- Commits en español, en la rama `ccr-19a9f894-tb9pz5`. `salida/` y `trabajo/` no se suben.

## Bloqueos que había en la conversación anterior
- **Wikimedia (upload.wikimedia.org y la API de Commons):** devolvía 429 durante días por la conexión de aquella sesión. Comprobar si en esta ya va.
- **usgs.gov:** bloquea con un 403 de su CDN. No intentar saltárselo.
- **Descargas de YouTube:** bloqueadas. No intentar saltárselo.

## Estado
- Ya publicados o entregados: Dosis #1–#6, sus Shorts, y los rankings 01 (animales más rápidos), 02 (animales más mortales), 03 (fenómenos naturales con sonido real), 04 (objetos fuera de su tiempo) y 05 (coches de policía más locos).
- **CAMBIO (23-nov-2026): el ranking 06 es ahora «GTA 6 y lo más rápido en llegar a 1.000 millones $».** El de youtubers se descartó: no se pueden usar fotos de personas reales y varios canales son de niños.
  - Guion y escenas listos en `produccion/ranking06-prueba/` (gancho + puestos 5 y 4) y `produccion/ranking06/` (entero).
  - Falta: rellenar `videos` con IDs de Pexels usando `videos_por_buscar` (sin imágenes del juego ni tráileres: copyright de Rockstar), montar la prueba y mandársela.
  - Datos: GTA 6, 3.790 M$ el primer día (19-nov-2026) y 32,5 M de copias antes de salir (Take-Two, nota de prensa del 20-nov-2026; incluye reservas). GTA V 3 días, Endgame 5 días, CoD MWII 10 días (Guinness). Avatar 17 días (Statista).
  - Créditos de la descripción: Guinness World Records, Take-Two Interactive, Statista.
- (Descartado) ranking de youtubers:, con MrBeast como gancho. Datos de Wikipedia, «List of most-subscribed YouTube channels», noviembre de 2026, solo personas y no empresas:
  - 1 MrBeast, 527 M (el único por encima de 500 M)
  - 2 Vlad y Niki, 151 M
  - 3 Stokes Twins, 150 M
  - 4 Kids Diana Show, 139 M
  - 5 Like Nastya, 134 M
  - También interesan Alejo Igoa (126 M, el youtuber en español más seguido) y PewDiePie (109 M, fue el número 1 durante años).
- **Lo que falta:**
  1. Fotos libres de cada youtuber, sobre todo de Wikimedia Commons. No usar capturas ni miniaturas de sus canales (copyright) ni imágenes de IA de personas reales.
  2. Montar la prueba (gancho y 2 puestos) y mandársela.
  3. Si da el visto bueno, montar el ranking entero y escribir la ficha `12-ranking06.md`.
