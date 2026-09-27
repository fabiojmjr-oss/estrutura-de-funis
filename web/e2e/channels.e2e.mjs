// The page in a real browser, across the channels it claims to serve: desktop, phone, a shared
// link, dark mode, paper and offline. Run with `npm run e2e` (Chromium via Playwright).

import assert from 'node:assert/strict';
import { after, before, test } from 'node:test';

import { chromium } from 'playwright';

import { serve } from '../serve.mjs';

const TABS = ['overview', 'builder', 'multichannel', 'sales', 'supply', 'management', 'ideation'];
let server;
let browser;
let base;

before(async () => {
  server = await serve(0);
  base = `http://127.0.0.1:${server.address().port}/`;
  browser = await chromium.launch();
});

after(async () => {
  await browser?.close();
  server?.close();
});

async function page(options = {}) {
  const context = await browser.newContext(options);
  const p = await context.newPage();
  const errors = [];
  p.on('pageerror', (e) => errors.push(e.message));
  p.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  return { context, page: p, errors };
}

async function openTab(p, hash) {
  // A new hash on the same page does not reload it, so wait for *this* tab to be the one shown.
  const tab = hash.split('?')[0];
  await p.goto(`${base}#${hash}`);
  await p.waitForSelector('html[data-ready="true"]');
  await p.waitForSelector(`#tab-${tab}[aria-selected="true"]`);
  await p.waitForSelector(`#view[aria-labelledby="tab-${tab}"] .panel`);
}

test('every tab renders on desktop without a script error', async () => {
  const { context, page: p, errors } = await page({ viewport: { width: 1280, height: 900 } });
  for (const tab of TABS) {
    await openTab(p, tab);
    assert.equal(await p.getAttribute(`#tab-${tab}`, 'aria-selected'), 'true', tab);
    assert.ok((await p.locator('#view svg.chart').count()) > 0, `${tab} has no chart`);
  }
  assert.deepEqual(errors, []);
  await context.close();
});

test('on a phone no tab scrolls sideways', async () => {
  const { context, page: p, errors } = await page({ viewport: { width: 360, height: 780 }, isMobile: true, hasTouch: true });
  for (const tab of TABS) {
    await openTab(p, tab);
    const overflow = await p.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    assert.ok(overflow <= 1, `${tab} overflows by ${overflow}px`);
  }
  assert.deepEqual(errors, []);
  await context.close();
});

test('a shared link reopens the same scenario', async () => {
  const { context, page: p } = await page();
  await openTab(p, 'multichannel?modelo=first&v0=150');
  assert.equal(await p.isChecked('input[name="modelo"][value="first"]'), true);
  assert.equal(await p.inputValue('input[data-param="v0"]'), '150');

  await openTab(p, 'ideation?politica=Sem%20gates');
  await p.waitForSelector('#out .kpi-value');
  const net = await p.textContent('#out .kpi .kpi-value');
  assert.match(net, /-124,6 mi/, 'no-gates net value should match the Python reference exactly');
  await context.close();
});

test('changing a control writes the scenario into the URL', async () => {
  const { context, page: p } = await page();
  await openTab(p, 'sales');
  await p.check('input[name="odds"][value="crm"]', { force: true });
  // replaceState is a same-document navigation; wait for it rather than reading p.url() once.
  await p.waitForURL(/odds=crm/);
  await openTab(p, 'builder');
  await p.fill('input[data-param="alvo"]', '500');
  await p.waitForURL(/alvo=500/);
  assert.match(await p.evaluate(() => window.location.hash), /alvo=500/);
  await context.close();
});

test('dark mode and print are styled, not ignored', async () => {
  const { context, page: p } = await page({ colorScheme: 'dark' });
  await openTab(p, 'overview');
  const dark = await p.evaluate(() => getComputedStyle(document.body).backgroundColor);
  assert.notEqual(dark, 'rgb(245, 247, 250)');
  await p.emulateMedia({ media: 'print' });
  assert.equal(await p.isVisible('.tabs'), false);
  assert.equal(await p.isVisible('.print-params'), true);
  await context.close();
});

test('after one visit the page works offline', async () => {
  const { context, page: p } = await page();
  await openTab(p, 'overview');
  await p.evaluate(async () => {
    const registration = await navigator.serviceWorker.ready;
    return registration.active?.state;
  });
  await p.reload();
  await p.waitForSelector('html[data-ready="true"]');
  await context.setOffline(true);
  await p.reload();
  await p.waitForSelector('html[data-ready="true"]', { timeout: 10000 });
  assert.ok((await p.locator('#view svg.chart').count()) > 0);
  await context.close();
});
