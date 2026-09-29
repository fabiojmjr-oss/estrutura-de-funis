// Hand calculations, and the gate simulator against Python's replicated results.

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

import { blendedVersusPaid, cacByModel } from '../js/engine/attribution.js';
import { funnelTable, leverTable, requiredTop } from '../js/engine/funnel.js';
import { binomial, replicate, rng, roundHalfEven, simulatePolicy, toRows } from '../js/engine/gates.js';
import { forecast } from '../js/engine/sales.js';
import { betaCdf, probAbove, quantile } from '../js/engine/stats.js';

const load = (name) => JSON.parse(readFileSync(new URL(`../data/${name}`, import.meta.url), 'utf8'));
const close = (a, b, tol = 1e-9) => assert.ok(Math.abs(a - b) <= tol, `${a} vs ${b}`);

test('beta CDF closed forms', () => {
  for (const x of [0.05, 0.3, 0.5, 0.9]) {
    close(betaCdf(x, 1, 1), x);
    close(betaCdf(x, 2, 1), x ** 2);
    close(betaCdf(x, 2, 2), 3 * x ** 2 - 2 * x ** 3);
  }
});

test('the uniform prior is not neutral at a low bar', () => {
  assert.ok(probAbove(0, 2, 0.04, [1, 1]) > 0.8);
  assert.ok(probAbove(0, 2, 0.04) < 0.5);
  close(probAbove(0, 0, 0.04), 0.5, 1e-9);
});

test('funnel table and reverse funnel by hand', () => {
  const rows = funnelTable(['A', 'B', 'C'], [1000, 500, 100]);
  close(rows[1].stepRate, 0.5);
  close(rows[2].stepRate, 0.2);
  close(rows[2].cumulativeRate, 0.1);
  assert.ok(rows[1].stepLow < 0.5 && rows[1].stepHigh > 0.5);
  close(requiredTop(80, [0.5, 0.2, 0.8]), 1000);
});

test('relative lifts are equal everywhere; a point is worth most at the lowest rate', () => {
  const rows = leverTable(['B', 'C', 'D'], [0.5, 0.2, 0.8], 1000);
  rows.forEach((row) => close(row.gainRelative, 8));
  assert.equal(rows[1].rankAbsolute, 1);
  close(rows[1].gainAbsolutePct, 0.05);
});

test('CAC by model and blended versus paid', () => {
  const journeys = [
    { path: ['Social', 'Busca'], customers: 1 },
    { path: ['Busca'], customers: 1 },
  ];
  const table = cacByModel(journeys, { Busca: 300, Social: 100 });
  const busca = table.find((r) => r.channel === 'Busca');
  close(busca.first, 300);
  close(busca.last, 150);
  const summary = blendedVersusPaid({ Pago: 2, Indicação: 1 }, { Pago: 1000 });
  close(summary.paid, 500);
  close(summary.blended, 1000 / 3);
});

test('forecast by hand, with and without stale deals', () => {
  const deals = [
    { stage: 'Q', amount: 100, days_in_stage: 5, won: true },
    { stage: 'Q', amount: 50, days_in_stage: 40, won: false },
  ];
  const all = forecast(deals, { Q: 0.4 });
  close(all.forecast, 60);
  const fresh = forecast(deals, { Q: 0.4 }, { staleAfter: { Q: 20 } });
  close(fresh.forecast, 40);
  assert.equal(fresh.staleCount, 1);
  close(fresh.error, -0.6);
});

test('Python rounding and quantiles', () => {
  assert.equal(roundHalfEven(2.5), 2);
  assert.equal(roundHalfEven(3.5), 4);
  assert.equal(roundHalfEven(376.8), 377);
  close(quantile([1, 2, 3, 4], 0.5), 2.5);
});

test('binomial draws have the right mean', () => {
  const random = rng(7);
  for (const [n, p] of [[5, 0.55], [600, 0.07], [2000, 0.4]]) {
    let total = 0;
    for (let i = 0; i < 4000; i += 1) total += binomial(n, p, random);
    close(total / 4000, n * p, 0.05 * n * p + 0.1);
  }
});

const ideation = load('ideation.json');
const ideas = toRows(ideation.ideas);
const reference = (policy, metric) => ideation.reference.find(
  (r) => r.policy === policy && r.metric === metric,
);

test('without gates the accounting matches Python exactly', () => {
  const policy = ideation.policies[0];
  const { summary } = simulatePolicy(ideas, policy, ideation.costs, 1);
  for (const metric of ['mvps_built', 'good_scaled', 'bad_scaled', 'spend', 'net_value']) {
    close(summary[metric], reference(policy.name, metric).mean, 1e-3);
  }
});

test('every gated policy lands inside the range Python reports', () => {
  for (const policy of ideation.policies.slice(1)) {
    const result = replicate(ideas, policy, ideation.costs, { replications: 30 });
    for (const metric of ['good_scaled', 'net_value']) {
      const { low, high } = reference(policy.name, metric);
      const value = result[metric].mean;
      assert.ok(value >= low && value <= high, `${policy.name} ${metric}: ${value} not in [${low}, ${high}]`);
    }
  }
});

test('the calibrated policy makes the most money in JavaScript too', () => {
  const nets = ideation.policies.map((policy) => [
    policy.name,
    replicate(ideas, policy, ideation.costs, { replications: 20 }).net_value.mean,
  ]);
  nets.sort((a, b) => b[1] - a[1]);
  assert.equal(nets[0][0], 'Calibrada');
});

test('URL parameters are validated: choices from a list, numbers clamped, junk ignored', async () => {
  const { param } = await import('../js/ui/state.js');
  assert.equal(param({ m: 'last' }, 'm', 'first', { oneOf: ['first', 'last'] }), 'last');
  assert.equal(param({ m: '<img>' }, 'm', 'first', { oneOf: ['first', 'last'] }), 'first');
  assert.equal(param({ x: '500' }, 'x', 10, { min: 0, max: 100 }), 100);
  assert.equal(param({ x: '1e309' }, 'x', 10), 10);
  assert.equal(param({ x: 'abc' }, 'x', 10), 10);
  assert.equal(param({}, 'constructor', 7), 7);
  assert.equal(param({ b: '1' }, 'b', false), true);
});
