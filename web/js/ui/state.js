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

/** Typed read of one parameter with a default. */
export function param(params, key, fallback) {
  if (!(key in params)) return fallback;
  const value = params[key];
  if (typeof fallback === 'number') {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
  }
  if (typeof fallback === 'boolean') return value === '1' || value === 'true';
  return value;
}
