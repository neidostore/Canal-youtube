// node render_html.js <archivo.html> <salida.png> <ancho> <alto>  → PNG con fondo transparente
const { chromium } = require('playwright');
const { pathToFileURL } = require('url'), path = require('path');
(async () => {
  const [html, out, w, h] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: +w, height: +h } });
  await p.goto(pathToFileURL(path.resolve(html)).href); await p.evaluate(() => document.fonts.ready);
  await p.screenshot({ path: out, omitBackground: true }); await b.close();
})();
