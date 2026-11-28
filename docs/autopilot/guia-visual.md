# Shock Mental · Guía visual y de voz (propuesta v2, pendiente de tu aprobación)

## 1. Auditoría (28-nov-2026)
| Elemento | Lo que funciona | Lo que parece amateur o no llama la atención |
|---|---|---|
| **Logotipo** (cerebro, rayos, «SHOCK MENTAL?») | Colores reconocibles (azul eléctrico y naranja) y mucha energía | Demasiados detalles: dinosaurio, chispas, interrogación y lema. En el tamaño del avatar (unos 40 px) no se lee ni «SHOCK» |
| **Banner** | Usa la paleta del canal | El logo es diminuto en medio de un degradado vacío. No dice qué es el canal ni cuándo hay vídeos nuevos |
| **Miniaturas de vídeos largos** | El canal se reconoce y el texto se lee bien | Siempre la misma composición: texto a la izquierda en 2 líneas, etiqueta, rayo y logo en la esquina. El texto ocupa la mitad y la imagen pierde fuerza. Los títulos con «¿…?» se repiten. Algunos fondos son planos (Arca de Noé, OVNI) y el rayo cruza al sujeto. El logo de la esquina sobra porque YouTube ya muestra el avatar |
| **Primer fotograma de los Shorts** | Las fotos reales son buenas | La lista del ranking (5-4-3-2-1) y la cabecera tapan la imagen del gancho, que es justo la portada |
| **Tipografía** | Inter Display Black: legible y moderna | Se usa siempre igual. No hay jerarquía con un color de acento |
| **Imágenes** | Fotos reales con licencia, que es lo que pide la audiencia | Algunas tienen poca resolución o les falta grado de color: se ven «de archivo» |

## 2. Dirección propuesta: «el laboratorio del asombro»
- **Base:** casi negra (#07080D) con UNA imagen protagonista grande, contraste alto y un grado cinematográfico (contraste +12 %, saturación +18 %, viñeta).
- **Firma reconocible sin ver el nombre:** el **filo eléctrico**, una línea degradada cian (#22D3EE) → ámbar (#FFB020) bajo el texto, más una sola palabra en el color de acento. Sin logo en la miniatura.
- **Texto:** 1-3 palabras, Inter Display Black de 140-190 px, en mayúsculas y con sombra fuerte. Complementa el título, no lo repite.
- **Acento por categoría:**

  | Categoría | Color |
  |---|---|
  | Ranking | ámbar #FFB020 |
  | Ciencia | cian #22D3EE |
  | Historia | oro #E8B04A |
  | Misterio | rojo #FF3B3B |
  | Tecnología | violeta #A78BFA |
  | Datos | amarillo #FFD21F |

- **Plantillas** (`miniaturas/plantilla-v2.html`):

  | Plantilla | Uso | Composición |
  |---|---|---|
  | `heroe` | Por defecto | Sujeto a la derecha, texto a la izquierda |
  | `centro` | Ciencia y espacio | Sujeto centrado, texto arriba |
  | `numero` | Rankings | Número gigante perfilado detrás del sujeto |
  | `comparacion` | Datos | Antes/después o A frente a B, con divisoria eléctrica |
  | `misterio` | Misterio | Un único foco de luz y el resto en penumbra |

- **Prohibido:** flechas, círculos rojos, más de 4 palabras, imágenes de IA genéricas, caras de personas reales hechas con IA, y prometer algo que no sale en el vídeo.
- **Prueba automática:** el texto debe medir al menos 13 px en una miniatura de 246 px (inicio en el móvil), el contraste al menos 3:1 sobre el fondo real, y la imagen no puede ser plana. Se generan 3 conceptos y se elige el mejor; tú puedes cambiarlo en Telegram.

### Shorts
- YouTube **no permite poner la portada de un Short por la API.** En la app del móvil (al subir o editando el Short) puedes elegir cualquier fotograma. Subir una imagen propia como portada solo está disponible para canales del Programa de Partners, y desde YouTube Studio en el ordenador.
- **Por eso la portada ya va dentro del vídeo:** la frase 1 es una imagen potente, sin la lista del ranking encima (ahora aparece después del gancho), con un titular de 1-3 palabras (`portada_texto`). Telegram te dice qué segundo elegir.

### Logotipo y banner (propuestas; no se cambian sin tu aprobación)
- **Logo:** mantener el actual como logotipo completo y crear un **símbolo simplificado** para el avatar: solo el cerebro dividido azul/naranja con un rayo, sin texto, que se lea a 40 px.
- **Banner:** a la izquierda «SHOCK MENTAL · Tu dosis de asombro», en el centro 3 miniaturas de muestra y a la derecha «Shorts cada día · Dosis los martes y viernes». Todo dentro de la zona segura de 1546×423.

## 3. Voz (Voice Director)
- **Herramienta:** Google Cloud TTS, voz `es-US-Chirp3-HD-Achird`.
  - Chirp 3 HD permite: velocidad, pausas (`[pause short]`, `[pause]`, `[pause long]`), SSML básico y pronunciaciones. **No tiene control de emoción ni de estilo.**
  - La energía se consigue con la escritura (preguntas, pausas antes del dato, exclamaciones medidas) y con la velocidad.
- **Pruebas** (mismo texto, misma voz):
  - **A** · Actual (1,15x).
  - **B** · Dinámica (1,22x, exclamaciones y pausas).
  - **C** · Equilibrada (1,12x, preguntas retóricas y pausas antes del dato).
  - Medidas: nota de locución A 82,9 · B 95,5 · C 91,4. Variación de tono: A 4,4 · B 5,2 · C 5,0 semitonos.
- **Opción más expresiva (requiere tu autorización, tiene coste):** **Gemini-TTS** tiene la misma voz «Achird» con instrucción de estilo («dilo con curiosidad y entusiasmo natural»). El precio publicado por terceros es de unos 10 $ por millón de tokens de audio, aproximadamente 2 €/mes al ritmo actual. **No está activado.**
