/** Construtor: any funnel, typed or loaded from a preset, with intervals, levers and reverse funnel. */

import { funnelTable, leverTable, requiredTop } from '../engine/funnel.js';
import { funnelChart } from '../ui/charts.js';
import { dec1, esc, int, pct } from '../ui/format.js';
import { number, select, table } from '../ui/dom.js';
import { param } from '../ui/state.js';

export const id = 'builder';

function presets(data) {
  return {
    marketing: data.marketing.funnel,
    sales: data.sales.funnel_infer,
    supply: data.supply.funnel,
    management: data.management.funnel,
    custom: [
      { stage: 'Visitas', entered: 10000 },
      { stage: 'Leads', entered: 800 },
      { stage: 'Oportunidades', entered: 120 },
      { stage: 'Clientes', entered: 30 },
    ],
  };
}

const encode = (rows) => rows.map((r) => `${r.stage}~${r.entered}`).join(';');
const decode = (text) => text.split(';').map((part) => {
  const [stage, entered] = part.split('~');
  return { stage, entered: Number(entered) };
}).filter((r) => r.stage && Number.isFinite(r.entered));

export function render(el, { data, params, setParams, setCsv }) {
  const all = presets(data);
  let preset = param(params, 'preset', 'marketing', { oneOf: ['marketing', 'sales', 'supply', 'management', 'custom'] });
  let stages = params.s ? decode(params.s) : all[preset] ?? all.marketing;
  let target = param(params, 'alvo', 300, { min: 1, max: 1e9 });

  el.innerHTML = `
    <h2>Construtor de funil</h2>
    <p class="lead">Carregue um dos funis ou digite o seu. O intervalo de 95% (Wilson) mostra quanto de cada
    taxa é ruído; a tabela de alavancas mostra onde um ponto vale mais, e onde 10% relativos valem o mesmo.</p>
    <div class="grid two">
      <div class="panel controls" id="controls">
        ${select('preset', 'Modelo', preset, [
    ['marketing', 'Marketing (coorte madura)'], ['sales', 'Vendas'], ['supply', 'Supply'],
    ['management', 'Gestão'], ['custom', 'Personalizado'],
  ])}
        <div id="stage-editor"></div>
        <button class="btn ghost small" id="add-stage" type="button">+ Etapa</button>
        ${number('alvo', 'Meta na última etapa (funil reverso)', target, { min: 1 })}
      </div>
      <div class="panel" id="out"></div>
    </div>`;

  const editor = el.querySelector('#stage-editor');
  const out = el.querySelector('#out');

  function drawEditor() {
    editor.innerHTML = `<div class="table-wrap"><table><thead><tr><th>Etapa</th><th>Quantidade</th><th></th></tr></thead><tbody>
      ${stages.map((r, i) => `<tr>
        <td class="editable"><input type="text" aria-label="Nome da etapa ${i + 1}" data-i="${i}" data-f="stage" value="${esc(r.stage)}"></td>
        <td class="editable"><input type="number" inputmode="numeric" min="0" aria-label="Quantidade na etapa ${i + 1}" data-i="${i}" data-f="entered" value="${r.entered}"></td>
        <td><button class="btn ghost small" type="button" data-remove="${i}" aria-label="Remover etapa ${i + 1}"${stages.length <= 2 ? ' disabled' : ''}>×</button></td>
      </tr>`).join('')}</tbody></table></div>`;
  }

  function drawOutput() {
    const labels = stages.map((r) => r.stage);
    const counts = stages.map((r) => r.entered);
    const rows = funnelTable(labels, counts);
    const rates = rows.slice(1).map((r) => r.stepRate);
    const valid = rates.every((r) => r > 0 && r <= 1);
    const levers = valid ? leverTable(labels.slice(1), rates, counts[0]) : [];
    const needed = valid ? requiredTop(target, rates) : NaN;
    out.innerHTML = `
      ${funnelChart(rows.map((r) => ({ label: r.stage, value: r.entered, display: int(r.entered), note: r.stepRate !== null ? `etapa ${pct(r.stepRate)}` : '' })), { label: 'Funil construído' })}
      <h3>Taxas com intervalo de 95%</h3>
      ${table(['Etapa', 'Entraram', 'Taxa da etapa', 'IC 95%', 'Acumulada'], rows.map((r) => [
    esc(r.stage), int(r.entered), r.stepRate === null ? '—' : pct(r.stepRate),
    r.stepLow === null ? '—' : `${pct(r.stepLow)} – ${pct(r.stepHigh)}`, pct(r.cumulativeRate),
  ]))}
      ${valid ? `<h3>Alavancas</h3>
      ${table(['Transição', 'Taxa', '+1 ponto → saída', '+10% relativo → saída', 'Ranking do ponto'], levers.map((l) => [
    esc(l.transition), pct(l.rate), `+${pct(l.gainAbsolutePct, 2)}`, '+10,0%', `${l.rankAbsolute}º`,
  ]))}
      <div class="insight"><p>Para entregar <strong>${int(target)}</strong> na última etapa, entram
      <strong>${int(Math.ceil(needed))}</strong> no topo (${dec1(needed / counts[0])}× o volume atual).
      Onde investir depende do custo de cada ganho, que o funil não contém.</p></div>`
    : '<div class="insight"><p>Alguma taxa está fora de (0, 100%]: confira as quantidades.</p></div>'}`;
    setCsv([['etapa', 'entraram', 'taxa_etapa', 'ic_baixo', 'ic_alto', 'acumulada'],
      ...rows.map((r) => [r.stage, r.entered, r.stepRate, r.stepLow, r.stepHigh, r.cumulativeRate])]);
    setParams({ preset, s: encode(stages), alvo: target });
  }

  el.querySelector('#controls').addEventListener('input', (event) => {
    const t = event.target;
    if (t.dataset.param === 'preset') {
      preset = t.value;
      stages = all[preset].map((r) => ({ ...r }));
      drawEditor();
    } else if (t.dataset.param === 'alvo') {
      target = Math.max(1, Number(t.value) || 1);
    } else if (t.dataset.i !== undefined) {
      const row = stages[Number(t.dataset.i)];
      row[t.dataset.f] = t.dataset.f === 'entered' ? Math.max(0, Number(t.value) || 0) : t.value;
    }
    drawOutput();
  });
  el.querySelector('#controls').addEventListener('click', (event) => {
    const remove = event.target.closest('[data-remove]');
    if (remove) {
      stages.splice(Number(remove.dataset.remove), 1);
      drawEditor();
      drawOutput();
    }
  });
  el.querySelector('#add-stage').addEventListener('click', () => {
    const last = stages[stages.length - 1];
    stages.push({ stage: `Etapa ${stages.length + 1}`, entered: Math.max(1, Math.round(last.entered / 2)) });
    drawEditor();
    drawOutput();
  });

  drawEditor();
  drawOutput();
  return {};
}
