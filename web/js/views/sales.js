/** Vendas: skipped stages, stage odds and a forecast graded against what was actually won. */

import { forecast } from '../engine/sales.js';
import { barChart, funnelChart } from '../ui/charts.js';
import { bind, kpi, range, segmented, table, toggle } from '../ui/dom.js';
import { brlM, dec1, esc, int, pct, signedPct } from '../ui/format.js';
import { param } from '../ui/state.js';

export const id = 'sales';

export function render(el, { data, params, setParams, setCsv }) {
  const { sales } = data;
  const open = sales.stages.slice(0, -1);
  const state = {
    source: param(params, 'odds', 'hist', { oneOf: ['crm', 'hist', 'custom'] }),
    custom: open.map((s, i) => param(params, `p${i}`, Math.round(sales.historical_probability[s] * 100), {
      min: 0,
      max: 100,
    })),
    stale: param(params, 'parados', true),
    factor: param(params, 'fator', 1, { min: 0.5, max: 3 }),
    skip: param(params, 'etapas', 'infer', { oneOf: ['infer', 'literal'] }),
  };

  el.innerHTML = `
    <h2>Vendas: o que o pipeline aberto vai fechar</h2>
    <p class="lead">O pipeline sintético guarda o desfecho final de cada negócio aberto, então a previsão pode
    ser avaliada em vez de discutida. Troque as probabilidades e veja o que realmente corrige o erro.</p>
    <div class="grid two">
      <div class="panel controls" id="controls">
        ${segmented('odds', 'Probabilidades por etapa', state.source, [['crm', 'Padrão do CRM'], ['hist', 'Histórico'], ['custom', 'Personalizadas']])}
        <fieldset class="control-group" id="custom-odds"><legend>Personalizadas</legend>
          ${open.map((s, i) => range(`p${i}`, s, state.custom[i], { min: 0, max: 100, step: 1, format: (v) => `${v}%` })).join('')}
        </fieldset>
        ${toggle('parados', 'Zerar negócios parados na etapa', state.stale)}
        ${range('fator', 'Limite de "parado" (× p85 dos ganhos)', state.factor, { min: 0.5, max: 3, step: 0.1, format: (v) => `${dec1(v)}×` })}
        ${segmented('etapas', 'Etapas puladas no funil', state.skip, [['infer', 'Inferir'], ['literal', 'Só o registrado']])}
      </div>
      <div id="out"></div>
    </div>`;

  const out = el.querySelector('#out');
  const formats = { fator: (v) => `${dec1(v)}×`, ...Object.fromEntries(open.map((_, i) => [`p${i}`, (v) => `${v}%`])) };

  function update() {
    el.querySelector('#custom-odds').hidden = state.source !== 'custom';
    const odds = state.source === 'crm'
      ? sales.crm_probability
      : state.source === 'hist'
        ? sales.historical_probability
        : Object.fromEntries(open.map((s, i) => [s, state.custom[i] / 100]));
    const stale = state.stale ? sales.stale_after_days : null;
    const current = forecast(sales.open_deals, odds, { staleAfter: stale, staleFactor: state.factor });
    const bench = [
      ['CRM padrão', forecast(sales.open_deals, sales.crm_probability)],
      ['Histórico', forecast(sales.open_deals, sales.historical_probability)],
      ['Histórico sem parados', forecast(sales.open_deals, sales.historical_probability, { staleAfter: sales.stale_after_days })],
    ];
    const funnel = state.skip === 'literal' ? sales.funnel_literal : sales.funnel_infer;
    const total = sales.open_deals.reduce((s, d) => s + d.amount, 0);
    const errTone = Math.abs(current.error) < 0.05 ? 'good' : Math.abs(current.error) > 0.2 ? 'bad' : 'warn';

    out.innerHTML = `
      <div class="panel">
        <div class="grid kpis">
          ${kpi('Pipeline aberto', brlM(total), { note: `${int(sales.open_deals.length)} negócios` })}
          ${kpi('Previsão', brlM(current.forecast))}
          ${kpi('Ganho de fato', brlM(current.actual), { note: 'desfecho guardado pelo gerador' })}
          ${kpi('Erro da previsão', signedPct(current.error), { tone: errTone })}
          ${kpi('Negócios parados', int(current.staleCount), { note: state.stale ? brlM(current.staleAmount) : 'filtro desligado' })}
        </div>
        ${barChart([
    ...bench.map(([label, r]) => ({ label, value: r.forecast })),
    { label: 'Seu cenário', value: current.forecast, tone: 'alt' },
    { label: 'Ganho de fato', value: current.actual, tone: 'good' },
  ], { label: 'Previsões contra o realizado', format: brlM })}
        <div class="insight"><p>Trocar o CRM pelo histórico muda o erro de ${signedPct(bench[0][1].error)} para
        ${signedPct(bench[1][1].error)}; zerar os parados leva a ${signedPct(bench[2][1].error)}. O erro não está nas
        probabilidades: está nos negócios cuja idade na etapa já diz "não".</p></div>
      </div>
      <div class="panel">
        <h3>Probabilidades: configuradas contra medidas</h3>
        ${table(['Etapa', 'CRM', 'Histórico', 'Parado após (dias)'], open.map((s) => [
    esc(s), pct(sales.crm_probability[s], 0), pct(sales.historical_probability[s]), dec1(sales.stale_after_days[s]),
  ]))}
      </div>
      <div class="panel">
        <h3>Funil — ${state.skip === 'literal' ? 'só o registrado' : 'etapas puladas inferidas'}</h3>
        ${funnelChart(funnel.map((r, i) => {
    const step = i ? r.entered / funnel[i - 1].entered : null;
    return { label: r.stage, value: r.entered, display: `${int(r.entered)}${step ? ` · ${pct(step)}` : ''}`, alt: step > 1 };
  }), { label: 'Pipeline de vendas' })}
        ${state.skip === 'literal' ? '<div class="insight"><p>Uma taxa de etapa acima de 100%: negócios criados direto em proposta nunca passaram por qualificação no registro. Meta por etapa definida sobre isso é definida sobre um artefato.</p></div>' : ''}
      </div>`;
    setCsv([['previsao', 'valor', 'erro'], ...bench.map(([l, r]) => [l, r.forecast, r.error]), ['seu cenário', current.forecast, current.error], ['ganho de fato', current.actual, 0]]);
    setParams({
      odds: state.source, parados: state.stale ? '1' : '0', fator: state.factor, etapas: state.skip,
      ...(state.source === 'custom' ? Object.fromEntries(state.custom.map((v, i) => [`p${i}`, v])) : {}),
    });
  }

  bind(el.querySelector('#controls'), formats, (p) => {
    state.source = p.odds;
    state.custom = open.map((_, i) => Number(p[`p${i}`]));
    state.stale = p.parados === '1';
    state.factor = Number(p.fator);
    state.skip = p.etapas;
    update();
  });
  update();
  return {};
}
