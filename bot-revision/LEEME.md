# Bot de revisión de SHOCK MENTAL (Telegram)

Solo para el canal **Shock Mental**. Neido Studio tendrá su propio bot.

## Cómo funciona

1. El PC monta el vídeo y lo sube a YouTube como **privado** (no se publica).
2. El bot te lo manda al móvil con título, descripción, etiquetas y fecha propuesta, y tres botones:
   **✅ Aprobar · ✏️ Pedir cambios · ❌ Descartar**.
3. ✅ → el bot lo programa en YouTube para su hueco del calendario y te lo confirma.
   ✏️ → le escribes o mandas audios con los cambios y terminas con /listo; el PC los aplica y te manda la versión nueva.
   ❌ → se queda privado y no se publica.
4. Órdenes: `/idea texto`, `/ideas`, `/pendientes`, `/calendario`, `/ayuda`.

El bot vive gratis en **Cloudflare Workers** (24 h, aunque el PC esté apagado). Solo responde a tu ID de Telegram.
El PC solo hace falta para montar vídeos y aplicar cambios.

### Calendario (hora de España)
| Día | Qué | Hora |
|---|---|---|
| Lunes, miércoles | Short sacado de la Dosis | 19:00 |
| Martes, viernes | Ranking top 5 | 19:00 |
| Jueves | Dosis de Asombro (largo) | 18:00 |
| Sábado | Short sacado de la Dosis | 12:00 |

Se cambia en `CALENDARIO`, al principio de `worker.js`.

## Lo que hace el usuario (desde el móvil, una sola vez)

### 1. Crear el bot en Telegram
1. Busca **@BotFather** (con la marca azul ✔️) → **Iniciar** → escribe `/newbot`.
2. Nombre: **Shock Mental · Revisión**. Usuario: **shockmental_revision_bot** (si está cogido, `shockmental_revisar_bot`).
3. Copia el **token** (`123456789:AAH…`) y pégaselo a Claude.
4. Abre el enlace de tu bot y pulsa **Iniciar** (así se sabe tu ID).

### 2. Cuenta gratis de Cloudflare (donde vive el bot)
1. Entra en **dash.cloudflare.com/sign-up**, crea la cuenta con tu correo y confírmala desde el email. No pide tarjeta.
2. En el menú, entra una vez en **Workers y Pages** (así se crea tu dirección `….workers.dev`).
3. Arriba a la derecha, el muñequito → **Perfil** → **Tokens de API** → **Crear token**.
4. Plantilla **«Editar Cloudflare Workers»** → **Usar plantilla** → abajo **Continuar con el resumen** → **Crear token**.
5. Copia el token (solo se enseña una vez) y pégaselo a Claude.

### 3. Google Cloud (para que el bot pueda programar en YouTube)
Con la cuenta que tiene el proyecto **My First Project**:
1. Abre **console.cloud.google.com/apis/library/youtube.googleapis.com** → **Habilitar**.
2. Abre **console.cloud.google.com/auth/overview** → **Comenzar**:
   - Nombre de la app: **Subidas Shock Mental**. Correo: el tuyo.
   - Público: **Externo**. Contacto: tu correo. Acepta y **Crear**.
3. Menú **Público** → **Publicar app** → **Confirmar** (si no, la autorización caduca a los 7 días).
4. Menú **Clientes** → **Crear cliente** → Tipo **App de escritorio** → nombre **PC de casa** → **Crear**.
5. Te enseña el **ID de cliente** y el **Secreto del cliente**: cópialos y pégaselos a Claude.
6. Claude te dará un enlace. Ábrelo en el móvil, elige la cuenta y el canal **Shock Mental**.
   Saldrá «Google no ha verificado esta aplicación»: es tu propia app → **Configuración avanzada** → **Ir a Subidas Shock Mental** → **Continuar**.
7. Al final, la página **no carga** («no se puede acceder a localhost»). Es normal: **copia la dirección entera** de esa página y pégasela a Claude.

### 4. Auditoría de YouTube (más adelante)
Hasta que Google audite el proyecto, todo lo subido por la API queda **privado** aunque esté programado.
A la hora de publicar, el bot te avisa para que lo pongas **Público** con un toque en la app de YouTube.
La auditoría se pide gratis en el formulario «YouTube API Services – Audit and Quota Extension».
Cuando la aprueben, se cambia `AUDITADO = "si"` en `wrangler.toml` y se vuelve a desplegar.

## Lo que hace Claude en el PC

```
# instalar o actualizar el bot (necesita CLOUDFLARE_API_TOKEN en el entorno)
python bot-revision/desplegar.py --telegram-token 123:ABC

# autorizar YouTube desde el móvil
python produccion/herramientas/subir_youtube.py autorizar-movil shockmental            # da el enlace
python produccion/herramientas/subir_youtube.py autorizar-movil shockmental --vuelta "http://localhost:8765/?…"
python bot-revision/desplegar.py --solo-secretos                                         # pasa la autorización al bot

# mandar un vídeo a revisión
python produccion/herramientas/revision.py enviar docs/shockmental/12-ranking06.md --tipo ranking

# ver los cambios pedidos (transcribe los audios con Whisper) y avisar de que se rehace
python produccion/herramientas/revision.py tareas
python produccion/herramientas/revision.py estado ranking06 rehaciendo --nota "🛠️ Aplicando tus cambios…"

# ideas guardadas con /idea
python produccion/herramientas/revision.py ideas [--usar N]
```

Claves y configuración: en `~/.canales-youtube/` del PC (`client_secret.json`, `tokens/shockmental.json`,
`shockmental-bot.json`) y en los secretos de Cloudflare. **Nunca en el repo.**

Coste: 0 €. Cloudflare Workers gratis (100.000 peticiones al día), Telegram gratis, API de YouTube gratis
(10.000 unidades al día; cada subida gasta 1.600), Whisper funciona en el PC.
