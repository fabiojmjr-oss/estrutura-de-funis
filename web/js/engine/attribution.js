/** Multi-channel attribution and CAC, mirroring funilab.marketing.acquisition. */

export const MODELS = ['first', 'last', 'linear', 'position'];
export const MODEL_LABELS = {
  first: 'Primeiro toque',
  last: 'Último toque',
  linear: 'Linear',
  position: 'Posição (40/20/40)',
};

function weights(size, model) {
  if (model === 'first') return Array.from({ length: size }, (_, i) => (i === 0 ? 1 : 0));
  if (model === 'last') return Array.from({ length: size }, (_, i) => (i === size - 1 ? 1 : 0));
  if (model === 'linear') return Array(size).fill(1 / size);
  if (model === 'position') {
    if (size === 1) return [1];
    if (size === 2) return [0.5, 0.5];
    const middle = 0.2 / (size - 2);
    return Array.from({ length: size }, (_, i) => (i === 0 || i === size - 1 ? 0.4 : middle));
  }
  throw new RangeError(`unknown attribution model ${model}`);
}

/**
 * Customers credited to each channel.
 * @param {{path: string[], customers: number}[]} journeys converting journeys and their counts
 */
export function attribute(journeys, model) {
  const credit = {};
  for (const { path, customers } of journeys) {
    const w = weights(path.length, model);
    path.forEach((channel, i) => {
      credit[channel] = (credit[channel] ?? 0) + w[i] * customers;
    });
  }
  return credit;
}

/** CAC and rank (1 = cheapest) per paid channel under every model. */
export function cacByModel(journeys, spend) {
  const paid = Object.keys(spend).filter((c) => spend[c] > 0);
  const table = paid.map((channel) => ({ channel, spend: spend[channel] }));
  for (const model of MODELS) {
    const credit = attribute(journeys, model);
    table.forEach((row) => {
      row[model] = credit[row.channel] ? row.spend / credit[row.channel] : Infinity;
    });
    const ranked = [...table].sort((x, y) => x[model] - y[model]);
    table.forEach((row) => {
      row[`rank_${model}`] = ranked.indexOf(row) + 1;
    });
  }
  return table;
}

/** Blended against paid CAC: the denominator is a decision. */
export function blendedVersusPaid(customersBySource, spend) {
  const totalSpend = Object.values(spend).reduce((s, v) => s + v, 0);
  const paidCustomers = Object.keys(spend)
    .filter((c) => spend[c] > 0)
    .reduce((s, c) => s + (customersBySource[c] ?? 0), 0);
  const allCustomers = Object.values(customersBySource).reduce((s, v) => s + v, 0);
  return {
    spend: totalSpend,
    paidCustomers,
    allCustomers,
    paid: totalSpend / paidCustomers,
    blended: totalSpend / allCustomers,
  };
}
