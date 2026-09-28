/**
 * Gate policies for the idea-to-MVP cycle, mirroring funilab.ideation.gates.
 *
 * The random streams differ from NumPy's, so a single run will not match Python draw for draw.
 * What must match is the accounting (asserted exactly on the deterministic no-gate policy) and
 * the distribution of outcomes (asserted against Python's replicated ranges).
 */

import { mean, probAbove, quantile } from './stats.js';

/** Small, fast, seedable PRNG (mulberry32). */
export function rng(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function gaussian(random) {
  const u = 1 - random();
  const v = random();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

/** Binomial draw: exact inversion for small means, normal approximation above. */
export function binomial(n, p, random) {
  if (n <= 0 || p <= 0) return 0;
  if (p >= 1) return n;
  if (p > 0.5) return n - binomial(n, 1 - p, random);
  const mu = n * p;
  if (mu < 40) {
    const q = 1 - p;
    const s = p / q;
    const a = (n + 1) * s;
    let r = q ** n;
    let u = random();
    let x = 0;
    while (u > r && x < n) {
      u -= r;
      x += 1;
      r *= a / x - s;
    }
    return x;
  }
  const draw = Math.round(mu + Math.sqrt(mu * (1 - p)) * gaussian(random));
  return Math.min(n, Math.max(0, draw));
}

export const rice = (idea) => (idea.reach * idea.impact * idea.confidence) / idea.effort;
export const ice = (idea) => (idea.impact / 3) * 10 * (idea.confidence * 10) * idea.ease;

/** Python's round(): half to even, which Math.round is not. */
export function roundHalfEven(x) {
  const r = Math.round(x);
  return Math.abs(x % 1) === 0.5 && r % 2 !== 0 ? r - 1 : r;
}

/** Column-oriented export (one array per field) to one object per idea. */
export function toRows(columns) {
  const keys = Object.keys(columns);
  return columns[keys[0]].map((_, i) => Object.fromEntries(keys.map((k) => [k, columns[k][i]])));
}

function passes(random, rates, n, bar, policy) {
  const size = rates.length;
  if (n === 0) return { ok: Array(size).fill(true), used: Array(size).fill(0) };
  const ok = [];
  const used = [];
  for (const rate of rates) {
    const k = binomial(n, rate, random);
    if (policy.reading === 'point') {
      ok.push(k / n >= bar);
      used.push(n);
      continue;
    }
    const p = probAbove(k, n, bar);
    if (p > policy.kill && p < policy.go) {
      const k2 = k + binomial(n, rate, random);
      ok.push(probAbove(k2, 2 * n, bar) >= policy.go);
      used.push(2 * n);
    } else {
      ok.push(p >= policy.go);
      used.push(n);
    }
  }
  return { ok, used };
}

/** Run every idea through the cycle under one policy; returns counts per stage and a summary. */
export function simulatePolicy(ideas, policy, costs, seed = 0) {
  const random = rng(seed);
  const n = ideas.length;
  const good = ideas.map((i) => Boolean(i.solution_fit));

  let order;
  if (policy.triage_score === 'none') {
    order = ideas.map((_, i) => [random(), i]).sort((x, y) => x[0] - y[0]).map((x) => x[1]);
  } else {
    const score = policy.triage_score === 'rice' ? rice : ice;
    order = ideas
      .map((idea, i) => [score(idea), random(), i])
      .sort((x, y) => y[0] - x[0] || x[1] - y[1])
      .map((x) => x[2]);
  }
  const triaged = Array(n).fill(false);
  order.slice(0, roundHalfEven(n * policy.triage_share)).forEach((i) => {
    triaged[i] = true;
  });

  const pain = passes(random, ideas.map((i) => i.true_pain_rate), policy.interviews,
    policy.pain_bar, policy);
  const signup = passes(random, ideas.map((i) => i.true_signup_rate), policy.visitors,
    policy.signup_bar, policy);
  const retained = passes(random, ideas.map((i) => i.true_retention), policy.mvp_users,
    policy.retention_bar, policy);

  const reached = [n, 0, 0, 0, 0, 0, 0];
  const s = {
    ideas: n, triaged: 0, mvps_built: 0, scaled: 0, good_scaled: 0, bad_scaled: 0,
    good_in_portfolio: good.filter(Boolean).length, false_kills: 0, triage_kills_of_good: 0,
    spend: 0, value_scaled: 0,
  };
  for (let i = 0; i < n; i += 1) {
    const problem = triaged[i] && pain.ok[i];
    const solution = problem && signup.ok[i];
    const validated = solution && retained.ok[i];
    [triaged[i], problem, solution, solution, validated, validated].forEach((hit, stage) => {
      if (hit) reached[stage + 1] += 1;
    });
    const smoke = signup.used[i] > 0 ? costs.smoke_fixed : 0;
    const mvpRound = retained.used[i] > 0 ? costs.mvp_fixed : 0;
    const spend = costs.triage
      + (triaged[i] ? costs.per_interview * pain.used[i] : 0)
      + (problem ? smoke + costs.per_visitor * signup.used[i] : 0)
      + (solution ? costs.mvp_build + mvpRound + costs.per_user * retained.used[i] : 0);
    s.spend += spend;
    if (triaged[i]) s.triaged += 1;
    if (solution) s.mvps_built += 1;
    if (validated) {
      s.scaled += 1;
      if (good[i]) {
        s.good_scaled += 1;
        s.value_scaled += ideas[i].value_if_scaled;
      } else {
        s.bad_scaled += 1;
        s.value_scaled -= costs.scale_investment;
      }
    }
    if (good[i] && triaged[i] && !validated) s.false_kills += 1;
    if (good[i] && !triaged[i]) s.triage_kills_of_good += 1;
  }
  s.cost_per_good_scaled = s.good_scaled ? s.spend / s.good_scaled : Infinity;
  s.net_value = s.value_scaled - s.spend;
  return { summary: s, reached };
}

/** Replicate a policy: mean and the 2.5-97.5% range of every summary metric. */
export function replicate(ideas, policy, costs, { replications = 30, seed = 0 } = {}) {
  const runs = [];
  for (let r = 0; r < replications; r += 1) {
    runs.push(simulatePolicy(ideas, policy, costs, seed * 1000 + r + 1));
  }
  const metrics = Object.keys(runs[0].summary);
  const out = {};
  for (const metric of metrics) {
    const values = runs.map((run) => run.summary[metric]);
    out[metric] = { mean: mean(values), low: quantile(values, 0.025), high: quantile(values, 0.975) };
  }
  out.reached = runs[0].reached.map((_, stage) => mean(runs.map((run) => run.reached[stage])));
  return out;
}
