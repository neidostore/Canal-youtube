# Neido Studio · Análisis inicial y Fase 1 (marca)

> Estado: **Fase 1 en curso**. Ninguna decisión está aprobada todavía.
> El prompt original del proyecto está en [00-prompt-original.md](00-prompt-original.md).

---

## 1. Qué canal estamos construyendo (en una frase)

**Una antología de cortometrajes de ficción en la que cada película parte de una situación imposible y la trata en serio, como si fuera una superproducción.**

El formato antología ya existe en la televisión (*La dimensión desconocida*, *Black Mirror*, *Love, Death & Robots*). Lo nuevo es hacerlo en español, con IA, con humor y choque cultural, y en un formato de YouTube.

---

## 2. Puntos fuertes

1. **La premisa se vende sola.** "Un colombiano aparece en el Titanic" se entiende en un segundo y despierta curiosidad. Eso es oro para títulos y miniaturas.
2. **El pez fuera del agua es un motor narrativo probado.** El contraste genera comedia, tensión y emoción a la vez.
3. **Los acentos del mundo hispano son un diferenciador real.** Colombianos, andaluces, mexicanos, argentinos, cubanos o gallegos, en épocas y mundos imposibles. Casi nadie lo explota en ficción con IA.
4. **La IA abarata justo lo más caro del cine:** escenarios, épocas y vestuario. Un barco de 1912 cuesta lo mismo que una cocina.
5. **Los Shorts salen solos.** Cada película tiene 3-5 momentos recortables (el gancho, la frase graciosa, el giro).
6. **Cada vídeo funciona por sí mismo.** Cualquiera puede entrar al canal por cualquier película.

---

## 3. Problemas reales (sin maquillar)

### 3.1 El mayor: 0 € frente a 6-10 minutos de cine con labios sincronizados
Una cuenta rápida:
- 8 minutos son 480 segundos.
- Los clips de IA suelen durar entre 5 y 10 segundos, y en cine un plano medio dura 3-5 segundos. Eso son **unos 100 planos por película**.
- La IA falla mucho: para conseguir un plano bueno suele hacer falta generar 2-4 intentos. Eso son **200-400 generaciones por película**.
- Los planes gratuitos dan, en general, **pocas generaciones al día**, con frecuencia **con marca de agua** y a veces **sin permiso de uso comercial**. Las cifras exactas las comprobaremos herramienta por herramienta en la Fase 3; no las doy aquí de memoria.

**Conclusión honesta:** dos películas de 6-10 minutos por semana a 0 € **no es realista**. Hay que diseñar el formato alrededor del presupuesto (ver punto 5), no al revés.

### 3.2 Sincronización labial
Es lo más caro y lo que peor sale en los planes gratuitos. Una película con mucho diálogo a cámara multiplica el coste y el riesgo de "efecto muñeco".

### 3.3 Continuidad
Sigue siendo el punto débil de la IA de vídeo. Se puede controlar mucho con referencias y fichas, pero no al 100 %. Hay que escribir los guiones pensando en ello.

### 3.4 Tu ordenador
La Radeon HD 6450 no sirve para generar IA en local, y probablemente tampoco para mover **DaVinci Resolve** con soltura (Resolve exige una GPU bastante más moderna). Esto lo comprobaremos en la Fase 3, pero hay que contar con montar en algo ligero (CapCut, Shotcut, Kdenlive) o en el móvil. Toda la generación será online.

### 3.5 Políticas de YouTube
- YouTube no monetiza el **"contenido no auténtico"**: vídeos en serie, repetitivos o producidos en masa. Historias originales con guion propio y trabajo creativo real sí son monetizables, pero el canal debe dejarlo claro (guiones originales, montaje propio, nada de plantillas repetidas).
- El contenido sintético **realista** debe marcarse con la etiqueta de IA en YouTube Studio. No penaliza, pero hay que hacerlo.
- **Personas reales:** no podemos poner en boca de personas reales (vivas o recientes) cosas que no dijeron, ni recrear víctimas reales de forma frívola. En el Titanic, el protagonista y los pasajeros con los que habla serán **personajes inventados** dentro de un hecho real.

### 3.6 "Aquí puede pasar cualquier cosa" es también un riesgo
Si cada vídeo es de un género distinto, el espectador no sabe qué promete el canal y **no tiene motivo para suscribirse**. Necesitamos **una regla fija** que una todas las películas, aunque cambien el género, la época y los personajes (ver 4.1).

---

## 4. Mejoras propuestas para hacerlo más original y reconocible

### 4.1 La regla de la anomalía (la promesa de marca)
**Cada película tiene un único elemento imposible: alguien o algo que no debería estar ahí.** Todo lo demás es realista y se trata en serio.
- Un colombiano en el Titanic.
- Una abuela gallega en la primera misión a Marte.
- Un móvil con un 3 % de batería en la batalla de las Termópilas.

La variedad está en el género; la constante es la anomalía. El espectador sabe qué va a recibir (el "¿pero qué estoy viendo?") sin saber qué historia le toca.

### 4.2 Películas numeradas, como expedientes
"Anomalía Nº 001", "Nº 002"... Da sensación de colección y de universo, y el número aparece igual en todas las miniaturas y en la cortinilla.

### 4.3 Un easter egg que se repite en todas las películas
Un objeto o un personaje secundario misterioso (por ejemplo, un reloj de bolsillo parado siempre a la misma hora, o un mismo desconocido que mira a cámara) aparece escondido en todas las películas, en cualquier época.
- No obliga a hacer segundas partes.
- Hace que la gente lo busque y lo comente ("¿lo habéis visto en el minuto 4?"), lo cual ayuda al algoritmo.
- Con el tiempo crea una "mitología" del canal muy barata de producir.

### 4.4 Escribir para lo que la IA hace bien
La técnica que más calidad da a coste cero no es una herramienta, es **el guion**:
- **Pensamientos en off del protagonista** en lugar de diálogo a cámara: no necesitan lip-sync.
- **Diálogos rodados como en el cine:** plano por encima del hombro, de espaldas, de perfil o con el que escucha en pantalla. En el cine real gran parte del diálogo se ve así. Reservamos el lip-sync para 3-6 frases clave por película.
- **POV** (primera persona): espectacular y sin cara que mantener.
- **Planos cortos** (2-4 s): la IA falla menos y el ritmo mejora.

### 4.5 Un "acabado de cine" común
Formato panorámico con bandas negras (2,39:1), el mismo etalonaje (LUT) y el mismo grano de película en todos los planos. Unifica clips de herramientas distintas y esconde defectos. Junto con un buen diseño de sonido, es la mitad de la sensación de "película".

### 4.6 Empezar más corto
Primero películas de **3-5 minutos**. Es más fácil retener a la gente y cuesta la mitad de generar. Cuando el sistema funcione, subimos a 8-10 minutos (a partir de 8 minutos YouTube permite anuncios a mitad del vídeo, pero eso solo importa cuando el canal ya esté monetizado).

---

## 5. Cómo conseguir calidad de cine con presupuesto cero

1. **Imagen primero, vídeo después.** Generamos los fotogramas clave de cada plano en herramientas de imagen gratuitas, con las referencias de los personajes. Solo animamos los planos que necesitan movimiento. Las imágenes gastan muchos menos créditos que el vídeo.
2. **Repartir el trabajo entre varias herramientas gratuitas** según lo que hace mejor cada una, aprovechando los créditos diarios que se recargan.
3. **Fichas de continuidad obligatorias** antes de generar nada (personajes, escenarios, vestuario, luz).
4. **Sonido de cine:** ambientes, efectos y música de bibliotecas gratuitas con licencia clara (por ejemplo, la Biblioteca de audio de YouTube). El sonido es lo que más "vende" que algo es una película.
5. **Claude hace todo el trabajo de escritorio:** guiones, guiones técnicos, listas de planos, prompts, fichas y revisión.
6. **Frecuencia realista** al principio: **1 película cada 1-2 semanas y 3-4 Shorts**. Ajustaremos cuando sepamos cuánto tarda de verdad una película.
7. **Punto de decisión honesto:** si en la prueba técnica las herramientas gratuitas no dan la calidad mínima, te lo diré y valoraremos opciones (una sola suscripción barata cuando haya ingresos, o reducir la duración).

---

## 6. Fases de trabajo (ajustadas)

| Fase | Contenido | Cambio que propongo |
|---|---|---|
| 1. Marca | Nombre, personalidad, identidad visual, dirección artística | — |
| 2. Formato | Estructura, duración, planos, diálogo, narración, ritmo, finales | Incluir la regla de la anomalía y el easter egg |
| 3. Producción | Herramientas gratuitas comprobadas, flujo, continuidad, voces, lip-sync, montaje | **Terminar con una prueba técnica de 30-60 s** antes de seguir. Si la calidad no llega, lo sabremos aquí y no en la semana 5 |
| 4. Guionización | Plantilla de historia, fichas, guion técnico, prompts | — |
| 5. Primera película | Historia, guion, diseño, planos, generación, montaje, revisión | — |
| 6. Lanzamiento y mejora | Título, miniatura, publicación, retención, mejoras | — |

---

## 7. Fase 1 · Nombre del canal

### ✅ DECISIÓN: **NEIDO STUDIO**
- Propuesto por el usuario y aprobado. `@neidostudio` comprobado como libre en YouTube por el usuario.
- Lema: **"Películas imposibles"** (aprobado, ver sección 8).
- Uso: *Neido Studio presenta · Película Nº 001 · [título]*.
- Por qué funciona: "Studio" convierte el canal en una productora de cine; nombre inventado y propio (fácil de posicionar); no encasilla en un género.
- Riesgos y solución: no explica el concepto (lo hace el lema + la regla de la anomalía); un "estudio" puede sonar frío (lo compensa un sello muy reconocible: cortinilla, numeración, easter egg).

### Historial de la búsqueda de nombre

### Criterios
- Corto, fácil de pronunciar y de escribir (también sin tilde en el @).
- No limitado a un género.
- Que transmita "algo que no debería estar ahí" o "mundos que se cruzan".
- Que funcione como logo pequeño (marca de agua) y como sello en las miniaturas.
- Mejor si se entiende también en inglés, por si algún día hay doblaje.

### Propuestas analizadas

| Nombre | A favor | En contra | Valoración |
|---|---|---|---|
| ~~ANOMALÍA~~ | Encajaba con la regla de la marca | **Ya está cogido en YouTube** (comprobado por el usuario) | Descartada |
| **CINE IMPOSIBLE** | Dice exactamente lo que es el canal. Muy claro para el que llega por primera vez | Suena más a etiqueta que a marca. Recuerda a *Misión imposible* | Mejor como lema que como nombre |
| **ERRATA** | Elegante y original: "un error en la historia del mundo". Corto, funciona en varios idiomas | Mucha gente no conoce la palabra. Explicarla cuesta | Buena, pero arriesgada |
| **DESFASE** | Doble sentido en España ("¡qué desfase!" + desfase temporal) | En Latinoamérica pierde el doble sentido. Ya existe un colectivo de cine peruano llamado Desfase Films | Descartada |
| **LA GRIETA** | Evoca el portal entre mundos | En Argentina "la grieta" es la polarización política: connotación negativa en un mercado clave | Descartada |
| **VÓRTICE / PARADOJA** | Suenan potentes | Encasillan en ciencia ficción | Descartadas |

### Segunda ronda (tras descartar Anomalía)
Lección de la primera ronda: las palabras sueltas y comunes ya suelen estar cogidas. Funcionan mejor las combinaciones de dos palabras o los nombres con un concepto propio.

| Nombre | A favor | En contra | Valoración |
|---|---|---|---|
| **MIL PUERTAS** | Cada película es una puerta a otro mundo, y conecta con el portal de la imagen de referencia. Permite numerar: "Puerta Nº 001". Logo sencillo (una puerta con luz). Fácil de decir en todo el mundo hispano. Combinación poco común, más fácil de registrar | No se traduce tan bien al inglés (*A Thousand Doors*). Puede sonar algo a fantasía si la identidad visual no es adulta | ⭐ Recomendada |
| **QUIMERA** | Una quimera es un ser hecho de varios animales, como el canal mezcla géneros. También significa "sueño imposible". Funciona en inglés (*Chimera*) | Palabra común: hay muchas películas y una serie corta llamada así. Mismo riesgo que Anomalía | Buena, pero probablemente cogida |
| **INTRUSO** | Cada película tiene un intruso (el elemento imposible). "Intruso Nº 001" | Suena a thriller o terror; encasilla | Regular |
| **INSÓLITO** | Es exactamente el "¿qué estoy viendo?" | Suena a canal de curiosidades ("lo más insólito"), justo lo que no queremos ser | Descartada |
| **FUERA DE LUGAR** | Describe la regla de la anomalía | Largo, suena a programa de tertulia, flojo como logo | Descartada |

### Recomendación
**MIL PUERTAS** como nombre y **"Películas imposibles"** como lema.
- Canal: **Mil Puertas · Películas imposibles**
- Cada película es una "Puerta": *Puerta Nº 001 · El colombiano del Titanic*.
- @ posibles: `@milpuertas`, `@milpuertasfilms`, `@milpuertas.cine`
- La regla de la anomalía se mantiene: detrás de cada puerta hay algo que no debería estar ahí.

### Comprobación de disponibilidad (hasta donde he podido)
- Primera ronda: búsquedas web de "Anomalía Films", "Cine Imposible", "Errata Films", "Grieta Films" y "Desfase Films". El usuario confirmó después que Anomalía está cogido.
- Segunda ronda: búsquedas web de "Mil Puertas", "Quimera Films/Cine", "Insólito Films" y "Fuera de Lugar". **No aparece ningún canal de YouTube con esos nombres**, pero la búsqueda web no indexa todos los canales. Para Quimera aparecen varias películas y una serie corta llamada "Canal Quimera".
- **Desde este entorno no puedo abrir youtube.com**, así que no puedo confirmar si los @ están libres. Eso lo tienes que comprobar tú (son 2 minutos, te lo explico cuando elijamos nombre).

---

## 8. Personalidad de la marca

### ✅ DECISIÓN: tono C, equilibrado
**"Serios en la forma, gamberros en la premisa."** Producción de superproducción (imagen, sonido e interpretación creíbles); lo absurdo está en la situación, no en la forma de contarla. Cada película se inclina hacia lo épico o hacia la comedia según su historia.

### Principios propuestos (sin objeciones del usuario de momento)
1. **Reírnos con las culturas, nunca de ellas.** Acentos y expresiones con cariño; nada de estereotipos fáciles. El personaje "fuera de lugar" suele ser el más listo de la escena, no el payaso.
2. **Vender la historia, no la IA.** Sin "hecho con IA" como reclamo en títulos ni miniaturas. Se declara donde YouTube lo exige (etiqueta de contenido sintético).
3. **El público participa.** Encuestas en la pestaña Comunidad para elegir anomalías ("¿a quién metemos en la Antigua Roma?").
4. **Un sello inmutable:** cortinilla "Neido Studio presenta", número de película, easter egg escondido en todas.

### ✅ DECISIÓN: lema
**"Películas imposibles"** → marca completa: **Neido Studio · Películas imposibles**.
Frase secundaria opcional para la descripción del canal: *"Lo imposible, en serio."*

---

## 9. Pendiente en la Fase 1 (en este orden)
1. ✅ Análisis del concepto.
2. ✅ Nombre: **Neido Studio** (descartados por el camino: Anomalía, cogido; Mil Puertas y Gaves TV, no convencieron).
3. ⏳ Reservar `@neidostudio` en YouTube, TikTok e Instagram (lo hace el usuario).
4. ✅ Personalidad de la marca: tono C (equilibrado) y lema "Películas imposibles".
5. ⏳ **Identidad visual** ← estamos aquí.
   - ✅ Dirección: **C, la grieta de luz** (rendija de luz cálida/fría; negro, ámbar-dorado y cian-violeta). Bocetos en `marca/bocetos/`.
   - ✅ **Foto de perfil definitiva:** puerta entreabierta generada con Gemini, con recorte más cerrado → `marca/final/perfil.jpg`. Probada en círculo a 160, 88 y 40 px.
   - 💡 **Cortinilla (idea del usuario, aprobada como concepto):** la "I" de NEIDO es una puerta; se abre, la luz inunda la pantalla y de dentro sale el primer plano de la película. 3-4 s, personalizada en cada película. Va **después del gancho**, no al principio. Se hará con fotogramas clave en el editor (no con IA de vídeo, para que el texto no se deforme). Se define en Fase 2 (formato) y Fase 3 (montaje).
   - ✅ **Logo definitivo:** NEIDO en serifa (Cormorant Garamond) con la I como entrada de luz de una puerta (rendija vertical + luz por arriba y por abajo + reflejo en el suelo), STUDIO y PELÍCULAS IMPOSIBLES en Montserrat. Capas separadas para animar la cortinilla → `marca/final/logo.html` / `logo.png`.
   - ✅ Banner: **versión con escenas** (pasado cálido a la izquierda, futuro frío a la derecha, logo en la frontera con la I-puerta en la línea que separa ambos mundos). ⏳ Falta el fondo de Gemini (el v1 tiene una franja oscura; se montó esquivándola, ver línea siguiente).
   - ✅ Banner montado sobre el fondo v1 de Gemini → `marca/final/banner.png` (mejorable más adelante con un fondo nuevo).
   - ✅ **Marca de agua:** la I-puerta sola sobre un disco oscuro semitransparente, PNG 300×300 transparente → `marca/final/marca-agua.png`.
   - ✅ Dirección artística aprobada → [02-direccion-artistica.md](02-direccion-artistica.md).
   - ⏳ Plantilla de miniatura: se cierra con la primera película.

## ✅ FASE 1 CERRADA. Siguiente: Fase 2, formato de las películas → [03-fase-2-formato.md](03-fase-2-formato.md)

Prompts de Gemini en `marca/prompts-gemini.md`. Imagen de referencia del usuario en `marca/imagen-referencia.jpg`.
