# Conectar YouTube (Google Cloud · OAuth) · lo haces tú, unos 15 minutos

Es mejor hacerlo **en el PC**, con la cuenta de Google que es dueña del canal Shock Mental.

## Paso 1 · Activar las dos APIs
1. Entra en https://console.cloud.google.com
2. Arriba, en el selector de proyecto, elige el mismo proyecto donde está la clave de la voz (Text-to-Speech).
3. Ve a ☰ → **APIs y servicios** → **Biblioteca**.
4. Busca **YouTube Data API v3** → **Habilitar**.
5. Vuelve a la Biblioteca, busca **YouTube Analytics API** → **Habilitar**.

## Paso 2 · Pantalla de consentimiento
1. Ve a ☰ → **APIs y servicios** → **Pantalla de consentimiento de OAuth** (puede llamarse «Google Auth Platform»).
2. **Información de la app:** nombre `Shock Mental Autopilot` y tu correo como correo de asistencia.
3. **Público:** **Externo**.
4. **Información de contacto:** tu correo.
5. Acepta y pulsa **Crear**.
6. En **Público**, pulsa **Publicar la app** y confirma, para que pase a «En producción».
   - Es importante: en modo «Prueba», la autorización caduca cada 7 días.
   - No hace falta verificar nada. Al autorizar verás «Google no ha verificado esta app». Es normal porque la app es tuya: pulsa **Configuración avanzada → Ir a Shock Mental Autopilot**.

## Paso 3 · Crear el cliente
1. Ve a **Clientes** (o **Credenciales → Crear credenciales → ID de cliente de OAuth**).
2. Tipo de aplicación: **App de escritorio**. Nombre: `autopilot-pc`.
3. Pulsa **Crear**, y en la ventana que sale, **Descargar JSON**.
4. Deja el archivo descargado en la carpeta **Descargas** del PC. **No lo pegues en el chat:** yo lo muevo a la carpeta segura `~/.canales-youtube/client_secret.json`.

## Paso 4 · Avísame
Cuando el JSON esté en Descargas, dime «hecho». Entonces:
1. Te paso un enlace para autorizar el canal (un clic en tu cuenta).
2. Guardo la autorización y se la paso al bot de Telegram sin que aparezca en ningún sitio.
3. Pruebo a leer las estadísticas del canal para confirmar que funciona.

## Después: la auditoría de Google (más adelante)
Mientras Google no audite el proyecto, los vídeos subidos por la API se quedan en **privado**. El bot te avisará a la hora de publicar para que los pongas en público con un toque. La auditoría se pide con un formulario y te ayudaré con él.
