// Shared Chromium launcher for the dashboard checks.
// Uses the image's Playwright headless shell in /opt/ms-playwright: it ships with the sandbox image,
// so a restart cannot strip its libraries. MM_CHROMIUM overrides it. Each candidate is run with
// --version first, so a broken one is skipped. With none, Playwright's own browser download is used.
import { chromium } from 'playwright-core';
import { execFileSync } from 'node:child_process';
import { readdirSync } from 'node:fs';

function candidates() {
  const out = [];
  if (process.env.MM_CHROMIUM) out.push(process.env.MM_CHROMIUM);
  try {
    for (const d of readdirSync('/opt/ms-playwright').sort().reverse()) {
      if (d.startsWith('chromium_headless_shell-')) out.push(`/opt/ms-playwright/${d}/chrome-headless-shell-linux64/chrome-headless-shell`);
      else if (d.startsWith('chromium-')) out.push(`/opt/ms-playwright/${d}/chrome-linux64/chrome`);
    }
  } catch {}
  return out;
}

export function pickBrowser() {
  const errs = [];
  for (const exe of candidates()) {
    try { execFileSync(exe, ['--version'], { stdio: 'pipe', timeout: 20000 }); return exe; }
    catch (e) { errs.push(`${exe}: ${String(e.stderr || e.message).trim().split('\n')[0]}`); }
  }
  if (errs.length) console.error('skipped:\n  ' + errs.join('\n  '));
  return null; // Playwright's own download (CI: npx playwright install chromium-headless-shell)
}

export async function launch(opts = {}) {
  const exe = pickBrowser();
  return chromium.launch({ args: ['--no-sandbox', '--disable-gpu'], ...opts, ...(exe ? { executablePath: exe } : {}) });
}
