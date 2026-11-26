# Neido Studio · Música de la prueba técnica (Titanic), compuesta en MIDI y sintetizada con FluidSynth.
# - Parte 1: melodía ORIGINAL de flauta irlandesa (tin whistle) con cuerdas y arpa, estilo celta.
# - Parte 2: "Nearer, My God, to Thee" (melodía "Bethany", Lowell Mason, 1856: dominio público),
#   el himno que la orquesta del Titanic tocó durante el hundimiento.
# No usa ninguna melodía con derechos. Tempo 60 = 1 pulso por segundo, para cuadrar con los planos.
# Uso: python componer.py salida.mid [planos.json]
import sys, mido

import json
INTRO = 3.5           # la cortinilla dura 3,5 s
# los tiempos salen de planos.json: el himno entra en el plano 8 (cuando Margaret dice "El Titanic")
_pl = json.load(open(sys.argv[2]))["planos"] if len(sys.argv) > 2 else None
HIMNO = INTRO + sum(float(p["duracion"]) for p in _pl if p["n"] < 8) if _pl else 32.5
FIN = INTRO + sum(float(p["duracion"]) for p in _pl) if _pl else 40.5
TPB = 480
N = {"A3": 57, "B3": 59, "C#4": 61, "D3": 50, "D4": 62, "E4": 64, "F#4": 66, "G3": 55, "G4": 67, "A4": 69,
     "B4": 71, "C#5": 73, "D5": 74, "E5": 76, "F#5": 78, "G5": 79, "A5": 81, "A2": 45, "B2": 47, "G2": 43, "D2": 38,
     "E3": 52, "F#3": 54, "C#3": 49}
ACORDES = {"D": ["D3", "A3", "D4", "F#4"], "G": ["G2", "D3", "G3", "B3"], "A": ["A2", "E3", "A3", "C#4"],
           "Bm": ["B2", "F#3", "B3", "D4"], "Asus": ["A2", "E3", "A3", "D4"]}

eventos = []  # (tiempo_s, canal, nota, velocidad, duración_s)
def nota(t, canal, n, v, d): eventos.append((t, canal, N[n], v, d))

# canal 0 flauta (78 Whistle), 1 cuerdas (49 String Ensemble 2), 2 arpa (46), 3 coro (52 Choir Aahs), 4 cuerdas graves (48)
# --- parte 1: colchón de cuerdas + arpa, la flauta entra a los 4 s
compases = ["D", "D", "G", "D", "A", "G", "Bm", "D"]          # 8 compases de 3,5 s ≈ 28 s
dur_c = (HIMNO - INTRO) / len(compases)
for i, a in enumerate(compases):
    t = INTRO + i * dur_c
    for n in ACORDES[a]:
        nota(t, 1, n, 52, dur_c)
    for k, n in enumerate((ACORDES[a][1:] + [ACORDES[a][2]]) * 2):   # arpegio lento
        nota(t + k * dur_c / 8, 2, n, 40, dur_c / 2)
melodia = [  # (nota, pulsos) melodía original, empieza en el 2.º compás
    ("D5", 1.5), ("E5", .5), ("F#5", 1), ("E5", .5),
    ("D5", .5), ("B4", 1.5), ("A4", 2), ("D5", 1.5), ("E5", .5), ("F#5", 1), ("A5", 1),
    ("F#5", 2), ("E5", 2), ("B4", 1.5), ("D5", .5), ("E5", 1), ("F#5", 1),
    ("E5", 1.5), ("D5", .5), ("B4", 1), ("A4", 1), ("D5", 4)]
escala = (HIMNO - 1 - (INTRO + dur_c)) / sum(d for _, d in melodia)
t = INTRO + dur_c
for n, d in melodia:
    nota(t, 0, n, 78, d * escala * 0.95); t += d * escala

# --- parte 2: el himno, lento y grave (frase "Nearer, my God, to Thee, nearer to Thee")
himno = [("F#4", 1), ("E4", .5), ("D4", .5), ("D4", 1), ("B3", 1), ("A3", 1), ("D4", 1), ("F#4", 1), ("E4", 2)]
acordes_h = [("D", 0), ("G", 2), ("D", 4), ("Asus", 6)]
for a, off in acordes_h:
    for n in ACORDES[a]:
        nota(HIMNO + off, 4, n, 60, 2.2 if a != "Asus" else 2.5)
        nota(HIMNO + off, 3, n, 34, 2.2 if a != "Asus" else 2.5)
t = HIMNO
for n, d in himno:
    nota(t, 1, n, 70, d * 0.98); t += d

mid = mido.MidiFile(ticks_per_beat=TPB)
pista = mido.MidiTrack(); mid.tracks.append(pista)
pista.append(mido.MetaMessage("set_tempo", tempo=1_000_000))
for canal, prog in enumerate([78, 49, 46, 52, 48]):
    pista.append(mido.Message("program_change", channel=canal, program=prog, time=0))
    pista.append(mido.Message("control_change", channel=canal, control=91, value=90, time=0))   # reverberación
msgs = []
for t, c, n, v, d in eventos:
    msgs.append((t, 1, mido.Message("note_on", channel=c, note=n, velocity=v)))
    msgs.append((t + d, 0, mido.Message("note_off", channel=c, note=n, velocity=0)))
msgs.append((FIN, 0, mido.MetaMessage("end_of_track")))
msgs.sort(key=lambda x: (x[0], x[1]))
ahora = 0
for t, _, m in msgs:
    tick = round(t * TPB); m.time = tick - ahora; ahora = tick; pista.append(m)
mid.save(sys.argv[1] if len(sys.argv) > 1 else "musica.mid")
print("MIDI listo", len(eventos), "notas")
