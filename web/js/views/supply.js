/** Supply: first-pass yield against final yield, and the factory hidden between them. */

import { funnelChart } from '../ui/charts.js';
import { bind, kpi, range, table } from '../ui/dom.js';
import { dec1, esc, int, pct } from '../ui/format.js';
import { param } from '../ui/state.js';

export const id = 'supply';

/** The generator's rework model: failed attempts retried, each retry passing with probability r. */
function stageModel(fpy, retry, attempts) {
  const failAll = (1 - fpy) * (1 - retry) ** (attempts - 1);
  let extra = 0;
  for (let j = 1; j < attempts; j += 1) extra += (1 - fpy) * (1 - retry) ** (j - 1);
  return { final: 1 - failAll, repeats: extra };
}

export function render(el, { data, params, setParams, setCsv }) {
  const { supply } = data;
  const stages = supply.yields.filter((r) => r.stage !== 'total');
  const measured = supply.yields.find((r) => r.stage === 'total');
  const state = {
    fpy: stages.map((r, i) => param(params, `f${i}`, Math.round(r.first_pass_yield * 1000) / 10, {
      min: 80,
      max: 100,
    })),
    retry: param(params, 'retry', 85, { min: 50, max: 100 }),
    attempts: param(params, 'tentativas', 3, { min: 1, max: 5 }),
  };

  el.innerHTML = `
    <h2>Supply: a fábrica oculta</h2>
    <p class="lead">O funil de atendimento só conta quem chegou, por isso quase não perde nada. O rendimento
    acumulado de primeira passagem (RTY) conta quem chegou sem ser manuseado duas vezes. Ajuste o rendimento de
    primeira passagem de cada etapa e veja a distância entre os dois.</p>
    <div class="grid two">
      <div class="panel controls" id="controls">
        <fieldset class="control-group"><legend>Rendimento de primeira passagem</legend>
          ${stages.map((r, i) => range(`f${i}`, r.stage, state.fpy[i], { min: 80, max: 100, step: 0.1, format: (v) => `${dec1(v)}%` })).join('')}
        </fieldset>
        ${range('retry', 'Chance de uma nova tentativa passar', state.retry, { min: 50, max: 100, step: 1, format: (v) => `${v}%` })}
        ${range('tentativas', 'Tentativas antes de desistir', state.attempts, { min: 1, max: 5, step: 1, format: (v) => `${v}` })}
      </div>
      <div id="out"></div>
    </div>`;

  const out = el.querySelector('#out');
  const formats = { retry: (v) => `${v}%`, tentativas: (v) => `${v}`, ...Object.fromEntries(stages.map((_, i) => [`f${i}`, (v) => `${dec1(v)}%`])) };

  function update() {
    const rows = stages.map((r, i) => ({ stage: r.stage, fpy: state.fpy[i] / 100, ...stageModel(state.fpy[i] / 100, state.retry / 100, state.attempts) }));
    const rty = rows.reduce((p, r) => p * r.fpy, 1);
    const final = rows.reduce((p, r) => p * r.final, 1);
    const repeats = rows.reduce((s, r) => s + r.repeats, 0) * 100;
    const worst = [...rows].sort((a, b) => b.repeats - a.repeats)[0];
    let flow = 1000;
    const funnel = [{ label: 'Pedido', value: flow, display: int(flow) }];
    rows.forEach((r) => {
      flow *= r.final;
      funnel.push({ label: r.stage, value: flow, display: int(flow) });
    });

    out.innerHTML = `
      <div class="panel">
        <div class="grid kpis">
          ${kpi('Rendimento final', pct(final), { tone: 'good', note: 'o que o funil mostra' })}
          ${kpi('RTY', pct(rty), { tone: 'bad', note: 'passaram sem retrabalho' })}
          ${kpi('Retrabalho', `${dec1(repeats)} / 100`, { note: 'tentativas repetidas por 100 pedidos' })}
          ${kpi('Medido nos dados', pct(measured.first_pass_yield), { note: `RTY real; ${pct(supply.hidden_factory.orders_reworked_share)} dos pedidos retrabalhados` })}
        </div>
        <div class="insight"><p>Um pedido em ${dec1(1 / Math.max(1 - rty, 1e-9))} é manuseado duas vezes em algum ponto.
        A etapa que mais gera retrabalho é <strong>${esc(worst.stage)}</strong>
        (${dec1(worst.repeats * 100)} tentativas extras por 100). É ali que um projeto Lean paga primeiro.</p></div>
        ${funnelChart(funnel, { label: 'Fluxo de 1.000 pedidos' })}
      </div>
      <div class="panel">
        <h3>Etapa a etapa</h3>
        ${table(['Etapa', 'Primeira passagem', 'Final', 'Retrabalho / 100'], rows.map((r) => [
    esc(r.stage), pct(r.fpy), pct(r.final, 2), dec1(r.repeats * 100),
  ]))}
        <h3>Pedido perfeito (dados)</h3>
        ${table(['Componente', 'Taxa'], Object.entries(supply.perfect_order).map(([k, v]) => [esc(k.replaceAll('_', ' ')), pct(v, 2)]))}
      </div>`;
    setCsv([['etapa', 'primeira_passagem', 'final', 'retrabalho_por_100'], ...rows.map((r) => [r.stage, r.fpy, r.final, r.repeats * 100])]);
    setParams({ retry: state.retry, tentativas: state.attempts, ...Object.fromEntries(state.fpy.map((v, i) => [`f${i}`, v])) });
  }

  bind(el.querySelector('#controls'), formats, (p) => {
    state.fpy = stages.map((_, i) => Number(p[`f${i}`]));
    state.retry = Number(p.retry);
    state.attempts = Number(p.tentativas);
    update();
  });
  update();
  return {};
}
