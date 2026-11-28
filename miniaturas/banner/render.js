// node render.js → banner.png (2560×1440 para subir) y vistas previas de ordenador y móvil
const { chromium } = require('playwright'); const path = require('path'); const { pathToFileURL } = require('url');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 2560, height: 1440 } });
  const url = pathToFileURL(path.join(__dirname, 'banner.html')).href;
  await p.goto(url); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(500);
  await p.locator('#b').screenshot({ path: path.join(__dirname, 'banner.png') });
  await p.screenshot({ path: path.join(__dirname, 'vista-ordenador.png'), clip: { x: 0, y: 508, width: 2560, height: 423 } });
  await p.screenshot({ path: path.join(__dirname, 'vista-movil.png'), clip: { x: 507, y: 508, width: 1546, height: 423 } });
  await b.close(); console.log('ok');
})();
