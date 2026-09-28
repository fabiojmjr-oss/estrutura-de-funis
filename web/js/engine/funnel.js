/** Funnel arithmetic, mirroring funilab.core.conversion and funilab.core.levers. */

import { wilson } from './stats.js';

/** Step and cumulative rates, with a Wilson interval on each step. */
export function funnelTable(stages, counts) {
  if (stages.length !== counts.length) throw new RangeError('stages and counts differ in length');
  return stages.map((stage, i) => {
    const entered = counts[i];
    const previous = i === 0 ? null : counts[i - 1];
    const stepRate = previous ? entered / previous : null;
    const [low, high] = previous ? wilson(Math.min(entered, previous), previous) : [null, null];
    return {
      stage,
      entered,
      stepRate,
      stepLow: low,
      stepHigh: high,
      cumulativeRate: counts[0] ? entered / counts[0] : null,
    };
  });
}

export function expectedOutput(top, rates) {
  return rates.reduce((acc, r) => acc * r, top);
}

/** The reverse funnel: entries needed at the top to deliver the target at the bottom. */
export function requiredTop(target, rates) {
  const product = rates.reduce((acc, r) => acc * r, 1);
  if (product <= 0) throw new RangeError('a zero rate makes every target unreachable');
  return target / product;
}

/** Output gain from lifting each step rate by points and by percent. */
export function leverTable(labels, rates, top, { absolute = 0.01, relative = 0.1 } = {}) {
  if (rates.some((r) => !(r > 0 && r <= 1))) throw new RangeError('rates must be in (0, 1]');
  const base = expectedOutput(top, rates);
  const rows = rates.map((rate, i) => {
    const gainAbsolute = base * (Math.min(rate + absolute, 1) / rate - 1);
    return {
      transition: labels[i],
      rate,
      gainAbsolute,
      gainAbsolutePct: gainAbsolute / base,
      gainRelative: base * (Math.min(rate * (1 + relative), 1) / rate - 1),
    };
  });
  const ordered = [...rows].sort((x, y) => y.gainAbsolute - x.gainAbsolute);
  rows.forEach((row) => {
    row.rankAbsolute = ordered.findIndex((o) => o.gainAbsolute === row.gainAbsolute) + 1;
  });
  return rows;
}
