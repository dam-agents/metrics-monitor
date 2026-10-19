// Screenshot a built dashboard, to look at it before publishing (then open the PNG).
//   node scripts/browser/shot.mjs <file.html> <out.png> [light|dark] [width] [range]
import { launch } from './browser.mjs';
import { resolve } from 'node:path';
const [,, file, out, theme = 'light', width = '1320', range] = process.argv;
const b = await launch();
const p = await b.newPage({ viewport: { width: +width, height: 900 }, colorScheme: theme });
const errs = []; p.on('pageerror', e => errs.push(String(e)));
await p.goto('file://' + resolve(file)); await p.waitForTimeout(300);
if (range) { await p.evaluate(r => document.querySelector(`#range button[data-r="${r}"]`).click(), range); await p.waitForTimeout(200); }
await p.screenshot({ path: out, fullPage: true });
console.log(errs.length ? 'ERRORS:\n' + errs.join('\n') : `saved ${out}`);
await b.close();
