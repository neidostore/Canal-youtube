# Neido Studio · Sistema de producción automática

Todo el proceso, de los datos de la película al vídeo terminado, sin pasos manuales salvo la revisión del usuario.

```
producciones/<película>/planos.json      ← guion técnico en datos (lo escribe Claude)
        │
        ├─ kaggle/lanzar.py imagenes  →  clips/plano_NN.png   (SDXL + IP-Adapter, GPU de Kaggle)
        ├─ kaggle/lanzar.py voces     →  audio/plano_NN_K.wav (Chatterbox + voces semilla Kokoro)
        ├─ kaggle/lanzar.py video     →  clips/plano_NN.mp4   (Wan 2.2 TI2V-5B)
        ├─ kaggle/lanzar.py labios    →  clips/plano_NN.mp4   (LatentSync 1.5, solo planos "lipsync")
        │
        └─ montaje/montar.py  →  salida/pelicula.mp4 + pelicula.srt
                                (cortinilla, movimiento en imágenes fijas, rótulos, color de la casa,
                                 grano, viñeteado, bandas 2,39:1, voces, música, fundido final)
```

## Estado
| Pieza | Estado |
|---|---|
| `cortinilla/` (la I-puerta se abre) | ✅ Funciona. `node renderizar.js` → `cortinilla.mp4` |
| `montaje/montar.py` | ✅ Probado con material provisional (`producciones/_ensayo-montaje`) |
| `kaggle/lanzar.py` | ⏳ Escrito; bloqueado hasta que la red permita `api.kaggle.com` |
| `kaggle/imagenes.py`, `voces.py`, `video.py`, `labios.py` | ⏳ Borradores sin probar; se depuran en la prueba técnica |
| `fuentes/` | Cormorant Garamond y Montserrat (Google Fonts, licencia OFL) |

## Formato de `planos.json`
- `rotulo`, `estilo` (ADN visual), `negativo`.
- `personajes`: descripción física fija y ajustes de voz. En los prompts se escriben como `{santi}`.
- `planos`: `n`, `duracion`, `tipo` (`imagen_fija` | `video` | `lipsync`), `prompt`, `movimiento` / `movimiento_video`,
  `personajes`, `audio` (lista de `{quien, texto, tipo?}`), `rotulo`, `superposicion`, `vertical` (apto para Shorts), `final`.

## Montar una película
```
python3 pipeline/montaje/montar.py producciones/<película>            # con cortinilla
python3 pipeline/montaje/montar.py producciones/<película> --sin-cortinilla
```
Avisa si una voz dura más que su plano.
