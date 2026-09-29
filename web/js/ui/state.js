/**
 * Scenario state in the URL hash: #tab?key=value&...
 *
 * The URL is the channel-neutral carrier of a scenario. A link pasted into WhatsApp, an e-mail
 * or a LinkedIn post reopens the same tab with the same parameters on any device, with no server
 * and no account.
 */

export function readHash(hash = window.location.hash) {
  const raw = hash.replace(/^#/, '');
  const [tab, query = ''] = raw.split('?');
  const params = Object.fromEntries(new URLSearchParams(query));
  return { tab: tab || 'overview', params };
}

export function writeHash(tab, params) {
  const query = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ''),
  ).toString();
  const hash = `#${tab}${query ? `?${query}` : ''}`;
  if (window.location.hash !== hash) window.history.replaceState(null, '', hash);
  return window.location.href;
}

/**
 * Typed, validated read of one parameter.
 *
 * A shared link is input from anyone, so a value outside what the control can produce falls back
 * to the default rather than reaching the engine: ``oneOf`` for choices, ``min``/``max`` for
 * numbers (clamped). A malformed link then opens a sensible scenario instead of a broken tab.
 */
export function param(params, key, fallback, { oneOf = null, min = -Infinity, max = Infinity } = {}) {
  if (!Object.hasOwn(params, key)) return fallback;
  const value = params[key];
  if (typeof fallback === 'number') {
    const n = Number(value);
    return Number.isFinite(n) ? Math.min(max, Math.max(min, n)) : fallback;
  }
  if (typeof fallback === 'boolean') return value === '1' || value === 'true';
  if (oneOf && !oneOf.includes(value)) return fallback;
  return value;
}
