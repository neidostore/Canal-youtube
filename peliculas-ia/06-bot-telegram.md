# Neido Studio · Bot de revisión por Telegram (plan)

> Estado: ✅ **bot instalado** (24/11/2026) en Cloudflare Workers por Claude a través de la API.
> - Bot: **@NeidoStudioRevisionBot** · dirección: `https://neido-bot.neidostore.workers.dev`
> - Almacenamiento: KV `neido-bot` (el token de Cloudflare no tiene permiso de D1; KV basta para un bot personal).
> - Se activa solo (tarea cada 5 min que comprueba el webhook). El primero que escribe /start queda como dueño.
> - Secretos en Cloudflare: TELEGRAM_TOKEN, WEBHOOK_SECRET, CLAUDE_KEY (nunca en el repositorio).
> - Pendiente: dar a la sesión de Claude acceso al dominio del bot (formulario seguro con CLAUDE_KEY) y YouTube.
> - La cuenta de Cloudflare tiene otros proyectos del usuario (diagnosticalo-ia, KV "DATOS"): no tocarlos. Solo para Neido Studio (Shock Mental tendrá su propio bot en su conversación).

## Cómo funciona (tres piezas)

```
 Tú (móvil, Telegram)
        ▲   │  botones ✅ ✏️ ❌, /idea, /pendientes, textos y audios
        │   ▼
 BOT "Neido Studio · Revisión"  — vive gratis en Cloudflare Workers, 24 h, aunque tu PC esté apagado
   · guarda: pendientes, cambios pedidos, ideas, calendario (base de datos D1, gratis)
   · guarda las claves secretas (Telegram, YouTube) — Claude nunca las ve
        ▲   │
        │   ▼
 CLAUDE (sesiones en la nube)
   · produce el vídeo y lo manda al bot para revisión
   · cada hora, una tarea programada mira si has aprobado o pedido cambios:
       – cambios → los aplica (transcribe tus audios) y te reenvía la versión nueva
       – aprobado → sube el vídeo a YouTube programado y te lo confirma por el bot
```

## Lo que hay que saber (comprobado, noviembre 2026)
| Tema | Realidad |
|---|---|
| Tamaño de vídeo en Telegram | Un bot puede **enviar** archivos de hasta **50 MB** y **descargar** hasta **20 MB**. Las películas se comprimen a 720p para revisión; si aun así pasan de 50 MB, se manda un enlace. ([fast.io](https://fast.io/resources/telegram-file-size-limit/), [n8n](https://community.n8n.io/t/getting-large-file-from-telegram-node-get-file-in-n8n-problem-bad-request-file-is-too-big/216193.md)) |
| Alojamiento gratis 24 h | **Cloudflare Workers**: 100.000 peticiones/día gratis y base de datos D1 gratis (5 GB). Un bot personal gasta una mínima parte. ([límites](https://developers.cloudflare.com/workers/platform/limits), [precios](https://developers.cloudflare.com/workers/platform/pricing/), [D1](https://developers.cloudflare.com/d1/platform/pricing/)) |
| Velocidad de respuesta a cambios | El bot responde al instante, pero **Claude aplica los cambios en la siguiente pasada de la tarea programada (como mucho, 1 hora)**. No es instantáneo. |
| Coste en Claude | Las pasadas programadas gastan uso de tu plan Claude Pro. Si no hay nada pendiente, la pasada termina enseguida. |
| Subida a YouTube por API | La API oficial es gratuita (cuota por defecto suficiente para nuestro ritmo). **Duda sin resolver:** Google documentaba que los proyectos nuevos sin verificar suben los vídeos **en privado** hasta pasar una auditoría gratuita; páginas más recientes dicen que ya no. Se comprueba con una primera subida de prueba **en privado**. Si sigue la restricción: se pide la auditoría (gratis) y, mientras, el bot te manda el vídeo final y sus datos para programarlo tú desde la app de YouTube Studio (2 min). ([referencia oficial](https://developers.google.com/youtube/v3/docs/videos/insert), [guía de terceros](https://www.upload-post.com/youtube-api/)) |

## Calendario propuesto (Neido Studio)
Ritmo pedido por el usuario: **1 película + 4-5 Shorts por semana** (antes eran 3-4 Shorts).
Horas pensadas para España y Latinoamérica a la vez:

| Día | Qué | Hora España | México (CDMX) | Colombia | Argentina |
|---|---|---|---|---|---|
| Viernes | **Película** | 19:00 | 12:00 | 13:00 | 15:00 |
| Miércoles (víspera) | Short 1: el avance | 20:00 | 13:00 | 14:00 | 16:00 |
| Sábado | Short 2: momento cómico | 20:00 | 13:00 | 14:00 | 16:00 |
| Lunes | Short 3: el "¿pero qué…?" | 20:00 | 13:00 | 14:00 | 16:00 |
| Martes | Short 4: la pregunta | 20:00 | 13:00 | 14:00 | 16:00 |
| Domingo (opcional) | Short 5: extra o de la película anterior | 20:00 | 13:00 | 14:00 | 16:00 |

(Entre finales de marzo y finales de octubre, con el horario de verano de España, la diferencia con Latinoamérica es una hora más.)
Se ajustará con los datos reales de YouTube Studio (cuándo está conectada tu audiencia).

## Lo que necesito de ti (y dónde)
| Qué | Dónde | Notas |
|---|---|---|
| 1. Crear el bot con BotFather | Móvil | Te da una clave (token). **No la escribas en el chat.** |
| 2. Tu ID de Telegram | — | Ya no hace falta: el primero que escribe /start queda como dueño. |
| 3. Cuenta gratis de Cloudflare | PC o móvil | Sin tarjeta. |
| 4. Pegar las claves en Cloudflare (Secrets) | Navegador | Así solo las conoce el bot. |
| 5. Un permiso de Cloudflare para que Claude instale el bot | **PC** (formulario seguro) | |
| 6. Proyecto en Google Cloud + API de YouTube + autorizar tu canal | **PC** | Gratis. Te guío pantalla a pantalla. |
| 7. Permisos de red para esta sesión (Cloudflare, el bot, YouTube) | **PC** | Desde el móvil solo sale "Denegar". |
| 8. Permiso para crear la tarea programada (cada hora) | PC | Se puede pausar o borrar cuando quieras. |

## Cosas que no se pueden deshacer (se preguntan antes)
- Publicar o programar un vídeo público en YouTube. La primera subida será siempre **privada, de prueba**.
- Borrar ideas o pendientes del bot (el bot pedirá confirmación).

## Orden de trabajo
1. Crear el bot (móvil) ← primer paso
2. Cloudflare: cuenta + claves + instalar el bot + probar /start, /idea, /pendientes
3. Envío de un vídeo de prueba con botones
4. Tarea programada de Claude (cambios y aprobaciones)
5. YouTube: proyecto de Google, autorización, subida privada de prueba
6. Calendario y publicación programada

## Archivos
| Archivo | Qué es |
|---|---|
| [bot/worker.js](bot/worker.js) | El bot (Cloudflare Worker): Telegram, botones, /idea, /ideas, /pendientes, /id, API para Claude, token de YouTube |
| [bot/cliente.py](bot/cliente.py) | Lo que usa Claude: enviar a revisión (comprime si pasa de 48 MB), tareas, audios, transcripción, subida a YouTube |
| [bot/PASADA-PROGRAMADA.md](bot/PASADA-PROGRAMADA.md) | Instrucciones de la tarea programada de cada hora (se crea solo con aprobación) |
| [bot/GUIA-INSTALACION.md](bot/GUIA-INSTALACION.md) | Guía de instalación para el usuario |

Pruebas hechas (simulación con base de datos real y Telegram falso): ayuda, ID, solo responde al dueño, ideas, pendientes, envío de vídeo, pedir cambios por texto, versión 2, aprobar, tareas para Claude, clave obligatoria en la API.
