"""Pruebas de distribución YouTube + TikTok sin red.  python -m autopilot.pruebas.test_distribucion"""
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from autopilot import ceo, distribucion as D, nucleo, tiktok as TT


def main():
    nucleo.DB_RUTA = Path(tempfile.mkdtemp()) / "d.db"
    avisos, subidas = [], []
    ok = 0
    TT.conectado = lambda: True
    fallar = {"n": 2}

    def publicar_falso(video, titulo):
        subidas.append(titulo)
        if fallar["n"] > 0:
            fallar["n"] -= 1
            raise RuntimeError("TikTok 503")
        return {"publish_id": "P1", "modo": "inbox"}
    TT.publicar = publicar_falso
    with nucleo.db() as con:
        g = {"titulo": "Pagó 6 millones por un plátano 🍌 #shorts", "etiquetas": ["arte", "subastas"]}
        con.execute("INSERT INTO videos (id, formato, estado, version, carpeta, guion, titulo) VALUES (?,?,?,?,?,?,?)",
                    ("s1", "short", "programado", 2, "x", json.dumps(g), g["titulo"]))
        v = nucleo.fila(con.execute("SELECT * FROM videos WHERE id='s1'").fetchone())
        hora = (datetime.now(timezone.utc) - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:00.000Z")
        D.preparar(con, v, hora, "YT1")
        D.preparar(con, v, hora, "YT1")   # repetir no duplica
        assert con.execute("SELECT COUNT(*) FROM publicaciones").fetchone()[0] == 2; ok += 1
        # 1º intento: TikTok falla → solo TikTok queda para reintentar; YouTube publicado UNA vez
        D.ejecutar(con, avisos.append)
        est = dict(con.execute("SELECT plataforma, estado FROM publicaciones").fetchall())
        assert est == {"youtube": "publicado", "tiktok": "reintentar"}, est; ok += 1
        # 2º intento falla, 3º funciona
        D.ejecutar(con, avisos.append); D.ejecutar(con, avisos.append)
        est = dict(con.execute("SELECT plataforma, estado FROM publicaciones").fetchall())
        assert est["tiktok"] == "en_borradores" and len(subidas) == 3; ok += 1
        assert "#shorts" not in subidas[0] and "#shockmental" in subidas[0]; ok += 1   # título adaptado a TikTok
        assert any("Diferencia con YouTube" in a for a in avisos); ok += 1
        # nunca más: ejecutar otra vez no vuelve a subir nada
        D.ejecutar(con, avisos.append)
        assert len(subidas) == 3; ok += 1
        # tres fallos seguidos → fallido + decisión para el gerente, sin tocar YouTube
        con.execute("INSERT INTO videos (id, formato, estado, version, carpeta, guion, titulo) VALUES (?,?,?,?,?,?,?)",
                    ("s2", "short", "programado", 1, "x", json.dumps(g), "otro"))
        D.preparar(con, nucleo.fila(con.execute("SELECT * FROM videos WHERE id='s2'").fetchone()), hora, "YT2")
        fallar["n"] = 99
        for _ in range(4):
            D.ejecutar(con, avisos.append)
        assert con.execute("SELECT estado FROM publicaciones WHERE video_id='s2' AND plataforma='tiktok'").fetchone()[0] == "fallido"; ok += 1
        assert con.execute("SELECT COUNT(*) FROM decisiones WHERE requiere_gerente=1").fetchone()[0] == 1; ok += 1
        # versión cambiada tras aprobar → TikTok se cancela (no se publica una versión no aprobada)
        con.execute("INSERT INTO videos (id, formato, estado, version, carpeta, guion, titulo) VALUES (?,?,?,?,?,?,?)",
                    ("s3", "short", "programado", 1, "x", json.dumps(g), "v"))
        D.preparar(con, nucleo.fila(con.execute("SELECT * FROM videos WHERE id='s3'").fetchone()), hora, "YT3")
        con.execute("UPDATE videos SET version=2 WHERE id='s3'")
        D.ejecutar(con, avisos.append)
        assert con.execute("SELECT estado FROM publicaciones WHERE video_id='s3' AND plataforma='tiktok'").fetchone()[0] == "cancelado"; ok += 1
        # informe del CEO
        txt = ceo.informe(con, nucleo.config(), "semanal")
        assert "Informe semanal" in txt and "Objetivo 200" in txt; ok += 1
    print(f"OK: {ok} comprobaciones de distribución superadas")


if __name__ == "__main__":
    main()
