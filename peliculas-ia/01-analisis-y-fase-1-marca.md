# Canal de mini películas con IA · Análisis inicial y Fase 1 (marca)

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

### Criterios
- Corto, fácil de pronunciar y de escribir (también sin tilde en el @).
- No limitado a un género.
- Que transmita "algo que no debería estar ahí" o "mundos que se cruzan".
- Que funcione como logo pequeño (marca de agua) y como sello en las miniaturas.
- Mejor si se entiende también en inglés, por si algún día hay doblaje.

### Propuestas analizadas

| Nombre | A favor | En contra | Valoración |
|---|---|---|---|
| **ANOMALÍA** | Encaja con la regla de la marca. Se entiende igual en inglés (*Anomaly*). Permite "Anomalía Nº 001". Suena a cine | Es una palabra común (hay una película de 2019 con ese título), así que costará posicionar el nombre solo; necesitará apellido en el @ | ⭐ Mi favorita |
| **CINE IMPOSIBLE** | Dice exactamente lo que es el canal. Muy claro para el que llega por primera vez | Suena más a etiqueta que a marca. Recuerda a *Misión imposible* | Mejor como lema que como nombre |
| **ERRATA** | Elegante y original: "un error en la historia del mundo". Corto, funciona en varios idiomas | Mucha gente no conoce la palabra. Explicarla cuesta | Buena, pero arriesgada |
| **DESFASE** | Doble sentido en España ("¡qué desfase!" + desfase temporal) | En Latinoamérica pierde el doble sentido. Ya existe un colectivo de cine peruano llamado Desfase Films | Descartada |
| **LA GRIETA** | Evoca el portal entre mundos | En Argentina "la grieta" es la polarización política: connotación negativa en un mercado clave | Descartada |
| **VÓRTICE / PARADOJA** | Suenan potentes | Encasillan en ciencia ficción | Descartadas |

### Recomendación
**ANOMALÍA** como nombre y **"Películas imposibles"** como lema.
- Ejemplo de canal: **Anomalía · Películas imposibles**
- Ejemplos de @: `@anomaliafilms`, `@anomalia.films`, `@anomaliacine`

### Comprobación de disponibilidad (hasta donde he podido)
- He buscado en la web "Anomalía Films", "Cine Imposible", "Errata Films", "Grieta Films" y "Desfase Films": **no he encontrado ningún canal de YouTube con esos nombres**. Solo aparecen la película *Anomalia* (2019), un corto argentino de 2018 y el colectivo peruano Desfase Films.
- **Desde este entorno no puedo abrir youtube.com**, así que no puedo confirmar si los @ están libres. Eso lo tienes que comprobar tú (son 2 minutos, te lo explico cuando elijamos nombre).

---

## 8. Pendiente en la Fase 1 (en este orden)
1. ✅ Análisis del concepto.
2. ⏳ **Elegir el nombre** ← estamos aquí.
3. Comprobar los @ en YouTube, TikTok e Instagram.
4. Personalidad de la marca (tono de los títulos, de las descripciones, de la comunidad).
5. Identidad visual: logo, colores, tipografía, sello del número de película, marca de agua.
6. Dirección artística: el "look" común de todas las películas.

> Nota: en tu mensaje mencionas una imagen de referencia, pero no me ha llegado. Cuando lleguemos a la identidad visual, súbela al chat.
