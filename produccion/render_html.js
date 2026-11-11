// node render_html.js <archivo.html> <salida.png> <ancho> <alto>  → PNG con fondo transparente
const { chromium } = require('playwright');
(async () => {
  const [html, out, w, h] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: +w, height: +h } });
  await p.goto('file://' + html); await p.evaluate(() => document.fonts.ready);
  await p.screenshot({ path: out, omitBackground: true }); await b.close();
})();
