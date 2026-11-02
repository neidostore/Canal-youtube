# Producción automática de vídeos

```
GOOGLE_TTS_API_KEY=... python3 produccion/montar.py produccion/videoNN
```
- `videoNN/escenas.json`: guion dividido en frases, con la foto (Pexels) o la tarjeta de cada una.
- Resultado en `videoNN/salida/`: `video.mp4` (1080p), `subtitulos.srt` y `capitulos.txt`. No se suben a git.
- Voz: Google Cloud TTS, `es-US-Chirp3-HD-Orus`.
- Tarjetas (cifras, listas, citas, gráficos): `tarjetas.html` + `render_tarjetas.js`.
