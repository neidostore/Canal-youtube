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
