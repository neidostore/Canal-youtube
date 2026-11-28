# Shock Mental Autopilot · Fase 2: arquitectura y plan

## Principios
1. **Se reutiliza todo lo que funciona:** `montar.py`, las plantillas, el bot y las búsquedas de fotos con licencia. Nada se reescribe por gusto.
2. **Nada se publica sin tu ✅ en Telegram**, y esa aprobación va ligada a un vídeo y a una **versión** concretos.
3. **La calidad manda sobre la cantidad.** La puntuación tiene «vetos»: si hay un dato sin verificar, un problema de derechos o fallos técnicos, el vídeo queda bloqueado aunque sea potencialmente viral.
4. **Coste controlado:** límites por día y por mes, reintentos limitados y registro de cada gasto.
5. **Las claves nunca van al repositorio,** que es público. Viven en `~/.canales-youtube/`, en variables de entorno o en los secretos de Cloudflare.

## Esquema
```
                 ┌──────────── Telegram (tu centro de control) ────────────┐
                 │  ficha + vídeo + miniatura + botones · /panel · /idea    │
                 └───────────────▲──────────────────────────┬──────────────┘
                                 │                          │ aprobación (id + versión)
                      Cloudflare Worker (24 h, gratis) ── KV
                                 ▲                          │
                 /pc/* (con clave)│                          ▼
┌──────────────────────── PC · `python -m autopilot` (Programador de tareas) ─────────────┐
│ Director ─ cola de tareas (SQLite) ─ límites de coste y reintentos ─ registro            │
│  ├─ Investigador ─► Verificador ─► Guionista (Short / largo) ─► Productor (montar.py)    │
│  ├─ Diseñador (títulos + miniatura con plantilla)  ─► Control de calidad (automático)    │
│  ├─ Publicador (API de YouTube: subir en privado → programar al aprobar)                 │
│  └─ Analista (API de YouTube Analytics → métricas → informe → aprendizaje)               │
│ «Cerebro» (modelo de IA): interfaz única con proveedores intercambiables                 │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

## Piezas nuevas (carpeta `autopilot/`)
| Archivo | Para qué sirve |
|---|---|
| `config.toml` | Calendario, límites de gasto, modo prueba o producción, objetivos. **Se edita sin tocar código** |
| `db.py` | Base SQLite en `~/.canales-youtube/autopilot.db`: ideas, vídeos, versiones, fuentes, tareas, costes, errores, publicaciones y métricas |
| `cerebro.py` | Interfaz del modelo de IA: `generar(prompt, esquema)` con un proveedor configurable |
| `agentes/*.py` | Los 10 agentes. Cada uno lee de la cola, escribe su resultado y deja registro |
| `guion.py` | Formato estándar de guion (JSON) → `escenas.json`. Sustituye a los `crear_*.py` hechos a mano |
| `calidad.py` | Comprobaciones automáticas: duración, cortes de audio, volumen, fotogramas negros, subtítulos, número de fuentes, créditos, duplicados y similitud con vídeos anteriores |
| `puntuacion.py` | Puntuación de 0 a 100 con vetos |
| `__main__.py` | Órdenes: `ciclo`, `estado`, `panel`, `prueba` |

## Calendario inicial (configurable)
- **1 Short al día**: 4 rankings y 3 de curiosidad o historia por semana, más **1 vídeo largo a la semana**.
- La cadencia solo sube a 2 Shorts al día si se cumplen tres condiciones durante 2 semanas: la retención de los Shorts no baja, la cola tiene al menos 5 vídeos aprobados y el control de calidad deja pasar más del 80 % a la primera.
- **Motivo:** las políticas de monetización castigan el contenido repetitivo o producido en masa, y tu canal ya funciona con 1 vídeo al día.

## Puntuación (0-100) con vetos
| Criterio | Peso | Cómo se mide |
|---|---|---|
| Interés potencial | 15 | Tema parecido a tus mejores vídeos y tendencias actuales |
| Originalidad | 10 | Similitud con tus vídeos anteriores (menos es mejor) |
| Gancho | 15 | Dato con cifra o imagen en los 2 primeros segundos y menos de 20 palabras |
| Retención potencial | 15 | Duración adecuada (Shorts ≤ 60 s), cambio de plano cada ≤ 3 s, giro final |
| Valor para el espectador | 10 | Datos concretos y comprobados frente a relleno |
| Verificabilidad | 15 | Cada cifra con al menos 1 fuente fiable (2 si es dudosa) |
| Calidad audiovisual | 10 | Comprobaciones técnicas superadas |
| Conversión a suscriptor | 10 | Llamada a la acción, serie o continuación posible |

**Vetos (bloquean aunque la nota sea alta):** un dato sin fuente · una foto sin licencia o una imagen de un meme con copyright · caras de personas reales hechas con IA · cortes de audio · un vídeo casi idéntico a otro anterior · un título que promete algo que el vídeo no enseña.

## Fases
| Fase | Qué incluye | Depende de |
|---|---|---|
| 3 | Base de datos, cola, configuración, límites, interfaz del cerebro, los 10 agentes y el flujo | Elegir el cerebro |
| 4 | Ampliar el bot: botones nuevos (ver guion, ver fuentes, cambiar fecha), ficha completa, `/panel` | — |
| 5 | Shorts automáticos de principio a fin (de la idea al vídeo en Telegram) | 3 y 4 |
| 6 | Vídeos largos automáticos | 5 |
| 7 | Subida y programación en YouTube | **Tu configuración de Google Cloud (OAuth)** |
| 8 | Analítica y aprendizaje | OAuth (Analytics, solo lectura) |
| 9 | Pruebas completas y documentación | Todo lo anterior |
