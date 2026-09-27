/** Gestão: the benefit bridge, and Little's law on the execution portfolio. */

import { waterfallChart } from '../ui/charts.js';
import { bind, kpi, range, table } from '../ui/dom.js';
import { brlM, dec1, esc, int, pct } from '../ui/format.js';
import { param } from '../ui/state.js';

export const id = 'management';

const LABELS = {
  announced: 'Anunciado',
  'stopped before Aprovada': 'Não aprovado',
  'stopped before Financiada': 'Parado antes do financiamento',
  'stopped before Em execução': 'Parado antes de iniciar',
  'stopped before Entregue': 'Parado em execução',
  'stopped before Benefício medido': 'Entregue sem medição',
  'still in flight': 'Ainda em andamento',
  'under-delivered': 'Abaixo do plano',
  realised: 'Realizado e medido',
};

export function render(el, { data, params, setParams, setCsv }) {
  const { management } = data;
  const flow = management.flow;
  const state = {
    wip: param(params, 'wip', Math.round(flow.wip)),
    throughput: param(params, 'vazao', Math.round(flow.throughput_per_day * 30.4 * 10) / 10),
  };

  const bridge = management.bridge.map((b) => ({ label: LABELS[b.bar] ?? b.bar, value: b.benefit }));
  const announced = bridge[0].value;

  el.innerHTML = `
    <h2>Gestão: do benefício anunciado ao realizado</h2>
    <p class="lead">Coorte de iniciativas propostas um ano antes do horizonte. A ponte reconcilia exatamente:
    cada real que some tem um gate responsável.</p>
    <div class="panel">
      ${waterfallChart(bridge, { label: 'Ponte de benefício', format: (v) => dec1(v / 1e6) })}
      <p class="muted" style="font-size:.8rem">Valores em R$ milhões.</p>
      ${table(['Barra', 'R$ mi', 'Fração do anunciado'], bridge.map((b) => [esc(b.label), dec1(b.value / 1e6), pct(b.value / announced)]))}
      <div class="insight"><p>${brlM(-management.bridge.find((b) => b.bar === 'stopped before Benefício medido').benefit)} foram
      entregues e nunca medidos — mais que os ${brlM(management.bridge.find((b) => b.bar === 'realised').benefit)} realizados e
      medidos. O portfólio não sabe dizer se o seu maior resultado aconteceu.</p></div>
    </div>
    <div class="grid two" style="margin-top:1rem">
      <div class="panel controls" id="controls">
        <h3>Lei de Little</h3>
        ${range('wip', 'Iniciativas em execução (WIP)', state.wip, { min: 5, max: 120, step: 1, format: (v) => int(v) })}
        ${range('vazao', 'Entregas por mês (vazão)', state.throughput, { min: 1, max: 30, step: 0.1, format: (v) => dec1(v) })}
      </div>
      <div class="panel" id="out"></div>
    </div>`;

  const out = el.querySelector('#out');
  function update() {
    const lead = state.wip / (state.throughput / 30.4);
    const measuredLead = flow.wip / flow.throughput_per_day;
    out.innerHTML = `
      <div class="grid kpis">
        ${kpi('Lead time implícito', `${int(lead)} dias`, { tone: lead > measuredLead ? 'bad' : 'good' })}
        ${kpi('Atual (dados)', `${int(measuredLead)} dias`, { note: `WIP ${dec1(flow.wip)}, medido no que terminou: ${int(flow.lead_time_days)} dias` })}
        ${kpi('Com metade do WIP', `${int(lead / 2)} dias`, { note: 'mesma vazão, sem orçamento novo' })}
      </div>
      <div class="insight"><p>Lead time = WIP ÷ vazão. Todo projeto pode estar no prazo e o portfólio ficar mais
      lento: cada iniciativa a mais em andamento alonga o prazo de todas as outras. Começar menos é o jeito mais
      barato de terminar antes.</p></div>`;
    setCsv([['barra', 'beneficio'], ...bridge.map((b) => [b.label, b.value]), [], ['wip', 'vazao_mes', 'lead_time_dias'], [state.wip, state.throughput, lead]]);
    setParams({ wip: state.wip, vazao: state.throughput });
  }
  bind(el.querySelector('#controls'), { wip: (v) => int(v), vazao: (v) => dec1(v) }, (p) => {
    state.wip = Number(p.wip);
    state.throughput = Number(p.vazao);
    update();
  });
  update();
  return {};
}
