"""Pruebas del flujo sin red: base de datos temporal, planificación, cerebro (entregas válidas e inválidas),
verificador que devuelve al guionista, límites de gasto y detector de parecidos.
Ejecutar:  python -m autopilot.pruebas.test_flujo
"""
import json
import tempfile
from pathlib import Path

from autopilot import calidad, cerebro, director, guion as G, nucleo

EJEMPLO = json.loads((Path(__file__).parent / "guion_ejemplo_memes.json").read_text(encoding="utf-8"))


def main():
    nucleo.DB_RUTA = Path(tempfile.mkdtemp()) / "prueba.db"
    cfg = nucleo.config()
    ok = 0
    with nucleo.db() as con:
        # 1) planificar sin ideas → encarga investigación
        director.planificar(con, cfg)
        assert con.execute("SELECT COUNT(*) FROM tareas WHERE agente='investigador'").fetchone()[0] == 1; ok += 1
        # 2) el investigador entrega ideas; la de riesgo alto se descarta sola
        t = cerebro.siguiente(con)
        assert t["agente"] == "investigador" and "Investigador" in t["instrucciones"]; ok += 1
        r = cerebro.entregar(con, t["tarea_id"], {"ideas": [
            {"tema": "Fichajes más caros del fútbol", "formato": "short", "tipo": "ranking", "categoria": "deporte",
             "puntos": {"interes": 9, "originalidad": 8, "facilidad": 7, "riesgo_desinformacion": 2}},
            {"tema": "Curas milagrosas del cáncer", "formato": "short", "tipo": "curiosidad", "categoria": "salud",
             "puntos": {"interes": 9, "originalidad": 5, "facilidad": 5, "riesgo_desinformacion": 9}},
            {"tema": "Los memes más famosos de internet", "formato": "short", "tipo": "ranking", "categoria": "internet",
             "puntos": {"interes": 8, "originalidad": 7, "facilidad": 8, "riesgo_desinformacion": 2}}]})
        assert r == "2 ideas guardadas", r; ok += 1
        # 3) planificar → encarga 2 guiones (2 Shorts) respetando el cupo diario
        director.planificar(con, cfg)
        vids = con.execute("SELECT id, estado FROM videos").fetchall()
        assert len(vids) == 2 and all(v[1] == "guion" for v in vids), vids; ok += 1
        # 4) guion inválido → rechazado por formato y se vuelve a encargar
        t = cerebro.siguiente(con)
        assert t["agente"] == "guionista_short"; ok += 1
        malo = {**EJEMPLO, "frases": EJEMPLO["frases"][:3]}
        assert cerebro.entregar(con, t["tarea_id"], malo).startswith("RECHAZADO"); ok += 1
        t = cerebro.siguiente(con)
        assert t["agente"] == "guionista_short" and t["datos"].get("errores_formato"); ok += 1
        # 5) guion válido → pasa a verificación
        g = {k: v for k, v in EJEMPLO.items() if k != "verificacion"}
        assert "verificación" in cerebro.entregar(con, t["tarea_id"], g); ok += 1
        # 6) verificador encuentra un dato dudoso → vuelve al corrector
        t = cerebro.siguiente(con)
        assert t["agente"] == "verificador"; ok += 1
        res = cerebro.entregar(con, t["tarea_id"], {"datos": [
            {"dato": "4 M$", "estado": "verificado", "fuentes": ["https://x"]},
            {"dato": "80.000 M$", "estado": "dudoso", "fuentes": [], "nota": "el máximo fue unos 88.000 M$; vale «más de 80.000»"}]})
        assert "dudosos" in res; ok += 1
        t = cerebro.siguiente(con)
        assert t["agente"] == "corrector" and "80.000" in t["datos"]["instrucciones"][0]; ok += 1
        # 7) corrector + verificador OK → producción
        cerebro.entregar(con, t["tarea_id"], g)
        t = cerebro.siguiente(con)
        cerebro.entregar(con, t["tarea_id"], {"datos": [{"dato": "todo", "estado": "verificado", "fuentes": ["https://x"]}]})
        assert con.execute("SELECT estado FROM videos WHERE id=?", (t["video"]["id"],)).fetchone()[0] == "produccion"; ok += 1
        # 8) límites de gasto
        nucleo.apuntar_coste(con, "prueba", 0.5)
        try:
            nucleo.apuntar_coste(con, "prueba", 0.6)
            raise AssertionError("debía saltar el límite diario")
        except nucleo.LimiteSuperado:
            ok += 1
        # 9) parecido con vídeos anteriores
        assert calidad.parecido("La perrita del meme que vale millones", "La perrita del meme que vale millones 🐕 #shorts") > 0.9; ok += 1
        assert calidad.parecido("Fichajes más caros del fútbol", "El animal más rápido del mundo") < 0.2; ok += 1
        # 10) huecos del calendario: 14 Shorts y 2 largos por semana
        hs = director.huecos(cfg, 7)
        assert sum(f == "short" for f, _ in hs) == 14 and sum(f == "largo" for f, _ in hs) == 2; ok += 1
    print(f"OK: {ok} comprobaciones superadas")


if __name__ == "__main__":
    main()
