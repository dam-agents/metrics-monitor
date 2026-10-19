// Click through every range of a built dashboard, in light and dark, and report page errors and
// values that read NaN / undefined / Infinity. Prints only "done" when nothing is wrong.
//   node scripts/browser/check.mjs <dashboard.html>
import { launch } from './browser.mjs';
import { resolve } from 'node:path';
const file = resolve(process.argv[2]);
const b = await launch();
for (const scheme of ['light', 'dark']) {
  const p = await b.newPage({ viewport: { width: 1320, height: 900 }, colorScheme: scheme });
  let errs = [];
  p.on('pageerror', e => errs.push(String(e).slice(0, 200)));
  p.on('console', m => m.type() === 'error' && errs.push(m.text().slice(0, 200)));
  await p.goto('file://' + file); await p.waitForTimeout(300);
  const ranges = await p.evaluate(() => [...document.querySelectorAll('#range button')].map(b => b.dataset.r));
  if (!ranges.length) console.log(`${scheme}: no range buttons found`);
  for (const r of ranges) {
    await p.evaluate(r => document.querySelector(`#range button[data-r="${r}"]`).click(), r);
    await p.waitForTimeout(100);
    const text = await p.evaluate(() => document.querySelector('main').innerText);
    const bad = text.match(/.{0,40}\b(NaN|undefined|Infinity)\b.{0,20}/);
    const charts = await p.evaluate(() => document.querySelectorAll('#cards .card').length);
    if (errs.length || bad || !charts) console.log(`${scheme} ${r}: ${errs.join(' ; ')}${bad ? ' text: ' + bad[0] : ''}${charts ? '' : ' no charts'}`);
    errs = [];
  }
  await p.close();
}
console.log('done');
await b.close();
