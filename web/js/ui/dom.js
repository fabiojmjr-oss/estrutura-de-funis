/** Small helpers shared by the views: controls bound to the URL, KPI tiles, tables. */

import { esc } from './format.js';

/** A labelled range slider whose current value is echoed in an <output>. */
export function range(key, label, value, { min, max, step, format = (v) => v }) {
  return `<label class="field"><span>${esc(label)} <output data-for="${key}">${esc(format(value))}</output></span>`
    + `<input type="range" data-param="${key}" min="${min}" max="${max}" step="${step}" value="${value}" aria-label="${esc(label)}"></label>`;
}

export function number(key, label, value, { min = 0, max, step = 1 } = {}) {
  return `<label class="field"><span>${esc(label)}</span>`
    + `<input type="number" inputmode="decimal" data-param="${key}" value="${value}" min="${min}"${max !== undefined ? ` max="${max}"` : ''} step="${step}"></label>`;
}

export function select(key, label, value, options) {
  const items = options.map(([v, text]) => `<option value="${esc(v)}"${String(v) === String(value) ? ' selected' : ''}>${esc(text)}</option>`).join('');
  return `<label class="field"><span>${esc(label)}</span><select data-param="${key}">${items}</select></label>`;
}

export function segmented(key, label, value, options) {
  const items = options.map(([v, text]) => `<label><input type="radio" name="${key}" data-param="${key}" value="${esc(v)}"${String(v) === String(value) ? ' checked' : ''}>${esc(text)}</label>`).join('');
  return `<fieldset class="control-group"><legend>${esc(label)}</legend><div class="segmented">${items}</div></fieldset>`;
}

export function toggle(key, label, value) {
  return `<label class="field toggle"><input type="checkbox" data-param="${key}"${value ? ' checked' : ''}><span>${esc(label)}</span></label>`;
}

/** Collect every [data-param] control under root into a flat string map. */
export function readControls(root) {
  const params = {};
  root.querySelectorAll('[data-param]').forEach((input) => {
    const key = input.dataset.param;
    if (input.type === 'radio') {
      if (input.checked) params[key] = input.value;
    } else if (input.type === 'checkbox') {
      params[key] = input.checked ? '1' : '0';
    } else {
      params[key] = input.value;
    }
  });
  return params;
}

/** Wire a controls container: echo range values, then call onChange with the parameters. */
export function bind(root, formats, onChange) {
  const handler = (event) => {
    const target = event.target;
    if (target.matches?.('input[type="range"]')) {
      const out = root.querySelector(`output[data-for="${target.dataset.param}"]`);
      const format = formats[target.dataset.param] ?? ((v) => v);
      if (out) out.textContent = format(Number(target.value));
    }
    onChange(readControls(root));
  };
  root.addEventListener('input', handler);
  root.addEventListener('change', handler);
}

export function kpi(label, value, { note = '', tone = '' } = {}) {
  return `<div class="kpi ${tone}"><span class="kpi-label">${esc(label)}</span>`
    + `<span class="kpi-value">${esc(value)}</span>${note ? `<span class="kpi-note">${esc(note)}</span>` : ''}</div>`;
}

/** A table from a header row and body rows of already-formatted cells (HTML allowed). */
export function table(header, rows, { highlight = () => false, caption = '' } = {}) {
  const head = header.map((h) => `<th scope="col">${esc(h)}</th>`).join('');
  const body = rows.map((row, i) => `<tr${highlight(i) ? ' class="highlight"' : ''}>${row.map((cell, j) => (j === 0 ? `<th scope="row">${cell}</th>` : `<td>${cell}</td>`)).join('')}</tr>`).join('');
  return `<div class="table-wrap"><table>${caption ? `<caption class="muted">${esc(caption)}</caption>` : ''}<thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}

export function rankBadge(rank, count) {
  const tone = rank === 1 ? 'best' : rank === count ? 'worst' : '';
  return `<span class="rank ${tone}">${rank}º</span>`;
}
