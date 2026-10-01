// Screenshots the dashboard (Nipah glycoprotein G, the default target) for docs/screenshot.jpg.
// Run against a stack already up at http://localhost:5173 — see
// .github/workflows/update-screenshot.yml, or run locally after `docker compose up -d`.
import { chromium } from 'playwright';

const url = process.env.DASHBOARD_URL ?? 'http://localhost:5173';
const out = process.env.SCREENSHOT_PATH ?? 'docs/screenshot.jpg';

const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForSelector('text=Hit rate by design method');
  // Let the chart finish its entry animation before capturing.
  await page.waitForTimeout(500);
  await page.screenshot({ path: out, type: 'jpeg', quality: 90 });
  console.log(`Saved ${out}`);
} finally {
  await browser.close();
}
