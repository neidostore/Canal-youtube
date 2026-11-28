# Shock Mental como empresa · estructura, CEO y distribución

## Organigrama (sin agentes redundantes)
| Puesto | Quién | Qué hace (y dónde está en el código) |
|---|---|---|
| **Gerente general** | Tú | Apruebas el contenido (Telegram), los gastos, los cambios importantes y la estrategia |
| **CEO** (director general de IA) | `director.py` + `ceo.py` | Planificación diaria y semanal, cola, prioridades, coordinación, límites de coste, vigilancia (atascos, fallos, cola baja), registro de decisiones e informes |
| Contenido | Investigador · Verificador · Guionista de Shorts · Guionista de largos | `agentes/*.md`. El cerebro es la tarea programada de Claude. Los títulos y el posicionamiento los hacen los guionistas, no un agente aparte |
| Producción | Productor (`montar.py`) · Thumbnail Director (`miniaturas.py`) · Voice Director (`voz.py`) · Calidad (`calidad.py`) | |
| Distribución | Responsable de YouTube (`youtube.py`) · Responsable de TikTok (`tiktok.py` + `distribucion.py`) · Community Manager (`agentes/community.md`, solo borradores) | |
| Analítica | Analista único: YouTube, más TikTok cuando haya permiso de métricas, más crecimiento y monetización | `youtube.analizar`, `panel.py`, `ceo.informe` |

**Unificados** para no duplicar:
- Coordinador de tareas y planificación → dentro del CEO.
- Títulos y posicionamiento → en los guionistas.
- Analista de TikTok y responsable de crecimiento → en el analista.

**Agentes nuevos:** el CEO puede proponerlos en el informe semanal (problema, responsabilidades, coste y utilidad), pero no los crea sin tu aprobación.

## Lo que el CEO puede y no puede hacer
- **Puede:** encargar tareas, producir, rechazar por calidad, reintentar dentro de los límites, distribuir **lo que tú aprobaste**, analizar e informar.
- **No puede** (bloqueado en el código):
  - gastar por encima de `config.limites`;
  - publicar sin tu ✅ de esa versión;
  - borrar contenido;
  - tocar contraseñas o permisos;
  - cambiar la identidad del canal;
  - responder comentarios sin tu botón.

  Todo eso queda en `decisiones` como «requiere gerente» y te llega en el informe.

## Distribución YouTube + TikTok con una sola aprobación
1. Pulsas ✅ **APROBAR Y PUBLICAR** (vale para esa versión y para las dos plataformas).
2. YouTube: se sube en privado con hora de publicación (`publishAt`), y YouTube lo publica a la hora exacta.
3. TikTok: la API **no permite programar**. Cada 10 minutos el PC mira si ha llegado la hora y lo sube. Se registra la diferencia real con YouTube, normalmente menos de 10 minutos. **No es simultáneo al segundo.**
4. Cada plataforma tiene su propia fila en `publicaciones`. Si TikTok falla, solo se reintenta TikTok (máximo 3 veces) y nunca se vuelve a subir a YouTube. Si la versión cambió después de tu ✅, TikTok se cancela.
5. Te llega el resultado de cada plataforma, con el enlace y la diferencia de minutos.

## Limitaciones reales de las APIs (docs oficiales, 28-nov-2026)
| Función | YouTube | TikTok |
|---|---|---|
| Subir | ✅ API Data v3 | ✅ Content Posting API |
| Programar la hora | ✅ `publishAt` | ❌ No existe: el PC publica a la hora |
| Público sin auditoría | ❌ Queda privado hasta que se audita el proyecto de Google (te aviso a la hora para que lo pongas público con un toque) | ❌ Direct Post solo en privado (SELF_ONLY) y con la cuenta privada. **Alternativa por defecto: modo «borradores»**: llega a tu bandeja de TikTok y lo publicas con 2 toques. Sin auditoría y con la cuenta pública |
| Portada | Shorts: no por API; eliges el fotograma en la app. Largos: ✅ `thumbnails.set` (el canal tiene que estar verificado) | Se elige en la app |
| Métricas | ✅ YouTube Analytics | Necesita otro permiso (`video.list`, etc.). Se añadirá cuando conectes la cuenta |
| Límites | Cuota diaria de la API | 6 peticiones por minuto y token; unos 15 posts al día por cuenta (Direct Post); máximo 5 borradores pendientes en 24 h |
