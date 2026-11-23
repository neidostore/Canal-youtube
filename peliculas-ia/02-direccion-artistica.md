# Neido Studio · Dirección artística (propuesta)

> Estado: **propuesta pendiente de aprobación**. Es el último punto de la Fase 1.
> Objetivo: que cualquiera reconozca una película de Neido Studio con ver un solo fotograma, sea de la época o el género que sea.

---

## 1. El principio
**Lo imposible es la historia, nunca el estilo.**
Todas las películas se ven como fotografía de cine real: luz creíble, caras con textura, colores naturales. Un caballero medieval en un supermercado se rueda igual que un drama serio. Es la versión visual del tono que ya elegimos: *serios en la forma, gamberros en la premisa*.

---

## 2. Formato de imagen
| Uso | Formato |
|---|---|
| Películas (YouTube) | Vídeo 16:9 (1920×1080) con **bandas negras de cine 2,39:1** |
| Shorts / TikTok / Reels | 9:16 vertical, **sin bandas** (se recorta el centro de la escena) |
| Miniaturas | 16:9 con bandas finas (como en el boceto) |

Por qué las bandas: es la señal más rápida de "esto es cine", unifican planos de herramientas distintas y esconden defectos en los bordes de la imagen, que es donde más falla la IA.
Pega: se aprovecha menos pantalla. En móvil horizontal apenas se nota.

**Consecuencia práctica:** al generar cada plano hay que dejar "aire" arriba y abajo, porque esa parte se tapará. Lo importante va en la franja central.

---

## 3. Color
**Firma de la casa: el contraste cálido-frío de la puerta.**
- Cada película tiene **un mundo dominante** (el de la época o el lugar) y **un acento** que corresponde a la anomalía.
- Ejemplo, Titanic: el barco es ámbar y dorado (luz de lámparas, atardecer); el colombiano trae algo de luz fría (la pantalla del móvil, una camiseta azul). El color cuenta que no pertenece a ese mundo.

Paletas orientativas por mundo:
| Mundo | Paleta | Luz típica |
|---|---|---|
| Pasado (historia, época) | ámbar, sepia, oro, marrones | velas, lámparas, atardecer |
| Presente | neutra, natural | día nublado, fluorescentes, farolas |
| Futuro / espacio | cian, violeta, acero | pantallas, neón contenido, luz de estrellas |
| Fantasía / mitos | verdes musgo, oro viejo, niebla | luz filtrada, antorchas |
| Terror / misterio | casi monocromo, verde-gris | una sola fuente de luz |

Ajuste común en el montaje (el "etalonaje de la casa"):
- Saturación algo por debajo de lo natural (−10/−15 %). Nada de colores chillones.
- Negros ligeramente levantados (no negro puro), luces altas suaves.
- Tonos de piel siempre naturales, aunque el resto se coloree.

---

## 4. Luz
- **Luz motivada:** siempre debe existir algo que la produzca (ventana, lámpara, fuego, pantalla). Es lo que más diferencia el cine de la imagen de IA "porque sí".
- **Contraluces y atmósfera:** polvo, humo, niebla o vapor en el aire para que se vean los haces de luz.
- **Horas preferidas:** atardecer, noche y interiores con poca luz. Esconden mejor los defectos de la IA y son más cinematográficos que el mediodía.
- **El motivo de la casa:** en cada película, al menos un plano con **luz colándose por una puerta o una rendija**. Enlaza con el logo y es candidato a ser el easter egg que se repite (lo decidiremos en la Fase 2).

---

## 5. Cámara
- **Objetivos de cine:** sensación de 35 mm para los planos generales y de 50-85 mm para los primeros planos, con el fondo desenfocado.
- **Movimientos según el momento:**
  - Lentos y suaves (travelling, acercamiento) para presentar mundos y personajes.
  - Cámara en mano para la acción y la tensión.
  - Cámara quieta para el humor: el chiste funciona mejor con la cámara parada y la reacción en plano.
- **Destellos anamórficos** (las rayas de luz horizontales) con mucha moderación: uno o dos por película, no en cada plano.

---

## 6. Textura
- **Grano de película fino** en todos los planos, el mismo en toda la película. Es el "pegamento" que hace que clips de herramientas distintas parezcan rodados con la misma cámara.
- **Viñeteado** suave (bordes ligeramente más oscuros).
- **24 fotogramas por segundo**, el ritmo del cine.
- Nada de exceso de nitidez: la IA ya sale demasiado nítida y "digital".

---

## 7. Personajes
- **Caras reales, no caras de anuncio:** poros, arrugas, ojeras, barba de tres días, pelo despeinado. Las caras perfectas y lisas delatan la IA al instante.
- Variedad de edades, cuerpos y rasgos según el origen del personaje.
- Vestuario con desgaste y detalles de época bien documentados (lo verificamos en cada guion).

---

## 8. Rótulos y tipografía
- **Títulos de película:** Cormorant Garamond (la tipografía del logo), en blanco roto, con mucho espacio alrededor.
- **Textos secundarios** (lugar, año, "Película Nº 001"): Montserrat, pequeña y espaciada.
- **Rótulo de lugar y fecha** al empezar cada historia, estilo cine: *"Atlántico Norte · 14 de abril de 1912"*.
- Los textos se ponen siempre en el editor, nunca dentro de la imagen generada (la IA escribe mal).

---

## 9. Lo que NO hacemos
- ❌ Neón y brillos por todas partes, el "look de IA" de siempre.
- ❌ Portales en espiral, galaxias y efectos mágicos gratuitos.
- ❌ Caras de plástico perfectas.
- ❌ Colores saturados al máximo.
- ❌ Mezclar estilos en una misma película (realista + dibujo animado), salvo que sea un recurso de la historia.
- ❌ Texto generado por la IA dentro de la imagen.

---

## 10. El "ADN visual": bloque fijo para todos los prompts
Para que todas las imágenes salgan con el mismo estilo, cada prompt de imagen terminará con este bloque, siempre igual:

```
Cinematic film still, photorealistic, shot on 35mm with a cinema camera, natural motivated lighting, realistic skin texture with pores and imperfections, subtle film grain, slightly muted natural colours, shallow depth of field, atmospheric haze, composed for a 2.39:1 widescreen crop with the important action in the central band. No text, no watermark, no neon overload, no oversaturation, no plastic-looking faces.
```

Se ajustará cuando probemos las herramientas en la Fase 3 (cada generador responde distinto).
