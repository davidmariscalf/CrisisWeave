import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.CW_WEB_URL || 'http://127.0.0.1:8765';
const origin = new URL(base).origin;
const incidentUrl = new URL('/index.html', base).href;
const volunteerUrl = new URL('/volunteer.html', base).href;

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ serviceWorkers: 'allow' });

async function warm() {
  const page = await context.newPage();
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(String(error)));

  await page.goto(incidentUrl, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForSelector('.card', { timeout: 15000 });
  await page.evaluate(async () => {
    if (!('serviceWorker' in navigator)) throw new Error('service workers unavailable');
    await navigator.serviceWorker.ready;
  });
  assert.equal(pageErrors.length, 0, 'warm coordinator page emitted page errors');
  await page.close();
}

async function openOffline(url, selector, expectedStatus) {
  const page = await context.newPage();
  const externalRequests = [];
  const pageErrors = [];
  page.on('request', request => {
    const requestOrigin = new URL(request.url()).origin;
    if (requestOrigin !== origin) externalRequests.push(request.url());
  });
  page.on('pageerror', error => pageErrors.push(String(error)));

  const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
  assert.ok(response, 'offline navigation returned no response');
  assert.equal(response.status(), 200, 'offline navigation was not served successfully');
  await page.waitForSelector(selector, { timeout: 15000 });

  const status = (await page.locator('#connection, #connText').first().textContent())?.trim() || '';
  assert.match(status, expectedStatus, 'offline surface did not identify cached/offline state');
  assert.equal(pageErrors.length, 0, 'offline page emitted page errors');
  assert.deepEqual(externalRequests, [], 'offline page attempted an external request');

  await page.close();
}

try {
  await warm();
  await context.setOffline(true);
  await openOffline(incidentUrl, '.card', /offline|cached/i);
  await openOffline(volunteerUrl, '.card', /offline|cached/i);
  console.log('offline browser smoke test passed');
} finally {
  await browser.close();
}
