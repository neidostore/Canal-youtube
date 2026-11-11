// node generar-shock.js salida.png '{"fondo":"shock01/fondo-coche.png","l1":"¿VUELA","l2":"O SALTA?","chip":"+11 COSAS IMPOSIBLES"}'
const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const [out, json] = process.argv.slice(2); const q = JSON.parse(json);
  if (q.fondo) q.fondo = 'file://' + path.resolve(__dirname, q.fondo);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  await p.goto('file://' + __dirname + '/plantilla-shock.html#' + encodeURIComponent(JSON.stringify(q)));
  await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(300);
  await p.locator('#t').screenshot({ path: out }); await b.close();
})();
