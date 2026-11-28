# Shock Mental Autopilot · cómo funciona

## Cada día, sin que hagas nada
| Hora | Quién | Qué hace |
|---|---|---|
| 9:00 y 17:00 | Tarea programada de Claude (app de escritorio, «Scheduled») | Ciclo → investiga ideas → escribe guiones → verifica cada dato → corrige → ciclo (produce, control de calidad, envía a Telegram) |
| Cada 2 h desde las 10:00 | Programador de tareas de Windows (`ShockMental-Autopilot-Ciclo`) | Recoge tus ✅, cambios y rechazos; sube y programa lo aprobado (en modo producción); analiza las métricas una vez al día; actualiza `/panel` |

**Requisitos:** el PC encendido y la app de Claude abierta a las 9:00 y a las 17:00. Si está apagado, la tarea se ejecuta al abrir la app.

## Lo que haces tú (Telegram)
Cada vídeo llega con su portada o miniatura, el vídeo y la ficha (título, tipo, duración, nota de calidad, fecha, coste, descripción y avisos).
- ✅ **Aprobar y programar.** Vale solo para esa versión.
- ✏️ **Solicitar cambios**, por texto o por audio, y `/listo` al terminar. Los agentes hacen la versión siguiente.
- ❌ **Rechazar.** Se te pide el motivo, que queda como «lección» para los agentes.
- 📜 Ver guion · 📚 Ver fuentes · 📅 Cambiar fecha.
- `/panel` (objetivos y monetización) · `/idea texto` · `/pendientes` · `/calendario`.

## Flujo de un vídeo
idea → guion (guionista) → verificación (cualquier dato dudoso vuelve al corrector) → producción (`montar.py`) → control de calidad (vetos + nota de 70 o más) → Telegram → tu ✅ → subida en privado y programación → métricas → lecciones.

## Seguridad
- **Nada se publica sin tu ✅,** ligado al vídeo y a su versión. Hay pruebas automáticas que lo comprueban.
- **Modo prueba** (`autopilot/config.toml` → `modo = "prueba"`): no se sube nada a YouTube. Para empezar a publicar de verdad, cámbialo a `"produccion"` (te lo pediré antes).
- Límites: gasto de 1 € al día y 10 € al mes en APIs de pago (hoy todo es gratis), 2 reintentos por tarea, 4 vídeos al día y 4 versiones por vídeo. El ciclo lleva un candado para que no se ejecute dos veces a la vez.
- Las claves están solo en `~/.canales-youtube/`, en el entorno del usuario y en los secretos de Cloudflare. **El repositorio es público.**
- Registro de todo: tabla `registro` de `~/.canales-youtube/autopilot.db` y `~/.canales-youtube/ciclo.log`.
- Copia de seguridad de la configuración: `config.toml` está en git. La base de datos se copia con `copy %USERPROFILE%\.canales-youtube\autopilot.db <destino>`.

## Órdenes (PC)
```
python -m autopilot ciclo | panel | idea "tema" [--formato largo] | probar guion.json | enviar ID
python -m autopilot cerebro siguiente | entregar ID archivo.json | liberar
python -m autopilot.pruebas.test_flujo        # 17 comprobaciones del flujo
node bot-revision/prueba_worker.mjs           # 26 comprobaciones del bot
```
