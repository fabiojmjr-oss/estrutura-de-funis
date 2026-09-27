# Ciclo ideia → MVP → solução

Playbook do funil de captação de ideias, de ponta a ponta. Sete etapas, seis gates, uma regra:
**cada gate responde uma pergunta, com uma evidência nomeada, contra uma barra definida antes de
olhar o resultado.** O código que lê cada evidência está em `funilab.ideation`; os números que
sustentam as escolhas abaixo estão nos achados 9 e 10 do [README](../README.pt-BR.md).

---

## 1. Por que um funil de ideias precisa de estrutura

É o funil com as decisões mais caras e os dados mais pobres da empresa. Um MVP custa dezenas a
centenas de milhares de reais; a decisão de construí-lo costuma ser tomada com um score preenchido
na captação, antes de qualquer contato com cliente. Três erros se repetem:

| Erro | Como aparece | O que custa (simulação, achado 10) |
| --- | --- | --- |
| **Construir sem gate** | "Vamos testar construindo" | R$ −124,6 mi: 519 ideias ruins escaladas |
| **Cortar pelo score** | Top 30% do RICE segue, o resto morre | 64 das 109 ideias boas mortas antes de uma entrevista |
| **Rigor como virtude** | Barra de 95% em toda etapa | Menor valor entre as políticas com gate (R$ 16,6 mi) |

A política que mais gerou valor (R$ 31,5 mi, faixa 26,9–35,8) fez o contrário dos três: **não
cortou pelo score, gastou pouco em evidência para toda ideia, e calibrou a barra pelo custo de
cada erro.**

### Referências de mercado que o ciclo integra

| Referência | O que o ciclo aproveita |
| --- | --- |
| *Customer Development* — Steve Blank | Descoberta do cliente antes de construir (etapas 3–4) |
| *The Lean Startup* — Eric Ries (2011) | Construir–medir–aprender; MVP como experimento, não versão 1 |
| *Stage-Gate* — Robert G. Cooper | Gates com critérios de avanço definidos antes |
| *Double Diamond* — UK Design Council (2005) | Divergir/convergir no problema, depois na solução |
| *The Mom Test* — Rob Fitzpatrick | Entrevistas sobre comportamento passado, não opinião futura |
| *Jobs to be Done* — Clayton Christensen | Formular o problema como o "trabalho" que o cliente contrata |
| *Opportunity Solution Tree* — Teresa Torres | Ligar oportunidade → soluções → experimentos |
| Teste de PMF de 40% — Sean Ellis | Pergunta "quão decepcionado você ficaria…" no gate do MVP |
| RICE (Intercom) e ICE (Sean Ellis) | Scores de triagem — usados como apoio, não como filtro |
| *Working Backwards* / PR-FAQ — Amazon | Escrever o comunicado de lançamento antes de construir (etapa 1) |

### Ponte com Lean Six Sigma

Para quem vem de melhoria de processos, o ciclo é um **DMADV** (Design for Six Sigma) com gates
estatísticos:

| DMADV | Etapa do ciclo | Ferramenta equivalente |
| --- | --- | --- |
| Define | Captada → Triada | Project charter ≈ canvas da ideia |
| Measure | Problema validado | VOC ≈ entrevistas de problema; CTQs ≈ critério de dor |
| Analyze | Solução validada | Teste de hipótese ≈ smoke test com barra fixada |
| Design | MVP construído | Protótipo mínimo, escopo congelado |
| Verify | MVP validado → Escalada | Piloto com critério de aceite; plano de controle |

A diferença para um DMAIC: aqui a hipótese nula mais provável é que **a ideia não vale**
(82,6% das ideias do portfólio simulado não são boas). O desenho dos gates parte disso.

---

## 2. Visão geral

```
Captada ─[G1 Triagem]→ Triada ─[G2 Problema]→ Problema validado ─[G3 Solução]→ Solução validada
   → MVP construído ─[G4 Retenção]→ MVP validado ─[G5 Escala]→ Escalada
```

| # | Etapa atingida | Pergunta do gate anterior | Evidência | Barra padrão | Prazo |
| --- | --- | --- | --- | --- | --- |
| 0 | **Captada** | Está escrita de forma que outra pessoa julgue? | Canvas completo | 100% dos campos | contínuo |
| 1 | **Triada** | Vale uma hora? | Aderência estratégica; não é duplicata | sim/não | 7 dias |
| 2 | **Problema validado** | O problema existe, para quem, e dói? | Entrevistas de problema | P(dor > 35%) ≥ 60% | 14 dias |
| 3 | **Solução validada** | Vão agir diante da solução proposta? | Smoke test (landing, pré-venda) | P(conversão > 4%) ≥ 60% | 21 dias |
| 4 | **MVP construído** | O menor build que testa valor cabe no orçamento? | Escopo e custo aprovados | ≤ teto do MVP | 60 dias |
| 5 | **MVP validado** | Quem usa continua usando? | Retenção / teste de 40% | P(retenção > 33%) ≥ 60% | 45 dias |
| 6 | **Escalada** | A economia unitária sobrevive à escala? | Unit economics, capacidade | Payback ≤ meta | 14 dias |

As barras e o nível de confiança (60%) são o ponto de partida calibrado na simulação; **cada
organização deve recalibrá-los** com os próprios custos (ver seção 5).

---

## 3. As etapas, uma a uma

### Etapa 0 — Captação

**Objetivo:** transformar uma intuição em algo julgável por outra pessoa.

- Canal aberto a todos (colaboradores, clientes, dados, parceiros). No portfólio simulado, ideias
  de **clientes** e de **dados** têm problema real em 45–50% dos casos; de colaboradores, 30%. A
  fonte é informação — registre-a.
- Todo registro usa o [canvas da ideia](../templates/01-canvas-da-ideia.md): problema, para quem,
  evidência atual, hipótese de solução, e o comunicado de lançamento em uma frase (PR-FAQ).
- RICE/ICE podem ser preenchidos aqui, **como apoio de conversa**. Não decidem nada.

**Métrica da etapa:** ideias captadas por mês, por fonte; % de canvas completos.

### Gate 1 — Triagem (Captada → Triada)

**Pergunta:** vale uma hora de alguém?

- Critérios binários: aderente à estratégia? Não é duplicata? Tem um "para quem" identificável?
- **Não corte pelo score.** Achado 9: o RICE eleva a fração de ideias boas no top 20% de 17,4%
  para 26,2%. Cortar 40% da lista pelo score mata 25 de 109 ideias boas; cinco entrevistas
  (R$ 2 mil) são evidência melhor que qualquer score.
- Use o score só para **ordenar a fila** quando a capacidade de entrevistas for o gargalo.

**Função:** `funilab.ideation.score_validity` — rode no seu histórico para saber se o seu score
prevê alguma coisa antes de usá-lo para ordenar.

### Gate 2 — Problema (Triada → Problema validado)

**Pergunta:** o problema existe, para quem, e dói o bastante para agir?

- **5 entrevistas por ideia** na primeira rodada, pelo [roteiro de entrevista de
  problema](../templates/02-roteiro-entrevista-problema.md) (princípios do *The Mom Test*: fatos
  do passado, não opiniões sobre o futuro).
- Evidência contável: entrevistado relata o problema **e** já gastou tempo ou dinheiro tentando
  resolvê-lo.
- Leitura: `decide(k, n, barra=0.35, go=0.6, kill=0.2)`. Entre 0,2 e 0,6 → **segunda rodada** de
  mais 5 entrevistas, e decide sobre o total.
- Atenção à leitura pontual: 2 de 5 é 40% e "passa" numa barra de 35%, mas a probabilidade de a
  taxa real passar a barra é só 0,58.

### Gate 3 — Solução (Problema validado → Solução validada)

**Pergunta:** diante da solução proposta, as pessoas agem?

- Smoke test: landing page com pré-cadastro, pré-venda, carta de intenção, protótipo navegável com
  CTA. Registre no [cartão de experimento](../templates/03-cartao-de-experimento.md) **antes** de
  rodar: hipótese, métrica, amostra, barra.
- Tamanho de amostra: `sample_size(taxa_esperada, barra)`. Uma ideia boa (7% contra barra de 4%)
  decide em ~44 visitantes; uma na fronteira (4,5%) precisa de ~1.175. Se a amostra necessária não
  cabe no prazo, a resposta é "a ideia está perto demais da barra para este teste" — não "rodar
  mais uma semana e ver".
- **Prior neutro.** O padrão do código dá chances iguais antes dos dados. O prior uniforme dos
  tutoriais começa com 96% de confiança numa barra de 4% e aprova com dois visitantes que vão
  embora.

### Etapa 4 — MVP construído

**Pergunta:** qual o menor build que testa **valor** (não viabilidade técnica)?

- Escopo congelado no cartão de experimento: uma jornada, um segmento, uma métrica de valor.
- Teto de custo e prazo (padrão da simulação: R$ 80 mil, 60 dias). Estourou → volta ao gate com o
  aprendizado, não segue automaticamente.
- Tipos de MVP por custo crescente: concierge (manual), Mágico de Oz (manual por trás de uma
  interface), piloto com um cliente, produto mínimo.

### Gate 4 — Retenção (MVP construído → MVP validado)

**Pergunta:** quem usa continua usando?

- Métrica primária: retenção na semana 4 (ou o ciclo natural de uso) **ou** o teste de 40% de Sean
  Ellis ("muito decepcionado se não pudesse mais usar"). Registre no
  [scorecard do MVP](../templates/05-scorecard-mvp.md).
- ~60 usuários na primeira rodada; `decide(k, n, barra=0.33, go=0.6)`.
- Métricas secundárias (NPS, uso, receita) informam o pivô, não o gate.

### Gate 5 — Escala (MVP validado → Escalada)

**Pergunta:** a economia unitária sobrevive à escala?

- [Decisão de escala](../templates/06-decisao-de-escala.md): CAC esperado (use `funilab.marketing`
  para não cair no CAC blended), margem, payback, capacidade operacional (use `funilab.supply` se
  a solução passa pela operação).
- Uma ideia ruim escalada custa o investimento de escala inteiro (R$ 250 mil na simulação); é o
  erro mais caro por unidade, e o gate 4 já o torna raro — o gate 5 existe para o que retenção não
  mede: custo de servir e canal.

---

## 4. Governança e cadência

| Ritual | Frequência | Quem | Entrada | Saída |
| --- | --- | --- | --- | --- |
| Triagem | Semanal, 30 min | Dono do portfólio + 1 par | Canvas novos | Triada / arquivada / duplicata |
| Revisão de gates | Quinzenal, 60 min | Comitê de 3 pessoas | [Checklist de gate](../templates/04-checklist-de-gate.md) de cada ideia | go / kill / mais evidência |
| Revisão de portfólio | Mensal | Liderança | Funil (`funnel_table`), WIP, custo por solução | Ajuste de barras e capacidade |
| Recalibração | Semestral | Dono do portfólio | Desfechos reais das ideias | Novas barras, novo prior |

**Regras de governança:**

1. **Barra antes do dado.** O cartão de experimento é assinado antes de rodar. Barra movida depois
   do resultado anula o gate.
2. **Kill é resultado, não fracasso.** Registre o aprendizado; ideias mortas com evidência são o
   funil funcionando.
3. **Limite de WIP.** Máximo de MVPs em construção simultânea. Pela Lei de Little (achado 8), com a
   mesma vazão, metade do WIP é metade do lead time.
4. **Dono único por ideia** do gate 2 em diante.

### Indicadores do funil

| Indicador | Função | Leitura |
| --- | --- | --- |
| Conversão por etapa (coorte madura) | `funnel_table(..., mature_only=True)` | Onde as ideias morrem |
| Tempo por etapa (mediana e p85) | `stage_durations` | Onde as ideias esperam |
| WIP, vazão e lead time | `littles_law` | Se o portfólio está congestionado |
| Custo por solução escalada boa | `simulate_policy(...).summary` | Eficiência do ciclo |
| Ideias boas mortas (quando o desfecho for conhecido) | revisão semestral | Se as barras estão rígidas demais |

---

## 5. Como calibrar as barras para a sua realidade

As barras deste playbook vêm de uma simulação com custos específicos. O que se transfere é o
método:

1. **Levante os custos**: entrevista, smoke test, MVP, investimento de escala, e o valor médio de
   uma ideia boa escalada.
2. **Estime as taxas reais** de dor, conversão e retenção de ideias boas e ruins a partir do
   histórico (mesmo poucas dezenas de ideias já ajudam).
3. **Monte o portfólio sintético** com esses parâmetros (`generate_ideas` recebe as fontes e suas
   taxas de problema real; as taxas de dor, conversão e retenção são constantes de
   `funilab.synth.ideation`, e os custos vão em `CycleCosts`) e **compare políticas** com
   `compare_policies`.
4. **Ajuste num portfólio, reporte em outro** (outra semente), para que a busca não se avalie.
5. **Regra de bolso**: se uma ideia boa perdida vale mais que uma ruim escalada custa, baixe o
   nível de confiança exigido (60% em vez de 80–95%) e use segunda rodada; se o contrário, suba.

`funilab.ideation.stage_value` mostra o valor esperado de uma ideia em cada etapa: na simulação,
R$ 57 mil na captação e R$ 510 mil ao ser validada. A ideia não mudou; a evidência removeu as
formas de ela falhar. **Essa subida é o que o gasto em cada gate compra.**

---

## 6. Templates

| Template | Usado em |
| --- | --- |
| [`templates/01-canvas-da-ideia.md`](../templates/01-canvas-da-ideia.md) | Captação |
| [`templates/02-roteiro-entrevista-problema.md`](../templates/02-roteiro-entrevista-problema.md) | Gate 2 |
| [`templates/03-cartao-de-experimento.md`](../templates/03-cartao-de-experimento.md) | Gates 3 e 4 |
| [`templates/04-checklist-de-gate.md`](../templates/04-checklist-de-gate.md) | Toda revisão de gate |
| [`templates/05-scorecard-mvp.md`](../templates/05-scorecard-mvp.md) | Gate 4 |
| [`templates/06-decisao-de-escala.md`](../templates/06-decisao-de-escala.md) | Gate 5 |

## 7. Limites deste playbook

- Os números vêm de dado sintético plausível, não calibrado. O ranking das políticas depende da
  razão entre custo de MVP e valor de ideia boa.
- Pivôs não estão modelados: na prática, uma ideia que falha no gate 3 frequentemente volta ao
  gate 2 com outro segmento ou outra solução. Trate como nova ideia com histórico.
- Entrevistas reais têm viés (clientes simpáticos, perguntas indutoras); valem menos que o mesmo
  número de entrevistas simuladas. Compense com o roteiro, não com amostras maiores.
