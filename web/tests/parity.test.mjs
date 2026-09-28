// The JavaScript engine against Python's answers, from web/data/parity.json.
//
// python -m funilab.export writes the vectors; this suite asserts the page computes the same
// thing. A formula changed on one side and not the other fails here, not in front of a user.

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

import { attribute, MODELS } from '../js/engine/attribution.js';
import { betaCdf, decide, neutralPrior, probAbove, sampleSize, wilson } from '../js/engine/stats.js';

const parity = JSON.parse(readFileSync(new URL('../data/parity.json', import.meta.url), 'utf8'));
const close = (actual, expected, tol, label) => assert.ok(
  Math.abs(actual - expected) <= tol, `${label}: ${actual} vs ${expected}`,
);

test('beta CDF matches Python', () => {
  for (const { x, a, b, value } of parity.beta_cdf) close(betaCdf(x, a, b), value, 1e-6, `B(${x};${a},${b})`);
});

test('neutral prior matches Python', () => {
  for (const { bar, prior } of parity.neutral_prior) {
    const [a, b] = neutralPrior(bar);
    close(a, prior[0], 1e-6, `a at ${bar}`);
    close(b, prior[1], 1e-6, `b at ${bar}`);
  }
});

test('posterior probability matches Python', () => {
  for (const { k, n, bar, value } of parity.prob_above) close(probAbove(k, n, bar), value, 1e-6, `${k}/${n} > ${bar}`);
});

test('gate decisions match Python', () => {
  for (const { k, n, bar, go, kill, value } of parity.decide) {
    assert.equal(decide(k, n, bar, { go, kill }), value, `${k}/${n}`);
  }
});

test('sample sizes match Python exactly', () => {
  for (const { rate, bar, go, value } of parity.sample_size) {
    assert.equal(sampleSize(rate, bar, { go }), value, `${rate} vs ${bar} at ${go}`);
  }
});

test('Wilson interval matches Python', () => {
  for (const { k, n, low, high } of parity.wilson) {
    const [lo, hi] = wilson(k, n);
    close(lo, low, 1e-6, `low ${k}/${n}`);
    close(hi, high, 1e-6, `high ${k}/${n}`);
  }
});

test('attribution matches Python under every model', () => {
  const journeys = parity.attribution.journeys.map((path) => ({ path, customers: 1 }));
  for (const model of MODELS) {
    const credit = attribute(journeys, model);
    for (const [channel, value] of Object.entries(parity.attribution.credits[model])) {
      close(credit[channel] ?? 0, value, 1e-6, `${model}/${channel}`);
    }
  }
});
