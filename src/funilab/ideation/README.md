# funilab.ideation — the idea-to-MVP cycle

**EN** · [Português](#português)

Seven stages, six gates. Each gate reads a small experiment against a bar set in advance, and a
gate *policy* — how many ideas triage lets through, how much evidence each gate buys, how
confident the committee must be — is simulated on a portfolio whose truth is known, so the policy
can be priced by what it kills and what it scales.

| Piece | Functions | Question |
| --- | --- | --- |
| Scoring | `rice`, `ice`, `score_validity`, `top_overlap` | Does the triage score predict anything on this portfolio? |
| Evidence | `prob_above`, `decide`, `sample_size`, `neutral_prior` | Does this experiment clear the bar, and how large must it be? |
| Gates | `GatePolicy`, `simulate_policy`, `compare_policies` | What does a policy cost, and what does it return? |
| Economics | `stage_value`, `break_even_payoff` | What is an idea worth at each stage? |

**Evidence.** `prob_above(k, n, bar)` is the posterior probability that the true rate exceeds the
bar. The Beta CDF is computed by continued fraction (no SciPy) and tested against closed forms.
The default prior has its **median** on the bar and the weight of two observations — exactly even
odds before any evidence. The uniform prior is not neutral at low bars: against 4% it starts at
96% and passes an idea on two visitors who both leave. That defect was found by the module's own
example and is kept as a test.

**Gates.** `decide` returns `go`, `kill` or `more evidence`; in the simulation an idea between
`kill` and `go` gets one second round of the same size and is then advanced only if the pooled
evidence reaches `go`. Every policy result is replicated and reported as a range.

**What the simulation found** (README findings 9 and 10): cutting on the score is the most
expensive gate, because the score is the weakest evidence; a 95% bar makes the least money of any
gated policy, because a missed good idea is worth about twice what a scaled bad one costs; and the
calibrated policy — no score cut, five interviews, 60% with a second round — builds the most MVPs
and returns the most. It was tuned on one portfolio and is reported on another.

**Limits.** Binary gates with one extra round; no pivots. Evidence is simulated as independent
binomial draws, which real interviews are not. The policy ranking depends on the ratio of MVP cost
to the value of a good idea; the method transfers, the policy does not.

Playbook and templates: [`docs/ciclo-ideia-mvp.md`](../../../docs/ciclo-ideia-mvp.md).

## Português

Sete etapas, seis gates. Cada gate lê um experimento pequeno contra uma barra definida antes, e
uma *política* de gates — quantas ideias a triagem deixa passar, quanta evidência cada gate compra,
quão confiante o comitê precisa estar — é simulada num portfólio de verdade conhecida, para que a
política seja precificada pelo que mata e pelo que escala.

| Peça | Funções | Pergunta |
| --- | --- | --- |
| Score | `rice`, `ice`, `score_validity`, `top_overlap` | O score de triagem prevê algo neste portfólio? |
| Evidência | `prob_above`, `decide`, `sample_size`, `neutral_prior` | Este experimento passa a barra, e de que tamanho precisa ser? |
| Gates | `GatePolicy`, `simulate_policy`, `compare_policies` | Quanto uma política custa, e quanto devolve? |
| Economia | `stage_value`, `break_even_payoff` | Quanto vale uma ideia em cada etapa? |

**Evidência.** `prob_above(k, n, barra)` é a probabilidade a posteriori de a taxa real passar a
barra. A CDF da Beta é calculada por fração contínua (sem SciPy) e testada contra formas fechadas.
O prior padrão tem a **mediana** na barra e o peso de duas observações — chances exatamente iguais
antes de qualquer evidência. O prior uniforme não é neutro em barras baixas: contra 4% ele começa
em 96% e aprova uma ideia com dois visitantes que foram embora. O defeito foi achado pelo próprio
exemplo do módulo e ficou como teste.

**Gates.** `decide` devolve `go`, `kill` ou `more evidence`; na simulação, uma ideia entre `kill` e
`go` ganha uma segunda rodada do mesmo tamanho e só avança se a evidência somada atingir `go`. Todo
resultado de política é replicado e reportado como faixa.

**O que a simulação encontrou** (achados 9 e 10 do README): cortar pelo score é o gate mais caro,
porque o score é a evidência mais fraca; uma barra de 95% é a que menos ganha entre as políticas
com gate, porque uma ideia boa perdida vale cerca de duas vezes o que uma ruim escalada custa; e a
política calibrada — sem corte por score, cinco entrevistas, 60% com segunda rodada — constrói mais
MVPs e devolve mais. Foi ajustada num portfólio e é reportada em outro.

**Limites.** Gates binários com uma rodada extra; sem pivôs. A evidência é simulada como sorteios
binomiais independentes, o que entrevistas reais não são. O ranking das políticas depende da razão
entre custo de MVP e valor de uma ideia boa; o método se transfere, a política não.

Playbook e templates: [`docs/ciclo-ideia-mvp.md`](../../../docs/ciclo-ideia-mvp.md).
