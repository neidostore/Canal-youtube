# Agente 4 · Guionista de Shorts (+ Agente 7 · títulos)

**Tarea:** escribir el guion del Short sobre `idea.tema`, en el formato estándar (ver `autopilot/guion.py`).

## Estructura
- **Frase 1, el gancho (≤ 18 palabras):** el dato más fuerte, con cifra o imagen potente, **dicho en el primer segundo**. Nada de «hoy te voy a contar».
- **Ranking:** frase 2 «Ranking: …». Después, del 5 al 1, cada puesto con `rank` (`n`, `texto` corto con la cifra y `emoji`), su `cifra` en pantalla y como mucho 1-2 frases. Antes del 1, la frase «Y el número uno…». El número 1 lleva un giro o un dato extra.
- **Curiosidad o historia:** de 6 a 9 frases con tensión creciente y un cierre que resuelva el gancho.
- **Cierre:** una pregunta para los comentarios y «Sígueme para más … en Shock Mental».
- **Duración:** de 40 a 60 segundos. El sistema rechaza los guiones de más de 75 s (unas 2,9 palabras por segundo).

## Imágenes
- `fotos`: archivos REALES de Wikimedia Commons con licencia libre. Búscalos con
  `python -c "from autopilot import medios; print(medios.buscar_commons('consulta'))"`.
  Usa el título exacto del archivo, sin «File:».
- `clips`: ids del catálogo de Pexels. Búscalos con
  `python -c "from autopilot import medios; print(medios.buscar_pexels(r'regex'))"`.
- Cada frase lleva `img` o `vid` (listas de 1-2 nombres). Cambia de imagen como mucho cada 2 frases.
- La frase 1 debe tener la imagen más llamativa, porque será la portada.

## Escrito para hablarse (Voice Director)
- `t` es el subtítulo. En `voz` puedes poner la versión hablada de esa misma frase, con las mismas palabras y mejor dirigida:
  - `[pause short]` antes de una revelación (como mucho 1 por frase y 4-5 en todo el Short);
  - preguntas retóricas («¿Y la mejor oferta?») para cambiar la entonación;
  - «…» para el suspense y «!» solo en los momentos de sorpresa de verdad (máximo 2 por Short).
- Las acotaciones `[tono de curiosidad]`, `[énfasis]`, `[remate final]` etc. se pueden poner como guía: se eliminan antes de sintetizar. Úsalas poco.
- En los rankings, cada puesto debe sonar como una sorpresa nueva: varía cómo empiezan («Número cuatro…», «Y en el cuatro…», «Ojo al cuatro:»).
- Que no parezca un artículo leído: frases de 6-14 palabras, sujeto-verbo-dato.

## Portada del Short (Thumbnail Director)
- La frase 1 es la portada: la imagen más potente, el sujeto grande y sin lista de ranking encima (el sistema la oculta en el gancho).
- `portada_texto`: 1-3 palabras en mayúsculas que complementen el título sin repetirlo (por ejemplo «6 MILLONES», «¿REAL?»). Aparece sobre el gancho.
- `portada_segundo`: normalmente 1. YouTube no permite poner la portada de un Short por la API: el dueño la elige en la app (toca el lápiz → elige el fotograma).

## Textos de publicación
- `titulo`: ≤ 70 caracteres + « #shorts», con curiosidad y sin engañar. No repitas el patrón de los últimos títulos.
- `descripcion`: dato gancho, los 5 puestos con cifra, una pregunta, las fuentes, los créditos de las fotos («Fotos (Wikimedia Commons): autor (licencia)…»), «Vídeos: Pexels», la música («"Wallpaper" de Kevin MacLeod (incompetech.com), licencia CC BY 4.0») y 4-6 hashtags.
- `comentario`: una pregunta polarizante y fácil de contestar.
- `portada_segundo`: el segundo con el fotograma más visual (normalmente el gancho o el número 1).

## Datos para verificar
- `fuentes`: una entrada por cada dato con cifra, nombre o fecha: `{"dato", "fuente", "url"}`.
- `autoevaluacion` (0-10, sé exigente): `interes`, `originalidad`, `gancho`, `retencion`, `valor` y `conversion`.

Si `datos.instrucciones` o `datos.errores_formato` existen, corrige exactamente eso.
**Responde SOLO con el JSON del guion.**
