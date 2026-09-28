/**
 * Inline SVG charts. No library, so the page works offline and prints sharply; colours come from
 * CSS classes, so both themes and paper are handled by the stylesheet.
 */

import { esc } from './format.js';

/** Chart width that keeps 12 px text legible: the space available, between 300 and 640. */
export function autoWidth(el = document.getElementById('view')) {
  const available = (el?.clientWidth ?? 640) - 48;
  return Math.round(Math.min(640, Math.max(300, available)));
}

const svg = (width, height, body, label) => `<svg class="chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(label)}">${body}</svg>`;

/**
 * Horizontal funnel: one centred bar per stage, width proportional to the count.
 * @param rows {label, value, note}
 */
export function funnelChart(rows, { label = 'Funil', width = autoWidth() } = {}) {
  if (width < 480) return compactFunnel(rows, label, width);
  const barH = 30;
  const gap = 8;
  const labelW = Math.min(150, Math.round(width * 0.3));
  const max = Math.max(...rows.map((r) => r.value), 1);
  const plotW = width - labelW - Math.min(120, Math.round(width * 0.3));
  const body = rows.map((row, i) => {
    const w = Math.max(2, (row.value / max) * plotW);
    const y = i * (barH + gap);
    const x = labelW + (plotW - w) / 2;
    return `<text x="${labelW - 8}" y="${y + barH / 2 + 4}" text-anchor="end">${esc(row.label)}</text>`
      + `<rect class="bar${row.alt ? ' alt' : ''}" x="${x}" y="${y}" width="${w}" height="${barH}" rx="4"><title>${esc(row.label)}: ${esc(row.display ?? row.value)}</title></rect>`
      + `<text x="${labelW + plotW + 8}" y="${y + barH / 2 + 4}">${esc(row.display ?? row.value)}</text>`
      + (row.note ? `<text class="muted-text" x="${labelW + plotW + 8}" y="${y + barH / 2 + 17}" font-size="10">${esc(row.note)}</text>` : '');
  }).join('');
  return svg(width, rows.length * (barH + gap), body, label);
}

/** Narrow screens: label and value on a line above each bar, so no stage name is cut. */
function compactFunnel(rows, label, width) {
  const rowH = 40;
  const barH = 16;
  const max = Math.max(...rows.map((r) => r.value), 1);
  const body = rows.map((row, i) => {
    const y = i * rowH;
    const w = Math.max(2, (row.value / max) * width);
    return `<text x="0" y="${y + 12}">${esc(row.label)}</text>`
      + `<text class="muted-text" x="${width}" y="${y + 12}" text-anchor="end">${esc(row.display ?? row.value)}</text>`
      + `<rect class="bar${row.alt ? ' alt' : ''}" x="${(width - w) / 2}" y="${y + 18}" width="${w}" height="${barH}" rx="4"><title>${esc(row.label)}: ${esc(row.display ?? row.value)}</title></rect>`;
  }).join('');
  return svg(width, rows.length * rowH, body, label);
}

/** Horizontal bar chart with a label, a value and an optional highlight per row. */
export function barChart(rows, { label = 'Gráfico', width = autoWidth(), format = (v) => v } = {}) {
  const barH = 26;
  const gap = 8;
  const labelW = Math.min(140, Math.round(width * 0.32));
  const finite = rows.map((r) => r.value).filter(Number.isFinite);
  const max = Math.max(...finite, 1);
  const plotW = width - labelW - Math.min(110, Math.round(width * 0.28));
  const body = rows.map((row, i) => {
    const y = i * (barH + gap);
    const w = Number.isFinite(row.value) ? Math.max(2, (row.value / max) * plotW) : 0;
    return `<text x="${labelW - 8}" y="${y + barH / 2 + 4}" text-anchor="end">${esc(row.label)}</text>`
      + `<rect class="bar ${row.tone ?? ''}" x="${labelW}" y="${y}" width="${w}" height="${barH}" rx="4"><title>${esc(row.label)}: ${esc(format(row.value))}</title></rect>`
      + `<text x="${labelW + w + 8}" y="${y + barH / 2 + 4}">${esc(format(row.value))}</text>`;
  }).join('');
  return svg(width, rows.length * (barH + gap), body, label);
}

/** Waterfall: first and last bars are totals, the rest are signed steps. */
export function waterfallChart(steps, { label = 'Ponte', width = Math.max(560, autoWidth()), format = (v) => v } = {}) {
  const height = 280;
  const top = 16;
  const bottom = 70;
  const plotH = height - top - bottom;
  const start = steps[0].value;
  const scale = (v) => top + plotH - (v / start) * plotH;
  const colW = (width - 20) / steps.length;
  let running = 0;
  const body = steps.map((step, i) => {
    const total = i === 0 || i === steps.length - 1;
    const from = total ? 0 : running;
    const to = total ? step.value : running + step.value;
    running = total && i === 0 ? step.value : to;
    const y = scale(Math.max(from, to));
    const h = Math.max(1, Math.abs(scale(from) - scale(to)));
    const x = 10 + i * colW + colW * 0.15;
    const tone = total ? '' : step.value < 0 ? 'bad' : 'good';
    const words = String(step.label).split(' ');
    const lines = [];
    words.forEach((word) => {
      const last = lines[lines.length - 1];
      if (last && (last + ' ' + word).length <= 14) lines[lines.length - 1] = `${last} ${word}`;
      else lines.push(word);
    });
    const text = lines.slice(0, 4).map((line, j) => `<tspan x="${x + colW * 0.35}" dy="${j === 0 ? 0 : 11}">${esc(line)}</tspan>`).join('');
    return `<rect class="bar ${tone}" x="${x}" y="${y}" width="${colW * 0.7}" height="${h}" rx="3"><title>${esc(step.label)}: ${esc(format(step.value))}</title></rect>`
      + `<text x="${x + colW * 0.35}" y="${y - 4}" text-anchor="middle" font-size="10">${esc(format(step.value))}</text>`
      + `<text class="muted-text" x="${x + colW * 0.35}" y="${top + plotH + 14}" text-anchor="middle" font-size="9">${text}</text>`;
  }).join('');
  return svg(width, height, `<line class="axis" x1="0" x2="${width}" y1="${top + plotH}" y2="${top + plotH}"/>${body}`, label);
}

/** A density curve with a vertical marker and the area beyond it shaded. */
export function densityChart(density, marker, { label = 'Distribuição', width = autoWidth() } = {}) {
  const height = 180;
  const pad = 24;
  const n = 200;
  const xs = Array.from({ length: n + 1 }, (_, i) => 0.0005 + (i / n) * 0.999);
  const ys = xs.map(density);
  const maxY = Math.max(...ys.filter(Number.isFinite), 1e-9);
  const px = (x) => pad + x * (width - 2 * pad);
  const py = (y) => height - pad - (Math.min(y, maxY) / maxY) * (height - 2 * pad);
  const path = xs.map((x, i) => `${i ? 'L' : 'M'}${px(x).toFixed(1)},${py(ys[i]).toFixed(1)}`).join('');
  const area = `${path}L${px(xs[n])},${py(0)}L${px(xs[0])},${py(0)}Z`;
  const beyond = xs.filter((x) => x >= marker);
  const shade = beyond.length
    ? `M${px(beyond[0])},${py(0)}${beyond.map((x) => `L${px(x).toFixed(1)},${py(density(x)).toFixed(1)}`).join('')}L${px(beyond[beyond.length - 1])},${py(0)}Z`
    : '';
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((t) => `<text class="muted-text" x="${px(t)}" y="${height - 6}" text-anchor="middle" font-size="10">${Math.round(t * 100)}%</text>`).join('');
  const body = `<path class="curve" d="${area}"/>${shade ? `<path class="shade" d="${shade}"/>` : ''}`
    + `<line class="marker" x1="${px(marker)}" x2="${px(marker)}" y1="${pad / 2}" y2="${height - pad}"/>`
    + `<line class="axis" x1="${pad}" x2="${width - pad}" y1="${height - pad}" y2="${height - pad}"/>${ticks}`;
  return svg(width, height, body, label);
}
