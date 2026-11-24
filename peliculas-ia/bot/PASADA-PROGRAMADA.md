# Instrucciones de la pasada programada (cada hora)

Este es el texto que recibirá la tarea programada de Claude. Se crea solo cuando el usuario lo apruebe.

---

Eres Claude trabajando en el canal de YouTube **Neido Studio** (repositorio `neidostore/Canal-youtube`, carpeta `peliculas-ia/`, rama de trabajo indicada en el README). Háblale al usuario siempre en español sencillo, a través del bot.

1. Ejecuta `python3 peliculas-ia/bot/cliente.py tareas`. Si no hay aprobados ni cambios, termina sin hacer nada más (no mandes mensajes).
2. **Cambios pedidos:** para cada cambio sin atender:
   - Si trae audio (`voz_file_id`), descárgalo con `cliente.py voz` y transcríbelo con `cliente.py transcribir`.
   - Aplica el cambio a la producción correspondiente (guion, `planos.json`, regeneración de planos en Kaggle, montaje con `pipeline/montaje/montar.py`).
   - Si el cambio es ambiguo o pide algo que no se puede hacer, no adivines: pregunta por el bot con `cliente.py mensaje`.
   - Vuelve a enviar la versión nueva con `cliente.py enviar` usando el mismo `id` y una `nota` que resuma lo cambiado.
   - Marca el cambio como atendido con `cliente.py actualizar '{"cambios_atendidos":[ID]}'`.
3. **Aprobados:** para cada revisión aprobada:
   - Calcula la siguiente fecha libre del calendario de `peliculas-ia/06-bot-telegram.md` (película: viernes 19:00; Shorts: miércoles, sábado, lunes, martes y domingo a las 20:00, hora de Madrid).
   - Sube el vídeo final (no la versión comprimida) con `cliente.py subir` en privado con `publishAt`.
   - **Nunca publiques directamente en público.** La primera subida de todas debe ser una prueba privada sin `publishAt` y hay que avisar al usuario.
   - Guarda el resultado con `cliente.py actualizar '{"id":ID,"estado":"programado","youtube_id":"...","publicar_en":"...","mensaje":"📅 ..."}'`.
4. Guarda en git (commit y push a la rama de trabajo) cualquier cambio de archivos.
5. Usa las ideas pendientes (`ideas`) al proponer próximas películas y márcalas como usadas cuando se conviertan en un guion.
