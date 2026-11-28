# Conectar TikTok (cuando llegue el primer Short real que publicar)

Te lo pediré yo en ese momento por Telegram. No hace falta hacerlo antes.

1. Entra en https://developers.tiktok.com con la cuenta de TikTok de Shock Mental y crea una app («Manage apps → Connect an app»). Nombre: `Shock Mental Autopilot`.
2. Añade los productos **Login Kit** y **Content Posting API**. Permisos (scopes): `user.info.basic` y `video.upload` (y `video.publish` solo si un día pasamos la auditoría).
3. Redirect URI: `https://shockmental-revision.neidostore.workers.dev/tiktok/callback`
4. Copia el **Client key** y el **Client secret**. Yo te daré un comando para guardarlos en `~/.canales-youtube/tiktok.json` sin que pasen por el chat ni por Telegram.
5. Ejecuto `python -m autopilot tiktok conectar` → te mando un enlace **oficial de TikTok** → entras y pulsas **Autorizar**.
6. El bot recibe la autorización y el PC la termina. A partir de ahí se recuerda la cuenta y no te la vuelvo a pedir. Si caduca (180 días sin uso), te aviso para reconectar.

**Nunca me des tu contraseña de TikTok.** La app solo recibe permiso para subir vídeos, y puedes retirarlo cuando quieras desde TikTok.
