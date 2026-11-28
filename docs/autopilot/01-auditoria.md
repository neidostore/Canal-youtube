# Shock Mental Autopilot · Fase 1: auditoría del sistema actual

Fecha: 28 de noviembre de 2026. Repositorio `neidostore/Canal-youtube` (**público**), rama `ccr-927e3ba3-isn217`, 117 commits.

## 1. Lenguajes y herramientas
| Pieza | Tecnología | Dónde corre |
|---|---|---|
| Montaje de vídeo | Python 3.12 + ffmpeg 9.1 + PIL + numpy | PC con Windows (también funcionaba en Linux) |
| Tarjetas, intro y miniaturas | Node + Playwright/Chromium, HTML/CSS | PC |
| Voz | Google Cloud Text-to-Speech, `es-US-Chirp3-HD-Achird` a 1,15x | API de Google (clave en una variable de entorno del usuario) |
| Transcripción de audios de Telegram | faster-whisper «small» (local) | PC |
| Bot de revisión | JavaScript en Cloudflare Workers + KV, cron cada 15 min | Nube, gratis, 24 h |
| Subida a YouTube | Python + google-api-python-client (OAuth) | PC, **sin activar** |

## 2. Estructura
- `produccion/montar.py` (670 líneas) es el motor. Convierte `escenas.json` en `salida/video.mp4` con voz, clips, fotos con créditos, subtítulos animados, emojis, rótulos, tarjetas, efectos, música mezclada aparte (sin cortes), marco o marca y capítulos. Formato horizontal o vertical.
- `produccion/marco.py`, `render_tarjetas.js`, `render_html.js`, `tarjetas-shock.html`: estilo visual del canal.
- `produccion/herramientas/`
  - `crear_*.py`: un script por vídeo que escribe su `escenas.json`. **Hoy lo escribe Claude a mano en cada conversación.**
  - `commons_buscar.py`, `openverse.py`, `wiki.py`, `pexels_catalogo.py`: búsqueda de fotos con licencia libre, textos de Wikipedia y clips de Pexels (catálogo sin conexión de unos 28 MB).
  - `revision.py`: lado PC del bot (enviar a revisión, leer tareas, transcribir audios, ideas, avisos).
  - `subir_youtube.py`: subida por la API oficial, con autorización desde el móvil.
- `miniaturas/generar-shock.js` + `plantilla-shock.html`: miniaturas con el estilo del canal.
- `bot-revision/`: `worker.js`, `wrangler.toml` y `desplegar.py`.
- `docs/shockmental/NN-*.md`: una ficha por vídeo (título, descripción, fuentes, créditos, ajustes y comentario fijado).
- `marca/`, `musica/` (Kevin MacLeod, CC BY 4.0), `produccion/efectos/` y `produccion/clips/` (clips de Pexels en caché, 0,7 GB, fuera de git).

## 3. El bot de Telegram (lo que ya hace)
- Solo responde al dueño (`DUENO_ID`) y el webhook va con token secreto.
- Botones: ✅ Aprobar · ✏️ Pedir cambios (por texto o audio, se cierra con `/listo`) · ❌ Descartar.
- Órdenes: `/idea`, `/ideas`, `/pendientes`, `/calendario`, `/ayuda`.
- Calendario: ranking martes y viernes 19:00 · short lunes, miércoles y sábado · Dosis jueves 18:00. **Está fijo en el código.**
- Al aprobar, programa la fecha en YouTube (`publishAt`). **Necesita que el vídeo ya esté subido** y los secretos de Google, que todavía no existen.
- Cron cada 15 minutos: avisa a la hora de publicar e incluye el comentario fijado.
- API para el PC (`/pc/*`, con clave): `hueco`, `revision`, `tareas`, `estado`, `avisar`, `ideas`, `items`.
- Las versiones se cuentan (`version`), y los cambios anteriores se guardan.

## 4. Conexiones y credenciales (estado real)
| Servicio | Estado |
|---|---|
| Google TTS | ✅ Funciona (`GOOGLE_TTS_API_KEY` en el entorno del usuario) |
| Telegram | ✅ Funciona (token en `~/.canales-youtube/shockmental-bot.json` y en los secretos de Cloudflare) |
| Cloudflare Workers + KV | ✅ Funciona (`CLOUDFLARE_API_TOKEN` en el entorno del usuario) |
| GitHub | ✅ `gh` autenticado. El repositorio es **público**: nunca debe llevar claves (hoy no lleva ninguna) |
| YouTube Data API (subir y programar) | ❌ **No conectada.** Falta el proyecto OAuth de Google Cloud. Además, sin auditoría de Google los vídeos subidos por la API se quedan privados |
| YouTube Analytics API | ❌ No conectada (usa la misma autorización OAuth, con permiso de solo lectura) |
| Modelo de IA para investigar y escribir sin intervención | ❌ **No existe.** Hoy todo lo hace Claude en conversación. No hay clave de Anthropic ni de Gemini |
| Programación automática (cron) en el PC | ❌ No hay ninguna tarea programada en Windows |

## 5. Costes actuales
- Cloudflare, Telegram, GitHub, Pexels, Wikimedia y Wikipedia: gratis.
- Google TTS: un Short son unos 800 caracteres y una Dosis unos 6.000. Al ritmo actual son menos de 60.000 caracteres al mes, que debería quedar dentro del tramo gratuito mensual de Google. **Hay que confirmarlo en la consola de facturación de Google Cloud.**
- Claude: la suscripción del usuario, usada en conversación.
- **Coste por vídeo hoy: unos 0 € de herramientas** más el tiempo de revisión.

## 6. Qué funciona, qué falta y qué se reutiliza
**Funciona y se reutiliza tal cual:** el motor de montaje, el estilo visual, las búsquedas de fotos y clips con licencia, la voz, el bot con sus botones y versiones, la plantilla de miniaturas y las fichas de publicación.

**Problemas encontrados:**
1. El catálogo de Pexels estaba en una carpeta temporal. **Ya está copiado** a `~/.canales-youtube/datos/pexels.parquet`.
2. Los scripts de ayuda (búsqueda en Commons con pausas, detector de cortes de audio, hojas de fotogramas) estaban en la carpeta temporal y deben pasar al repositorio.
3. Cada vídeo necesita su propio `crear_*.py` escrito a mano. Falta un formato de guion estándar que el sistema pueda generar solo.
4. El calendario está fijo en `worker.js`.
5. No hay base de datos de contenido: el historial está repartido entre las fichas `.md`, KV y las carpetas.
6. No hay registro de costes ni de errores.

**Falta para el piloto automático:** un cerebro (modelo de IA) que pueda ejecutarse solo, un ejecutor programado, la cola de contenido, YouTube OAuth (subir, programar y analítica), el control de calidad automático y el panel de métricas.

## 7. Requisitos de monetización (fuentes oficiales, leídas el 28-nov-2026)
Fuentes: [Resumen del YPP](https://support.google.com/youtube/answer/72851?hl=es), [YPP ampliado](https://support.google.com/youtube/answer/13429240?hl=es) y [Cambios en el YPP](https://support.google.com/youtube/answer/12843009?hl=es).

| Nivel | Requisito hoy | Desde el 1 de febrero de 2027 (canales nuevos) | Qué da |
|---|---|---|---|
| **Ampliado** (España incluida) | 500 suscriptores + 3 subidas públicas en 90 días + (3.000 h en 12 meses **o** 3 M de visualizaciones de Shorts en 90 días) | Sin cambios | Membresías, Super Thanks/Chat, Shopping. **No incluye anuncios** |
| **Completo** (anuncios) | 1.000 suscriptores + (4.000 h en 12 meses **o** 10 M de visualizaciones de Shorts en 90 días) | 1.000 suscriptores + (**8.000 h** en 365 días **o** **20 M** de visualizaciones de Shorts en 90 días) | Reparto de anuncios y Premium |

**Conclusión honesta:** el objetivo de los 6 meses cae en mayo de 2027, con las reglas nuevas, que son el doble de exigentes. Para un canal que empezó el 2 de noviembre y lleva 15.000 visitas, la monetización completa por anuncios en 6 meses es muy poco probable. La meta intermedia realista es el **nivel ampliado (500 suscriptores)**, y el panel medirá el progreso hacia los dos niveles. Además, YouTube revisa el canal entero contra sus políticas de monetización, incluido el contenido repetitivo o «no auténtico». Por eso producir en masa sin valor propio pondría la monetización en peligro.
