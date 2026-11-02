// Genera una miniatura con foto: node miniaturas/generar.js salida.png "modo=dividida&izq=fotos/a.jpg&der=fotos/b.jpg&t1=NO ES LA&t2=COMIDA&tachar=1&etiqueta=$"
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [out, params] = process.argv.slice(2);
  const base = path.resolve(__dirname);
  const q = new URLSearchParams(params);
  for (const k of ['izq','der','fondo']) if (q.get(k)) q.set(k, 'file://' + path.resolve(base, q.get(k)));
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  await p.goto('file://' + base + '/plantilla-fotos.html?' + q.toString());
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(400);
  await p.locator('#mini').screenshot({ path: out });
  await b.close();
})();
