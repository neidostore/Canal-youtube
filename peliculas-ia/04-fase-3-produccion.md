# Neido Studio · Fase 3: sistema de producción

> Estado: **en curso**. Investigación de herramientas (noviembre de 2026).
> Aviso: casi todas las fuentes sobre planes gratuitos son blogs de terceros y a menudo se contradicen. Lo que se marca como "a verificar" se comprueba en la web oficial o en la prueba técnica antes de depender de ello.

---

## 1. El hallazgo principal ⚠️

**Los planes gratuitos de las grandes herramientas de vídeo con IA no sirven para un canal monetizado.** La práctica totalidad añade marca de agua y prohíbe el uso comercial en el plan gratis:

| Herramienta | Plan gratis (según fuentes de 2026) | Marca de agua | Uso comercial gratis |
|---|---|---|---|
| **Kling** | 66 créditos/día, sin acumular | Sí (casi todas las fuentes) | ❌ No |
| **Hailuo (MiniMax)** | Ya sin créditos mensuales; solo créditos de prueba (fuentes recientes) | Sí, 720p | ❌ No |
| **Dreamina (CapCut)** | 120-225 créditos/día según país; 1-2 clips | Sí, 720p | ❌ Solo uso personal |
| **Google Veo (app Gemini)** | Vídeo solo en planes de pago, según la mayoría de fuentes | — | — |
| **Grok Imagine** | Vídeo solo de pago (desde ~30 $/mes) | Sí, en todos los planes | — |
| **Wan (wan.video, web)** | Créditos por entrar cada día | ? | ? Condiciones no claras |

Un canal que quiere monetizar es uso comercial. Usar estas herramientas gratis implicaría marcas de agua en pantalla y un problema legal en cuanto el canal gane dinero.

Fuentes: [Kling, eesel](https://www.eesel.ai/blog/kling-ai-pricing), [Kling, aireiter](https://aireiter.com/blog/kling-ai-free-tier-2026), [Hailuo, framesurfer](https://framesurfer.com/blogs/hailuo-ai-video), [Hailuo, kingy](https://kingy.ai/news/hailuo-minimax-ai-review-a-new-era-of-ai-generated-video-creation/), [Dreamina, activepieces](https://www.activepieces.com/blog/dreamina-pricing-2026-plans-credits-and-costs), [Veo, costbench](https://costbench.com/software/ai-video-generators/google-veo/free-plan/), [Veo, aibusinessweekly](https://aibusinessweekly.net/p/google-gemini-video), [Grok, aliteq](https://aliteq.com/is-grok-imagine-free), [Wan, aitoolfinder](https://aitoolfinder.org/tools/wan-ai/).

---

## 2. La alternativa: modelos abiertos en GPU gratuita

Existen modelos de IA **de código abierto con licencia que permite uso comercial**, sin marca de agua. El problema es que necesitan una tarjeta gráfica potente. La solución gratuita:

### Kaggle (de Google): GPU gratis ~30 horas a la semana
- 2 tarjetas **NVIDIA T4** de 16 GB cada una, sesiones de hasta 12 h, cuota de ~30 h/semana. ([fastero](https://fastero.com/blog/kaggle-notebooks), [gabrubuilds](https://gabrubuilds.com/guides/kaggle-free-gpu/), [aifree](https://aifree.dev/offer/kaggle-free-gpu-tpu))
- **Se puede manejar a distancia con su API**: subir un "cuaderno" con las instrucciones, ejecutarlo en la GPU y descargar los resultados. ([docs oficiales de la API](https://raw.githubusercontent.com/Kaggle/kaggle-api/main/docs/kernels.md))
- **Consecuencia clave: Claude puede lanzar la generación de vídeo y voz por sí mismo**, sin que tú tengas que pegar prompts uno a uno. Tú solo creas la cuenta una vez y das acceso.

### Modelos candidatos
| Tarea | Modelo | Licencia | Notas |
|---|---|---|---|
| Animar imágenes (imagen → vídeo) | **Wan 2.2 TI2V-5B** (Alibaba) | Apache 2.0 ✅ comercial | Oficialmente pide 24 GB para 720p; en una T4 de 16 GB hará falta cuantizar o bajar resolución, y será lento. Sin cifras verificadas en T4: **se mide en la prueba técnica**. ([Hugging Face](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B), [computingforgeeks](https://computingforgeeks.com/run-wan-video-generation-locally/)) |
| Voces | **Chatterbox Multilingual** (Resemble AI) | MIT ✅ comercial | Español de España y de Latinoamérica; clona una voz con ~10 s de referencia; marca de agua de audio inaudible. ([Hugging Face](https://huggingface.co/ResembleAI/chatterbox), [Resemble](https://resemble.ai/introducing-chatterbox-multilingual-open-source-tts-for-23-languages)) |
| Sincronización labial | **LatentSync** (ByteDance) | Código Apache 2.0; pesos OpenRAIL++ (a verificar) | ([GitHub](https://github.com/bytedance/LatentSync), [Hugging Face](https://huggingface.co/ByteDance/LatentSync-1.6)) |

### Imágenes
- **Gemini (app gratuita)**: muy buena calidad y muy buena para mantener personajes con imágenes de referencia (ya lo comprobamos con el logo y la foto de perfil). Google declara que no reclama la propiedad del contenido generado ([condiciones de la API de Gemini](https://ai.google.dev/gemini-api/terms-archive/terms_11_20_25)); las condiciones de la app de consumo y la marca de agua visible **están por verificar**. ([felloai](https://felloai.com/is-nano-banana-free/), [aifreeapi](https://www.aifreeapi.com/en/posts/nano-banana-free-use))
- Alternativa abierta en Kaggle si Gemini no sirviera: a valorar en la prueba técnica.

---

## 3. Los tres caminos posibles

| Camino | Calidad | Uso comercial / marca de agua | Tu trabajo | Riesgo |
|---|---|---|---|---|
| **A) Herramientas web gratuitas** (Kling, Dreamina…) | La mejor | ❌ / con marca de agua | Alto: todo a mano | Incompatible con monetizar |
| **B) Todo con modelos abiertos en Kaggle** | Menor que Kling | ✅ / sin marca | Mínimo: lo lanza Claude | Calidad y velocidad por confirmar |
| **C) Híbrido**: imágenes con Gemini (a mano) + animación, voces y labios con modelos abiertos en Kaggle (lo lanza Claude) + montaje automático | Buena | ✅ / sin marca (a verificar Gemini) | Medio: solo las imágenes clave | Velocidad de Kaggle por confirmar |

**Recomendación: C**, validado con la prueba técnica de 30-60 s.

### ✅ DECISIÓN: camino C (híbrido)

---

## 4. Estado del acceso a Kaggle
- Cuenta creada. Token guardado como secreto de red para `www.kaggle.com` y en `~/.kaggle/access_token` de esta sesión (archivo efímero, no está en el repositorio).
- ⚠️ Los dos tokens que se escribieron en el chat están expuestos: **revocarlos** y crear uno nuevo fuera del chat.
- ❌ Bloqueado: el programa oficial de Kaggle usa `api.kaggle.com`, que la red del entorno no permite. Desde el móvil la ventana de permiso solo ofrece "Denegar": hay que aprobarlo, o añadir `api.kaggle.com` en *Dominios permitidos* del entorno, **desde el ordenador o desde claude.ai/code en un navegador**.
- Alternativa sin red: modo manual (el usuario ejecuta en Kaggle un cuaderno preparado por Claude).

## 5. Prueba técnica
Guion, fichas y prompts → [05-prueba-tecnica.md](05-prueba-tecnica.md).

### Modo de trabajo: ✅ automático
El usuario prefiere que Claude haga todo y él dé los ok. Por eso las imágenes también se generan con modelos abiertos en Kaggle (no con Gemini). Si la calidad no llega, plan B: el usuario hace en Gemini solo las hojas de personaje.

## 6. Sistema de producción construido
Ver [pipeline/README.md](pipeline/README.md). Cortinilla y montaje automático funcionando; etapas de Kaggle escritas, pendientes de acceso a `api.kaggle.com`.

## 7. Problemas con las GPU gratuitas (24/11/2026)
- **Kaggle:** cuenta, teléfono, cuota (0 de 30 h usadas) e internet correctos, pero la cola de GPU estaba en la **posición 1188**. Los trabajos lanzados por API se quedaron más de 2 h en cola. No es fiable a ciertas horas; queda por probar a primera hora de la mañana (Europa).
- **Modal:** cuenta creada sin tarjeta (1 $ de crédito). **Las funciones con GPU exigen añadir un método de pago**, aunque el crédito sea gratuito ("Please add a payment method to use T4 GPU functions"). Sin tarjeta solo sirve para CPU. Descartado mientras la condición sea no poner tarjeta.
- **Lightning AI:** según fuentes de septiembre de 2026, el plan gratuito pasó a ser un crédito único de 5 $ sin tarjeta (25 más con tarjeta). Daría para la prueba técnica, no para producir cada semana. ([usagepricing](https://www.usagepricing.com/blueprint/activity/lightning-ai-2026-09-21-gpu-rate-card-reprice), [aimultiple](https://aimultiple.com/free-cloud-gpu))
- Conclusión provisional: **no hay GPU gratuita, fiable y automatizable sin tarjeta.** La opción sostenible a 0 € es Kaggle si la cola es razonable a otras horas.
