/** Visão geral: the five funnels on one screen, each with the finding that matters. */

import { funnelChart } from '../ui/charts.js';
import { brlM, int, pct } from '../ui/format.js';
import { replicate, toRows } from '../engine/gates.js';

export const id = 'overview';

function card(title, question, chart, finding, target) {
  return `<article class="panel card">
    <h2>${title}</h2>
    <p class="muted">${question}</p>
    ${chart}
    <div class="insight"><p>${finding}</p></div>
    <button class="btn ghost small" data-goto="${target}">Explorar →</button>
  </article>`;
}

const rows = (funnel) => funnel.map((r, i) => ({
  label: r.stage,
  value: r.entered,
  display: `${int(r.entered)}${i ? ` · ${pct(r.entered / funnel[i - 1].entered)}` : ''}`,
}));

export function render(el, { data, goto, setCsv }) {
  const { marketing, sales, supply, management, ideation } = data;
  const q3 = Object.fromEntries(marketing.conventions.Q3.map((r) => [r.convention, r.end_to_end]));
  const q4 = Object.fromEntries(marketing.conventions.Q4.map((r) => [r.convention, r.end_to_end]));
  const literal = sales.funnel_literal;
  const proposalStep = literal[2].entered / literal[1].entered;
  const rty = supply.yields.find((r) => r.stage === 'total');
  const bridge = Object.fromEntries(management.bridge.map((b) => [b.bar, b.benefit]));

  const policy = ideation.policies.find((p) => p.name === 'Calibrada');
  const result = replicate(toRows(ideation.ideas), policy, ideation.costs, { replications: 10 });
  const ideaRows = ideation.stages.map((stage, i) => ({ label: stage, value: result.reached[i], display: int(result.reached[i]) }));

  el.innerHTML = `
    <h2>Cinco funis, um motor</h2>
    <p class="lead">Cada funil responde à pergunta que costuma ser feita a ele, e mostra o número que a
    convenção padrão esconde. Os valores são recalculados aqui mesmo, a partir dos dados exportados pela
    biblioteca Python.</p>
    <div class="grid cards">
      ${card('Ideia → MVP', 'Quais ideias merecem um MVP, e quanta evidência compra essa decisão?',
    funnelChart(ideaRows, { label: 'Funil de ideias, política calibrada', width: 300 }),
    `Política calibrada: <strong>${brlM(result.net_value.mean)}</strong> de valor líquido médio, contra
       ${brlM(ideation.reference.find((r) => r.policy === 'Sem gates' && r.metric === 'net_value').mean)} sem gates.`,
    'ideation')}
      ${card('Marketing', 'Qual é a conversão, e quanto dela é definição?',
      funnelChart(rows(marketing.funnel), { label: 'Funil de marketing, coorte madura', width: 300 }),
      `A coorte do T4 converte <strong>${pct(q4.cohort_all, 2)}</strong>, metade do T3 maduro
       (${pct(q3.cohort_matured, 2)}). Nada mudou: ela ainda não maturou.`, 'multichannel')}
      ${card('Vendas', 'Quanto o pipeline aberto vai realmente fechar?',
        funnelChart(rows(sales.funnel_infer), { label: 'Pipeline de vendas', width: 300 }),
        `Contando só o registrado, proposta/qualificação dá <strong>${pct(proposalStep)}</strong>:
       negócios criados direto em proposta.`, 'sales')}
      ${card('Supply', 'Quanto da operação é trabalho feito duas vezes?',
          funnelChart(rows(supply.funnel), { label: 'Funil de atendimento', width: 300 }),
          `Rendimento final ${pct(rty.final_yield)}, mas RTY de <strong>${pct(rty.first_pass_yield)}</strong>:
       ${pct(supply.hidden_factory.orders_reworked_share)} dos pedidos retrabalhados.`, 'supply')}
      ${card('Gestão', 'Para onde vai o benefício anunciado?',
            funnelChart(rows(management.funnel), { label: 'Funil de execução estratégica', width: 300 }),
            `Realizado e medido: <strong>${pct(bridge.realised / bridge.announced)}</strong> do anunciado;
       ${brlM(-bridge['stopped before Benefício medido'])} entregues sem medição.`, 'management')}
    </div>`;
  el.querySelectorAll('[data-goto]').forEach((b) => b.addEventListener('click', () => goto(b.dataset.goto)));
  setCsv([['funil', 'etapa', 'entraram'],
    ...marketing.funnel.map((r) => ['marketing', r.stage, r.entered]),
    ...sales.funnel_infer.map((r) => ['vendas', r.stage, r.entered]),
    ...supply.funnel.map((r) => ['supply', r.stage, r.entered]),
    ...management.funnel.map((r) => ['gestão', r.stage, r.entered]),
    ...ideaRows.map((r) => ['ideia→mvp (média)', r.label, Math.round(r.value)])]);
  return {};
}
