/** Brazilian formatting, one place. */

const number = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
const decimal1 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const decimal2 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export const int = (v) => (Number.isFinite(v) ? number.format(v) : '—');
export const dec1 = (v) => (Number.isFinite(v) ? decimal1.format(v) : '—');
export const dec2 = (v) => (Number.isFinite(v) ? decimal2.format(v) : '—');
export const pct = (v, digits = 1) => (Number.isFinite(v)
  ? `${new Intl.NumberFormat('pt-BR', { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(v * 100)}%`
  : '—');
export const signedPct = (v, digits = 1) => (Number.isFinite(v) ? `${v > 0 ? '+' : ''}${pct(v, digits)}` : '—');
export const brl = (v) => (Number.isFinite(v) ? `R$ ${number.format(v)}` : '—');
export const brlM = (v) => (Number.isFinite(v) ? `R$ ${decimal1.format(v / 1e6)} mi` : '—');

/** Escape text before it goes into innerHTML (stage names are typed by the user). */
export function esc(text) {
  return String(text)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}
