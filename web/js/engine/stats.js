/**
 * Statistics for gate decisions, mirroring funilab.ideation.evidence and funilab.core.
 *
 * No dependencies: the regularised incomplete beta function is computed by continued fraction
 * (modified Lentz), the log-gamma by Lanczos. Every function here is asserted against Python's
 * answers in web/tests/parity.test.mjs, so the page and the library cannot quietly disagree.
 */

const FPMIN = 1e-300;
const LANCZOS = [
  0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
  -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6,
  1.5056327351493116e-7,
];

/** Natural log of the gamma function (Lanczos, g = 7). */
export function lgamma(z) {
  if (z < 0.5) {
    return Math.log(Math.PI / Math.abs(Math.sin(Math.PI * z))) - lgamma(1 - z);
  }
  const x = z - 1;
  let sum = LANCZOS[0];
  for (let i = 1; i < 9; i += 1) sum += LANCZOS[i] / (x + i);
  const t = x + 7.5;
  return 0.5 * Math.log(2 * Math.PI) + (x + 0.5) * Math.log(t) - t + Math.log(sum);
}

function betacf(a, b, x) {
  const qab = a + b;
  const qap = a + 1;
  const qam = a - 1;
  let c = 1;
  let d = 1 - (qab * x) / qap;
  if (Math.abs(d) < FPMIN) d = FPMIN;
  d = 1 / d;
  let h = d;
  for (let m = 1; m <= 300; m += 1) {
    const m2 = 2 * m;
    let aa = (m * (b - m) * x) / ((qam + m2) * (a + m2));
    d = 1 + aa * d;
    if (Math.abs(d) < FPMIN) d = FPMIN;
    c = 1 + aa / c;
    if (Math.abs(c) < FPMIN) c = FPMIN;
    d = 1 / d;
    h *= d * c;
    aa = (-(a + m) * (qab + m) * x) / ((a + m2) * (qap + m2));
    d = 1 + aa * d;
    if (Math.abs(d) < FPMIN) d = FPMIN;
    c = 1 + aa / c;
    if (Math.abs(c) < FPMIN) c = FPMIN;
    d = 1 / d;
    const delta = d * c;
    h *= delta;
    if (Math.abs(delta - 1) < 3e-16) break;
  }
  return h;
}

/** P(X <= x) for X ~ Beta(a, b). */
export function betaCdf(x, a, b) {
  if (x <= 0) return 0;
  if (x >= 1) return 1;
  const front = Math.exp(
    lgamma(a + b) - lgamma(a) - lgamma(b) + a * Math.log(x) + b * Math.log1p(-x),
  );
  if (x < (a + 1) / (a + b + 2)) return (front * betacf(a, b, x)) / a;
  return 1 - (front * betacf(b, a, 1 - x)) / b;
}

const priorCache = new Map();

/** Beta (a, b) with a + b = weight and its median exactly on the bar: even odds before data. */
export function neutralPrior(bar, weight = 2) {
  if (!(bar > 0 && bar < 1)) throw new RangeError('bar must be strictly between 0 and 1');
  const key = `${bar}|${weight}`;
  if (priorCache.has(key)) return priorCache.get(key);
  let low = 1e-9;
  let high = weight - 1e-9;
  for (let i = 0; i < 80; i += 1) {
    const a = (low + high) / 2;
    if (betaCdf(bar, a, weight - a) > 0.5) low = a;
    else high = a;
  }
  const a = (low + high) / 2;
  const prior = [a, weight - a];
  priorCache.set(key, prior);
  return prior;
}

/** Posterior probability that the true rate exceeds the bar. */
export function probAbove(k, n, bar, prior = null) {
  const [a, b] = prior ?? neutralPrior(bar);
  return 1 - betaCdf(bar, a + k, b + n - k);
}

/** 'go', 'kill' or 'more evidence'. */
export function decide(k, n, bar, { go = 0.8, kill = 0.2, prior = null } = {}) {
  if (!(kill >= 0 && kill < go && go <= 1)) throw new RangeError('need 0 <= kill < go <= 1');
  const p = probAbove(k, n, bar, prior);
  if (p >= go) return 'go';
  if (p <= kill) return 'kill';
  return 'more evidence';
}

/** Smallest sample at which an idea performing at the expected rate reaches a decision. */
export function sampleSize(expectedRate, bar, { go = 0.8, prior = null, maxN = 100000 } = {}) {
  if (expectedRate === bar) throw new RangeError('an idea exactly at the bar never decides');
  const above = expectedRate > bar;
  const decided = (n) => {
    const p = probAbove(n * expectedRate, n, bar, prior);
    return above ? p >= go : p <= 1 - go;
  };
  const candidates = [];
  const logMax = Math.log10(maxN);
  for (let i = 0; i < 600; i += 1) {
    const n = Math.round(10 ** ((logMax * i) / 599));
    if (candidates[candidates.length - 1] !== n) candidates.push(n);
  }
  const first = candidates.findIndex(decided);
  if (first < 0) throw new RangeError(`no sample up to ${maxN} reaches a decision`);
  const lower = candidates[Math.max(first - 1, 0)];
  for (let n = lower; n <= candidates[first]; n += 1) if (decided(n)) return n;
  return candidates[first];
}

/** Inverse of the standard normal CDF (Acklam, relative error below 1.2e-9). */
export function normalQuantile(p) {
  const a = [-39.69683028665376, 220.9460984245205, -275.9285104469687, 138.357751867269,
    -30.66479806614716, 2.506628277459239];
  const b = [-54.47609879822406, 161.5858368580409, -155.6989798598866, 66.80131188771972,
    -13.28068155288572];
  const c = [-0.007784894002430293, -0.3223964580411365, -2.400758277161838,
    -2.549732539343734, 4.374664141464968, 2.938163982698783];
  const d = [0.007784695709041462, 0.3224671290700398, 2.445134137142996, 3.754408661907416];
  const low = 0.02425;
  if (p < low) {
    const q = Math.sqrt(-2 * Math.log(p));
    return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
      / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
  }
  if (p > 1 - low) return -normalQuantile(1 - p);
  const q = p - 0.5;
  const r = q * q;
  return ((((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q)
    / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
}

/** Wilson score interval for k successes in n trials. */
export function wilson(k, n, confidence = 0.95) {
  if (n <= 0) return [NaN, NaN];
  const z = normalQuantile(0.5 + confidence / 2);
  const p = k / n;
  const denominator = 1 + (z * z) / n;
  const centre = (p + (z * z) / (2 * n)) / denominator;
  const half = (z * Math.sqrt((p * (1 - p)) / n + (z * z) / (4 * n * n))) / denominator;
  return [centre - half, centre + half];
}

/** Linear-interpolation quantile, as pandas computes it. */
export function quantile(values, q) {
  const sorted = values.filter((v) => Number.isFinite(v)).sort((x, y) => x - y);
  if (!sorted.length) return NaN;
  const position = (sorted.length - 1) * q;
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  return sorted[lower] + (sorted[upper] - sorted[lower]) * (position - lower);
}

export function mean(values) {
  const finite = values.filter((v) => Number.isFinite(v));
  return finite.length ? finite.reduce((s, v) => s + v, 0) / finite.length : NaN;
}
