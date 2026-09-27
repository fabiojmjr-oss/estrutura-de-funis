/** Multicanal: CAC and attribution across channels, and how a convention flips the budget. */

import { attribute, blendedVersusPaid, cacByModel, MODEL_LABELS, MODELS } from '../engine/attribution.js';
import { barChart } from '../ui/charts.js';
import { bind, kpi, range, rankBadge, segmented, table } from '../ui/dom.js';
import { brl, dec1, esc, int, pct } from '../ui/format.js';
import { param } from '../ui/state.js';

export const id = 'multichannel';

export function render(el, { data, params, setParams, setCsv }) {
  const { marketing } = data;
  const channels = Object.keys(marketing.spend);
  const state = {
    model: param(params, 'modelo', 'last'),
    mult: channels.map((_, i) => param(params, `v${i}`, 100)),
  };

  const q = (label) => Object.fromEntries(marketing.conventions[label].map((r) => [r.convention, r]));
  const q3 = q('Q3');
  const q4 = q('Q4');

  el.innerHTML = `
    <h2>Multicanal: aquisição e atribuição</h2>
    <p class="lead">Dois números abrem toda reunião de marketing — CAC e canal vencedor — e os dois são
    convenções antes de serem medições. Mude o modelo de atribuição e a verba de cada canal.</p>
    <div class="grid two">
      <div class="panel controls" id="controls">
        ${segmented('modelo', 'Modelo de atribuição', state.model, MODELS.map((m) => [m, MODEL_LABELS[m]]))}
        <fieldset class="control-group"><legend>Verba por canal (% da real)</legend>
          ${channels.map((c, i) => range(`v${i}`, c, state.mult[i], { min: 25, max: 200, step: 5, format: (v) => `${v}%` })).join('')}
        </fieldset>
        <p class="muted" style="font-size:.8rem">Os clientes ficam fixos: o painel mostra a sensibilidade do
        CAC à verba, não a resposta da demanda a ela.</p>
      </div>
      <div id="out"></div>
    </div>
    <div class="panel">
      <h3>Conversão Lead → Cliente: a mesma base, cinco convenções</h3>
      ${table(['Convenção', 'T3 (jul–set)', 'T4 (out–dez)'], [
    ['Período (entradas pela própria data)', pct(q3.period.end_to_end, 2), pct(q4.period.end_to_end, 2)],
    ['Coorte, o que atingiu até 31/dez', pct(q3.cohort_all.end_to_end, 2), pct(q4.cohort_all.end_to_end, 2)],
    ['Coorte, em até 120 dias', pct(q3.cohort_window.end_to_end, 2), pct(q4.cohort_window.end_to_end, 2)],
    ['Coorte madura (120 dias decorridos)', pct(q3.cohort_matured.end_to_end, 2), q4.cohort_matured.entities ? pct(q4.cohort_matured.end_to_end, 2) : 'ainda não se sabe'],
  ])}
    </div>`;

  const out = el.querySelector('#out');
  const formats = Object.fromEntries(channels.map((_, i) => [`v${i}`, (v) => `${v}%`]));

  function update() {
    const spend = Object.fromEntries(channels.map((c, i) => [c, marketing.spend[c] * (state.mult[i] / 100)]));
    const cac = cacByModel(marketing.journeys, spend);
    const summary = blendedVersusPaid(marketing.customers_by_source, spend);
    const credit = attribute(marketing.journeys, state.model);
    const flips = cac.filter((row) => {
      const ranks = MODELS.map((m) => row[`rank_${m}`]);
      return Math.max(...ranks) !== Math.min(...ranks);
    }).map((row) => {
      const best = MODELS.reduce((a, m) => (row[`rank_${m}`] < row[`rank_${a}`] ? m : a));
      const worst = MODELS.reduce((a, m) => (row[`rank_${m}`] > row[`rank_${a}`] ? m : a));
      return `<strong>${esc(row.channel)}</strong>: ${row[`rank_${best}`]}º no ${MODEL_LABELS[best].toLowerCase()}
        (${brl(row[best])}), ${row[`rank_${worst}`]}º no ${MODEL_LABELS[worst].toLowerCase()} (${brl(row[worst])})`;
    });

    out.innerHTML = `
      <div class="panel">
        <div class="grid kpis">
          ${kpi('Verba de mídia', brl(summary.spend))}
          ${kpi('CAC pago', brl(summary.paid), { note: `${int(summary.paidCustomers)} clientes de canais pagos` })}
          ${kpi('CAC blended', brl(summary.blended), { note: `${pct(1 - summary.blended / summary.paid, 0)} "mais barato"`, tone: 'warn' })}
        </div>
        <div class="insight"><p>O blended divide a mesma verba por ${int(summary.allCustomers)} clientes, incluindo
        ${int(summary.allCustomers - summary.paidCustomers)} de indicação e orgânico que a verba não comprou. É o
        número que não dá para comprar mais.</p></div>
      </div>
      <div class="panel">
        <h3>CAC por canal — ${esc(MODEL_LABELS[state.model])}</h3>
        ${barChart(cac.map((r) => ({ label: r.channel, value: r[state.model] })), { label: 'CAC por canal', format: brl })}
        ${table(['Canal', 'Verba', ...MODELS.map((m) => MODEL_LABELS[m])], cac.map((r) => [
    esc(r.channel), brl(r.spend), ...MODELS.map((m) => `${brl(r[m])} ${rankBadge(r[`rank_${m}`], cac.length)}`),
  ]))}
        ${flips.length ? `<div class="insight"><p>O ranking muda com a convenção:</p><p>${flips.join('<br>')}</p></div>` : ''}
      </div>
      <div class="panel">
        <h3>Clientes creditados por canal — ${esc(MODEL_LABELS[state.model])}</h3>
        ${table(['Canal', 'Clientes creditados', 'Fatia'], Object.entries(credit).sort((a, b) => b[1] - a[1]).map(([c, v]) => [
    esc(c), dec1(v), pct(v / Object.values(credit).reduce((s, x) => s + x, 0)),
  ]))}
      </div>`;
    setCsv([['canal', 'verba', ...MODELS.map((m) => `cac_${m}`), ...MODELS.map((m) => `rank_${m}`)],
      ...cac.map((r) => [r.channel, r.spend, ...MODELS.map((m) => r[m]), ...MODELS.map((m) => r[`rank_${m}`])])]);
    setParams({ modelo: state.model, ...Object.fromEntries(state.mult.map((v, i) => [`v${i}`, v])) });
  }

  bind(el.querySelector('#controls'), formats, (p) => {
    state.model = p.modelo;
    state.mult = channels.map((_, i) => Number(p[`v${i}`]));
    update();
  });
  update();
  return {};
}
