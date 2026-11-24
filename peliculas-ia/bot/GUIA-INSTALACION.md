# Instalar el bot de revisión de Neido Studio (paso a paso, en español)

Tiempo total: unos 20 minutos. Se puede hacer desde el móvil; con el PC es más cómodo pegar el código (paso 2.6).
Si en algún paso un botón no se llama igual o te pierdes, haz una captura y mándamela.

⚠️ **Regla de oro:** las claves (el token de BotFather y las palabras secretas) **nunca se escriben en el chat con Claude**. Solo se pegan en BotFather (lo da él) y en Cloudflare.

---

## PASO 1 · Crear el bot en Telegram (móvil, 3 minutos)
1. Abre Telegram y busca **@BotFather** (tiene una insignia azul de verificado).
2. Pulsa **Iniciar** y escribe: `/newbot`
3. Te pide el **nombre** (el que se ve en los chats). Escribe:
   `Neido Studio · Revisión`
4. Te pide el **nombre de usuario** (único y tiene que acabar en "bot"). Prueba en este orden hasta que uno esté libre:
   `NeidoStudioRevisionBot` → `NeidoStudio_Revision_bot` → `NeidoRevisionBot`
5. BotFather te responde con un mensaje que contiene el **token**: una línea parecida a `1234567890:AAH...`.
   **Cópialo en una nota privada del móvil.** No lo mandes a nadie.
6. (Opcional) Ponle la foto del canal: escribe `/setuserpic`, elige el bot y envía la imagen `perfil.jpg` que te mandé.

## PASO 2 · Cloudflare (navegador, 15 minutos)
1. Entra en **dash.cloudflare.com/sign-up** y crea una cuenta gratuita (correo y contraseña). Confirma el correo. No pide tarjeta.
2. En el menú de la izquierda entra en **Compute (Workers)** → **Workers & Pages** → botón **Create** → **Create Worker** (o "Start with Hello World").
   - Nombre: `neido-bot` → **Deploy**.
   - Te dará una dirección como `https://neido-bot.TU-NOMBRE.workers.dev`. **Apúntala** (esta sí me la puedes decir, no es secreta).
3. Crea la base de datos: menú **Storage & Databases** → **D1 SQL Database** → **Create** → nombre `neido-bot-db` → **Create**.
4. Enlázala al bot: vuelve a **Workers & Pages** → `neido-bot` → pestaña **Bindings** (o **Settings → Bindings**) → **Add binding** → **D1 database**:
   - Variable name: `DB`
   - D1 database: `neido-bot-db`
   - **Add / Save**.
5. Las claves: en `neido-bot` → **Settings** → **Variables and Secrets** → **Add**. Para cada una elige el tipo **Secret**:
   | Nombre | Valor |
   |---|---|
   | `TELEGRAM_TOKEN` | el token de BotFather (paso 1.5) |
   | `WEBHOOK_SECRET` | invéntate una palabra de 20 letras y números, sin espacios (ej.: `PuertaLuz2026Neido4x9`) |
   | `CLAUDE_KEY` | invéntate **otra** palabra distinta, también de 20 letras y números |
   Guarda las dos palabras inventadas en tu nota privada. **`OWNER_ID` todavía no**: va en el paso 3.
6. El código: en `neido-bot` → botón **Edit code** (arriba a la derecha) → borra todo lo que hay → pega el contenido completo del archivo `worker.js` que te mandé → **Deploy**.
7. Activa el bot: abre en el navegador esta dirección, cambiando las dos partes en mayúsculas:
   `https://neido-bot.TU-NOMBRE.workers.dev/instalar?clave=TU_WEBHOOK_SECRET`
   Debe salir: `Webhook: OK` y `Comandos: OK`.

## PASO 3 · Que el bot solo te responda a ti (2 minutos)
1. En Telegram abre tu bot nuevo y escribe `/start`.
2. Te contestará: **"Tu ID de Telegram es: 123456789"**.
3. En Cloudflare → `neido-bot` → **Settings → Variables and Secrets → Add** → Secret:
   - Nombre: `OWNER_ID`
   - Valor: ese número
4. Vuelve a Telegram y escribe `/start` otra vez: ahora te sale la ayuda del bot. Prueba:
   - `/idea Un vikingo despierta en un centro comercial`
   - `/ideas`
   - `/pendientes`
   A partir de ahora, si otra persona le escribe al bot, no le contestará nada.

## PASO 4 · Conectar a Claude con el bot (desde el PC, 2 minutos)
1. Dime la dirección del bot (`https://neido-bot.TU-NOMBRE.workers.dev`).
2. Te aparecerá un **formulario seguro**: pega ahí tu `CLAUDE_KEY`. Desde el móvil no funciona (solo sale "Denegar"); hazlo con esta sesión abierta en el PC (claude.ai/code).
3. Te mando un vídeo de prueba al bot para comprobar los botones.

## PASO 5 · YouTube (más adelante, desde el PC)
Lo haremos cuando lo anterior funcione: proyecto gratuito en Google Cloud, activar la API de YouTube y autorizar tu canal. Te guiaré pantalla a pantalla.
