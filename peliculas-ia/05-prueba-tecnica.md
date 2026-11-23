# Neido Studio · Prueba técnica (Fase 3)

> Objetivo: producir **~45 segundos** de película con el camino C y medir de verdad calidad, tiempo y coste.
> No es la Película Nº 001: es un ensayo. Si sale bien, la escena se puede reaprovechar.

## Qué se pone a prueba
| Prueba | Dónde |
|---|---|
| Mantener la misma cara y ropa en varios planos | Santi en los planos 3, 7 y 9; la señora en 5, 6 y 8 |
| Animar imágenes de Gemini con Wan 2.2 en Kaggle | Planos 2, 3, 5, 8, 9 |
| Imagen fija con movimiento hecho en el montaje | Plano 1 |
| Voces con acento (Chatterbox) | Narrador, Santi (colombiano, Medellín), señora (español formal) |
| Sincronización labial (LatentSync) | Planos 6 y 7 |
| Pensamientos en off sin lip-sync | Planos 3 y 9 |
| Rótulo y easter egg añadidos en el montaje | Planos 1 y 4 |
| Montaje automático: bandas 2,39:1, grano, color, sonido, cortinilla | Todo |

---

## Fichas de personaje

### SANTIAGO "SANTI" RESTREPO (la anomalía)
- Colombiano de Medellín, 32 años. Técnico de mantenimiento de ascensores. Ingenioso, rápido, de buen humor incluso cuando está asustado.
- **Físico:** piel morena clara, pelo negro corto con los lados rapados, barba corta de pocos días, ojos marrones, complexión delgada, 1,75 m.
- **Ropa (no cambia nunca):** camiseta lisa amarilla, chaqueta vaquera azul abierta, vaqueros oscuros, zapatillas blancas, gorra negra sin logotipos, mochila gris pequeña.
- **Objeto:** un móvil con funda negra.
- **Ventaja:** sabe lo que le pasó al Titanic. **Desventaja:** nadie le va a creer.

### LADY MARGARET ASHFORD (personaje inventado)
- Pasajera británica de primera clase, 55 años. Orgullosa, estirada, pero curiosa.
- **Físico:** piel clara, pelo gris recogido en un moño alto, rostro anguloso con arrugas marcadas, ojos azul grisáceo.
- **Ropa (no cambia nunca):** vestido de noche eduardiano de color burdeos oscuro, estola de piel clara, collar de perlas, guantes largos de color marfil.

## Ficha de escenario: cubierta de paseo de primera clase, Titanic
- 14 de abril de 1912, ~23:30. Noche sin luna, mar en calma total, cielo lleno de estrellas, mucho frío (se ve el vaho al hablar).
- Suelo de tablas de madera, barandilla blanca, botes salvavidas colgados, lámparas eléctricas de luz cálida en la pared.
- **Luz:** cálida y dorada de las lámparas (mundo de 1912). La luz fría solo llega con Santi: la pantalla de su móvil y la luz de la puerta.
- **Dirección:** la proa queda a la derecha de la imagen; el mar, al fondo.

---

## Guion técnico (~45 s)

| Nº | Plano | Duración | Imagen | Sonido |
|---|---|---|---|---|
| 1 | General: el Titanic navegando de noche en mar en calma | 5 s | Imagen fija + acercamiento lento en el montaje. Rótulo: *Atlántico Norte · 14 de abril de 1912* | NARRADOR: *"14 de abril de 1912. Esta noche, en el barco más famoso del mundo, hay alguien que no debería estar aquí."* Mar, motores lejanos |
| 2 | POV: una puerta de servicio se abre a la cubierta; luz cálida delante, luz fría detrás | 3 s | Vídeo (Wan) | Puerta, viento |
| 3 | Medio: Santi sale a la cubierta, mira alrededor, desconcertado | 4 s | Vídeo (Wan) | SANTI (pensamiento): *"Ush… esto no es el metro de Medellín."* |
| 4 | Inserto: su móvil en la mano, sin cobertura, 4:04 | 2 s | Imagen fija; la hora y "Sin servicio" se ponen en el montaje (easter egg) | Pitido de error suave |
| 5 | Medio: Lady Margaret lo mira de arriba abajo desde la barandilla | 3 s | Vídeo (Wan), reacción sin hablar | Música de cuerda lejana del salón |
| 6 | Medio-corto: Lady Margaret habla | 4 s | Vídeo + lip-sync | LADY MARGARET: *"¿Se ha perdido, caballero? Esta cubierta es de primera clase."* |
| 7 | Medio-corto: Santi responde, sonriendo nervioso | 5 s | Vídeo + lip-sync | SANTI: *"¿Qué pasa, pues? Tranquila, mi señora… Oiga, una preguntica: ¿este barco cómo se llama?"* |
| 8 | Medio: Lady Margaret, orgullosa, mirando al mar | 4 s | Vídeo (Wan); la voz va sobre el plano sin mover los labios en exceso (de perfil) | LADY MARGARET: *"El Titanic, por supuesto. El barco más seguro jamás construido."* |
| 9 | Primer plano: la cara de Santi se descompone | 4 s | Vídeo (Wan), reacción | SANTI (pensamiento): *"Ay, no. No, no, no, no…"* Silencio total → corte a negro |

Total con la cortinilla: ~45 s.

---

## Prompts para Gemini (desde el móvil)

**Orden:** primero las dos hojas de personaje (1 y 2). Después, para cada plano, **adjunta la hoja del personaje** que sale en él, para que Gemini mantenga la cara y la ropa. Pide **formato 16:9**.

Bloque fijo de estilo (ya va incluido al final de cada prompt): *ADN visual*.

### 1. Hoja de personaje: Santi
```
Character reference sheet, photorealistic, neutral grey studio background, soft even lighting. The same man shown three times side by side: front view, three-quarter view, and profile. He is a 32-year-old Colombian man from Medellín, light brown skin, short black hair with shaved sides, short stubble beard, brown eyes, slim build. He wears a plain yellow t-shirt, an open blue denim jacket, dark jeans, white sneakers, a plain black cap with no logos, and a small grey backpack. Friendly, clever expression. Realistic skin texture with pores, no retouching. No text.
```

### 2. Hoja de personaje: Lady Margaret
```
Character reference sheet, photorealistic, neutral grey studio background, soft even lighting. The same woman shown three times side by side: front view, three-quarter view, and profile. She is a 55-year-old British aristocrat in 1912: fair skin, grey hair in a high bun, angular face with marked wrinkles, grey-blue eyes, proud posture. She wears a dark burgundy Edwardian evening gown, a light fur stole, a pearl necklace and long ivory gloves. Realistic skin texture, no retouching. No text.
```

### Plano 1 (sin personajes)
```
Wide establishing shot of the RMS Titanic sailing at night on a perfectly calm, mirror-like North Atlantic, moonless sky full of stars, warm lights glowing from the portholes and decks, faint smoke from the funnels, cold atmosphere. Cinematic film still, photorealistic, shot on 35mm with a cinema camera, natural motivated lighting, subtle film grain, slightly muted natural colours, atmospheric haze, composed for a 2.39:1 widescreen crop with the ship in the central band. No text, no watermark, no oversaturation. 16:9.
```

### Plano 2 (sin personajes)
```
Point-of-view shot from inside a dark narrow service corridor of a 1912 ocean liner, looking at a wooden door that is opening onto the first-class promenade deck at night. Warm golden light from the deck lamps spills in through the opening; behind the viewer, a faint cool cyan light glows. Wooden deck planks and a white railing visible through the door, starry night sky beyond. Cinematic film still, photorealistic, shot on 35mm with a cinema camera, natural motivated lighting, subtle film grain, slightly muted natural colours, atmospheric haze, composed for a 2.39:1 widescreen crop. No text, no watermark. 16:9.
```

### Plano 3 (adjunta la hoja de Santi)
```
Using the attached character sheet for the man's face, hair and clothes exactly, medium shot of this man stepping out onto the first-class promenade deck of the Titanic at night, 1912. He looks around confused and amazed, the bow is to the right of the frame. Wooden deck, white railing, lifeboats hanging above, warm electric wall lamps, his breath visible in the cold air, starry sky. His modern clothes look out of place. Cinematic film still, photorealistic, shot on 35mm with a cinema camera, natural motivated lighting, realistic skin texture, subtle film grain, slightly muted natural colours, shallow depth of field, atmospheric haze, composed for a 2.39:1 widescreen crop with him in the centre. No text, no watermark, no plastic-looking faces. 16:9.
```

### Plano 4 (adjunta la hoja de Santi)
```
Close-up insert shot of a man's hand holding a modern smartphone with a black case, the screen glowing cool blue-white, against the dark wooden deck of a 1912 ocean liner at night with warm lamp light in the background. The screen content is blank and bright (no readable text). Cinematic film still, photorealistic, shallow depth of field, subtle film grain. No text, no watermark. 16:9.
```

### Plano 5 (adjunta la hoja de Lady Margaret)
```
Using the attached character sheet for the woman's face, hair and clothes exactly, medium shot of this woman standing by the white railing of the Titanic's first-class promenade deck at night, 1912, looking at someone off-screen to the left with a mix of disdain and curiosity, one eyebrow raised. Warm electric wall lamps, starry sky, calm black sea behind her, her breath visible in the cold air. Cinematic film still, photorealistic, shot on 35mm with a cinema camera, natural motivated lighting, realistic skin texture with wrinkles, subtle film grain, slightly muted natural colours, shallow depth of field, composed for a 2.39:1 widescreen crop with her in the centre. No text, no watermark. 16:9.
```

### Plano 6 (adjunta la hoja de Lady Margaret)
```
Using the attached character sheet for the woman's face, hair and clothes exactly, medium close-up of this woman on the Titanic's first-class deck at night, 1912, facing the camera slightly to the left, mouth slightly open as if about to speak, haughty expression. Warm lamp light on her face, dark starry background softly blurred. Cinematic film still, photorealistic, realistic skin texture, subtle film grain, slightly muted natural colours, shallow depth of field, face clearly visible and well lit, composed for a 2.39:1 widescreen crop with her face in the centre. No text, no watermark. 16:9.
```

### Plano 7 (adjunta la hoja de Santi)
```
Using the attached character sheet for the man's face, hair and clothes exactly, medium close-up of this man on the Titanic's first-class deck at night, 1912, facing the camera slightly to the right, nervous friendly smile, mouth slightly open as if about to speak. Warm lamp light on one side of his face, a faint cool blue glow from below from his phone. Dark starry background softly blurred. Cinematic film still, photorealistic, realistic skin texture, subtle film grain, slightly muted natural colours, shallow depth of field, face clearly visible and well lit, composed for a 2.39:1 widescreen crop with his face in the centre. No text, no watermark. 16:9.
```

### Plano 8 (adjunta la hoja de Lady Margaret)
```
Using the attached character sheet for the woman's face, hair and clothes exactly, medium shot in profile of this woman looking proudly out at the calm black sea from the Titanic's railing at night, 1912, chin raised. Warm lamp light outlining her profile, starry sky. Cinematic film still, photorealistic, realistic skin texture, subtle film grain, slightly muted natural colours, shallow depth of field, atmospheric haze, composed for a 2.39:1 widescreen crop. No text, no watermark. 16:9.
```

### Plano 9 (adjunta la hoja de Santi)
```
Using the attached character sheet for the man's face, hair and clothes exactly, close-up of this man's face on the Titanic's deck at night, 1912, his expression collapsing into slowly dawning horror as he realises where he is, eyes wide, the smile disappearing. Warm lamp light from the side, dark background. Cinematic film still, photorealistic, realistic skin texture with pores, subtle film grain, slightly muted natural colours, shallow depth of field, composed for a 2.39:1 widescreen crop with his face in the centre. No text, no watermark. 16:9.
```

---

## Qué medimos al terminar
- ¿Se reconoce a Santi y a Lady Margaret como las mismas personas en todos sus planos?
- Tiempo de GPU en Kaggle por clip animado y por frase de lip-sync.
- Cuántos intentos hicieron falta por plano.
- Tiempo total del usuario.
- Calidad final: ¿parece cine o parece "vídeo de IA"? Veredicto honesto.
