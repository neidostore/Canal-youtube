// node generar-v2.js salida.png '{"layout":"heroe","categoria":"misterio","fondo":"ruta.jpg","texto":"¿ESTÁ|*AQUÍ*?"}'
// Escribe la miniatura y, en stdout, la caja del texto (para la prueba de legibilidad en móvil).
// Con "sin_texto": true genera solo el fondo (para medir el contraste detrás del texto).
const { chromium } = require('playwright'); const path = require('path'); const { pathToFileURL } = require('url');
(async () => {
  const [out, json] = process.argv.slice(2); const q = JSON.parse(json);
  for (const k of ['fondo', 'fondo2']) if (q[k] && !/^(https?|file):/.test(q[k])) q[k] = pathToFileURL(path.resolve(__dirname, q[k])).href;
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  await p.goto(pathToFileURL(path.join(__dirname, 'plantilla-v2.html')).href + '#' + encodeURIComponent(JSON.stringify(q)));
  await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(400);
  const caja = await p.evaluate(() => { const r = document.getElementById('txt').getBoundingClientRect();
    const lineas = [...document.querySelectorAll('.w')].map(e => parseFloat(getComputedStyle(e).fontSize));
    return { x: r.x, y: r.y, w: r.width, h: r.height, fuente_px: Math.min(...lineas, 999), lineas: lineas.length }; });
  await p.locator('#t').screenshot({ path: out }); await b.close();
  console.log(JSON.stringify(caja));
})();
