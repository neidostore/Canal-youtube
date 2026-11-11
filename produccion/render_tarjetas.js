// node render_tarjetas.js <tarjetas.json> <carpeta_salida>  → card_<id>.png (1920x1080)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const [json, out, plantilla = 'tarjetas.html'] = process.argv.slice(2);
  const cards = JSON.parse(fs.readFileSync(json, 'utf8'));
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  for (const [k, card] of Object.entries(cards)) {
    await p.goto('file://' + path.join(__dirname, plantilla) + '?k=' + k + '#' + encodeURIComponent(JSON.stringify(card)));
    await p.evaluate(() => document.fonts.ready);
    await p.waitForTimeout(150);
    await p.locator('#c').screenshot({ path: path.join(out, `card_${k}.png`) });
  }
  await b.close();
})();
