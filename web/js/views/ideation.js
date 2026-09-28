/**
 * Ideia -> MVP: simulate a gate policy on the 628-idea portfolio, and read one experiment
 * against its bar. The simulation runs in the browser with the same accounting as
 * funilab.ideation.gates; web/tests/engine.test.mjs asserts it lands inside Python's ranges.
 */

import { replicate, toRows } from '../engine/gates.js';
import { decide, lgamma, neutralPrior, probAbove, sampleSize } from '../engine/stats.js';
import { densityChart, funnelChart } from '../ui/charts.js';
import { bind, kpi, number, range, segmented, select, table } from '../ui/dom.js';
import { brl, brlM, dec1, esc, int, pct } from '../ui/format.js';
import { param } from '../ui/state.js';

export const id = 'ideation';

const PRESET_LABELS = {
  'Sem gates': 'Sem gates — constrói tudo',
  Intuição: 'Intuição — score de feeling, leitura pontual',
  Evidência: 'Evidência — corte por RICE, 80% de confiança',
  'Rigor máximo': 'Rigor máximo — corte de 70%, 95%',
  Calibrada: 'Calibrada — sem corte, 5 entrevistas, 60%',
};
const DECISION = { go: ['go', 'Avançar'], kill: ['kill', 'Matar'], 'more evidence': ['more', 'Mais evidência'] };

function policyFromParams(base, params) {
  return {
    ...base,
    name: 'Seu cenário',
    triage_share: param(params, 'triagem', base.triage_share * 100) / 100,
    triage_score: param(params, 'score', base.triage_score),
    interviews: param(params, 'entrevistas', base.interviews),
    visitors: param(params, 'visitantes', base.visitors),
    mvp_users: param(params, 'usuarios', base.mvp_users),
    pain_bar: param(params, 'barra_dor', base.pain_bar * 100) / 100,
    signup_bar: param(params, 'barra_conv', base.signup_bar * 100) / 100,
    retention_bar: param(params, 'barra_ret', base.retention_bar * 100) / 100,
    reading: param(params, 'leitura', base.reading),
    go: param(params, 'go', base.go * 100) / 100,
    kill: param(params, 'kill', base.kill * 100) / 100,
  };
}

export function render(el, { data, params, setParams, setCsv }) {
  const { ideation } = data;
  const ideas = toRows(ideation.ideas);
  const goodCount = ideas.filter((i) => i.solution_fit).length;
  const presetName = param(params, 'politica', 'Calibrada');
  const base = ideation.policies.find((p) => p.name === presetName) ?? ideation.policies.at(-1);
  let policy = policyFromParams(base, params);
  let costs = {
    ...ideation.costs,
    mvp_build: param(params, 'custo_mvp', ideation.costs.mvp_build),
    scale_investment: param(params, 'invest_escala', ideation.costs.scale_investment),
  };
  let reps = param(params, 'reps', 30);
  const calc = {
    k: param(params, 'k', 2),
    n: param(params, 'n', 5),
    bar: param(params, 'barra', 35),
    expected: param(params, 'esperada', 55),
  };

  const pctFmt = (v) => `${v}%`;
  const controls = (p) => `
    ${select('politica', 'Partir de uma política', presetName, ideation.policies.map((x) => [x.name, PRESET_LABELS[x.name] ?? x.name]))}
    <fieldset class="control-group"><legend>Gate 1 · Triagem</legend>
      ${range('triagem', 'Ideias que passam da triagem', Math.round(p.triage_share * 100), { min: 10, max: 100, step: 5, format: pctFmt })}
      ${select('score', 'Ordenadas por', p.triage_score, [['rice', 'RICE'], ['ice', 'ICE'], ['none', 'Sorteio']])}
    </fieldset>
    <fieldset class="control-group"><legend>Gates 2–4 · Evidência</legend>
      ${range('entrevistas', 'Entrevistas de problema', p.interviews, { min: 0, max: 40, step: 1, format: (v) => int(v) })}
      ${range('barra_dor', 'Barra de dor confirmada', Math.round(p.pain_bar * 100), { min: 5, max: 80, step: 1, format: pctFmt })}
      ${range('visitantes', 'Visitantes do smoke test', p.visitors, { min: 0, max: 3000, step: 50, format: (v) => int(v) })}
      ${range('barra_conv', 'Barra de conversão', Math.round(p.signup_bar * 100), { min: 1, max: 15, step: 1, format: pctFmt })}
      ${range('usuarios', 'Usuários do MVP', p.mvp_users, { min: 0, max: 200, step: 5, format: (v) => int(v) })}
      ${range('barra_ret', 'Barra de retenção', Math.round(p.retention_bar * 100), { min: 10, max: 70, step: 1, format: pctFmt })}
    </fieldset>
    <fieldset class="control-group"><legend>Leitura da evidência</legend>
      ${segmented('leitura', 'Como ler', p.reading, [['posterior', 'Probabilidade a posteriori'], ['point', 'Taxa observada']])}
      ${range('go', 'Confiança para avançar (go)', Math.round(p.go * 100), { min: 50, max: 99, step: 1, format: pctFmt })}
      ${range('kill', 'Abaixo disso, matar (senão 2ª rodada)', Math.round(p.kill * 100), { min: 1, max: 49, step: 1, format: pctFmt })}
    </fieldset>
    <fieldset class="control-group"><legend>Custos</legend>
      ${number('custo_mvp', 'Construir um MVP (R$)', costs.mvp_build, { min: 0, step: 5000 })}
      ${number('invest_escala', 'Escalar uma ideia (R$)', costs.scale_investment, { min: 0, step: 10000 })}
      ${select('reps', 'Replicações', reps, [[10, '10 (rápido)'], [30, '30 (padrão)'], [60, '60 (preciso)']])}
    </fieldset>`;

  el.innerHTML = `
    <h2>Ideia → MVP: o ciclo completo</h2>
    <p class="lead">${int(ideas.length)} ideias, ${int(goodCount)} realmente boas — o simulador conhece a verdade que o
    comitê não conhece, então conta o que nenhum pipeline real consegue: as ideias boas que a política matou e as
    ruins que escalou. Ajuste os gates; cada resultado é a média de várias rodadas, com faixa.</p>
    <div class="grid two">
      <div class="panel controls" id="controls">${controls(policy)}</div>
      <div id="out"><div class="panel"><p class="spinner"> Simulando…</p></div></div>
    </div>
    <div class="grid two" style="margin-top:1rem">
      <div class="panel controls" id="calc-controls">
        <h3>Calculadora de gate</h3>
        ${number('k', 'Responderam (confirmaram dor, converteram, ficaram)', calc.k, { min: 0 })}
        ${number('n', 'Expostos (entrevistados, visitantes, usuários)', calc.n, { min: 1 })}
        ${range('barra', 'Barra da taxa real', calc.bar, { min: 1, max: 90, step: 1, format: pctFmt })}
        ${range('esperada', 'Taxa esperada se a ideia for boa', calc.expected, { min: 1, max: 95, step: 1, format: pctFmt })}
      </div>
      <div class="panel" id="calc-out"></div>
    </div>`;

  const out = el.querySelector('#out');
  const calcOut = el.querySelector('#calc-out');
  let timer = null;
  let token = 0;

  function reference(name, metric) {
    return ideation.reference.find((r) => r.policy === name && r.metric === metric);
  }

  function runSimulation() {
    const mine = ++token;
    out.querySelector('.panel')?.setAttribute('aria-busy', 'true');
    setTimeout(() => {
      if (mine !== token) return;
      const r = replicate(ideas, policy, costs, { replications: reps });
      const calibrated = reference('Calibrada', 'net_value');
      const funnel = ideation.stages.map((stage, i) => ({
        label: stage, value: r.reached[i],
        display: `${dec1(r.reached[i])}${i ? ` · ${pct(r.reached[i] / Math.max(r.reached[i - 1], 1e-9))}` : ''}`,
      }));
      const tone = r.net_value.mean > 0 ? 'good' : 'bad';
      out.innerHTML = `
        <div class="panel" aria-busy="false">
          <div class="grid kpis">
            ${kpi('Valor líquido', brlM(r.net_value.mean), { tone, note: `faixa ${brlM(r.net_value.low)} a ${brlM(r.net_value.high)}` })}
            ${kpi('Boas escaladas', `${dec1(r.good_scaled.mean)} de ${goodCount}`, { tone: 'good' })}
            ${kpi('Ruins escaladas', dec1(r.bad_scaled.mean), { tone: r.bad_scaled.mean > 5 ? 'bad' : '' })}
            ${kpi('Boas mortas', dec1(r.false_kills.mean + r.triage_kills_of_good.mean), { note: `${dec1(r.triage_kills_of_good.mean)} só na triagem`, tone: 'warn' })}
            ${kpi('MVPs construídos', dec1(r.mvps_built.mean))}
            ${kpi('Custo por boa escalada', brl(r.cost_per_good_scaled.mean))}
          </div>
          ${funnelChart(funnel, { label: 'Funil de ideias do cenário (média)' })}
          <div class="insight"><p>Referência da biblioteca Python (portfólio independente, 30 rodadas): a política
          calibrada rende ${brlM(calibrated.mean)} (faixa ${brlM(calibrated.low)} a ${brlM(calibrated.high)}).
          ${r.net_value.mean > calibrated.high ? 'Seu cenário supera a faixa dela.' : r.net_value.mean >= calibrated.low ? 'Seu cenário está dentro da faixa dela.' : 'Seu cenário fica abaixo da faixa dela.'}</p></div>
        </div>
        <div class="panel">
          <h3>As cinco políticas de referência (Python)</h3>
          ${table(['Política', 'MVPs', 'Boas escaladas', 'Ruins escaladas', 'Valor líquido', 'Faixa (R$ mi)'], ideation.policies.map((p) => [
    esc(p.name), dec1(reference(p.name, 'mvps_built').mean), dec1(reference(p.name, 'good_scaled').mean),
    dec1(reference(p.name, 'bad_scaled').mean), brlM(reference(p.name, 'net_value').mean),
    `${dec1(reference(p.name, 'net_value').low / 1e6)} a ${dec1(reference(p.name, 'net_value').high / 1e6)}`,
  ]), { highlight: (i) => ideation.policies[i].name === presetName })}
        </div>`;
      setCsv([['metrica', 'media', 'p2_5', 'p97_5'],
        ...Object.entries(r).filter(([k]) => k !== 'reached').map(([k, v]) => [k, v.mean, v.low, v.high])]);
    }, 20);
  }

  function schedule() {
    clearTimeout(timer);
    timer = setTimeout(runSimulation, 200);
  }

  function updateCalc() {
    const n = Math.max(1, Math.round(calc.n));
    const k = Math.min(Math.max(0, Math.round(calc.k)), n);
    const bar = calc.bar / 100;
    const [a, b] = neutralPrior(bar);
    const pa = a + k;
    const pb = b + n - k;
    const lbeta = lgamma(pa) + lgamma(pb) - lgamma(pa + pb);
    const density = (x) => Math.exp((pa - 1) * Math.log(x) + (pb - 1) * Math.log1p(-x) - lbeta);
    const p = probAbove(k, n, bar);
    const [cls, label] = DECISION[decide(k, n, bar, { go: policy.go, kill: policy.kill })];
    const pointPass = k / n >= bar;
    let needed = '—';
    try {
      needed = int(sampleSize(calc.expected / 100, bar, { go: policy.go }));
    } catch {
      needed = 'nenhuma amostra decide';
    }
    calcOut.innerHTML = `
      <div class="grid kpis">
        ${kpi('Taxa observada', pct(k / n), { note: pointPass ? 'passa na leitura pontual' : 'não passa na leitura pontual' })}
        ${kpi('P(taxa real > barra)', pct(p))}
        <div class="kpi"><span class="kpi-label">Decisão (go ${pct(policy.go, 0)}, kill ${pct(policy.kill, 0)})</span><span class="kpi-value"><span class="chip ${cls}">${label}</span></span></div>
        ${kpi('Amostra para decidir', needed, { note: `se a taxa real for ${calc.expected}%` })}
      </div>
      ${densityChart(density, bar, { label: 'Distribuição a posteriori da taxa real' })}
      <p class="muted" style="font-size:.8rem">Curva: o que a evidência diz sobre a taxa real (prior neutro: 50% de chance
      de passar a barra antes de qualquer dado). Área sombreada: probabilidade de passar a barra.</p>`;
  }

  function sync() {
    setParams({
      politica: presetName,
      triagem: Math.round(policy.triage_share * 100), score: policy.triage_score,
      entrevistas: policy.interviews, visitantes: policy.visitors, usuarios: policy.mvp_users,
      barra_dor: Math.round(policy.pain_bar * 100), barra_conv: Math.round(policy.signup_bar * 100),
      barra_ret: Math.round(policy.retention_bar * 100), leitura: policy.reading,
      go: Math.round(policy.go * 100), kill: Math.round(policy.kill * 100),
      custo_mvp: costs.mvp_build, invest_escala: costs.scale_investment, reps,
      k: calc.k, n: calc.n, barra: calc.bar, esperada: calc.expected,
    });
  }

  const controlsEl = el.querySelector('#controls');
  const formats = {
    triagem: pctFmt, entrevistas: int, visitantes: int, usuarios: int, barra_dor: pctFmt,
    barra_conv: pctFmt, barra_ret: pctFmt, go: pctFmt, kill: pctFmt, barra: pctFmt, esperada: pctFmt,
  };
  bind(controlsEl, formats, (p) => {
    if (p.politica !== presetName) {
      // A new starting point: reset every control to that policy and re-render the tab.
      setParams({ politica: p.politica });
      render(el, { data, params: { politica: p.politica }, setParams, setCsv });
      return;
    }
    policy = policyFromParams(base, p);
    if (policy.kill >= policy.go) policy.kill = Math.max(0.01, policy.go - 0.01);
    costs = { ...costs, mvp_build: Number(p.custo_mvp) || 0, scale_investment: Number(p.invest_escala) || 0 };
    reps = Number(p.reps);
    sync();
    updateCalc();
    schedule();
  });
  bind(el.querySelector('#calc-controls'), formats, (p) => {
    calc.k = Number(p.k);
    calc.n = Number(p.n);
    calc.bar = Number(p.barra);
    calc.expected = Number(p.esperada);
    sync();
    updateCalc();
  });

  sync();
  updateCalc();
  runSimulation();
  return {};
}
