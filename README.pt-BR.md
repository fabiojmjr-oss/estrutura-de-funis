# funilab — estruturas de funil, medidas

[![ci](https://github.com/fabiojmjr-oss/estrutura-de-funis/actions/workflows/ci.yml/badge.svg)](https://github.com/fabiojmjr-oss/estrutura-de-funis/actions/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)

Cinco funis — marketing, vendas, supply chain, execução estratégica e, no centro, o ciclo completo
de uma ideia captada até uma solução escalada — sobre um único motor de funil, com os dados
sintéticos para exercitar tudo isso. Python, com testes e tipagem. Repositório irmão do
[`ferramentas-de-trabalho`](https://github.com/fabiojmjr-oss/ferramentas-de-trabalho), construído
com as mesmas regras.

**[Read in English →](README.md)**

---

## Por que isso existe

Um funil é uma cadeia de razões, e a aritmética de uma razão nunca é onde o relatório de funil
erra. Ele erra nas convenções que ninguém escreve: se um negócio criado já em proposta passou pela
qualificação, se os clientes deste mês são divididos pelos leads deste mês ou pelos leads que os
geraram, se uma coorte que entrou semana passada conta como tendo falhado em converter.

Este repositório toma a mesma posição do irmão: essas convenções pertencem ao código, como
argumentos, com teste. Onde uma métrica de funil tem mais de uma definição legítima, a função
devolve todas, porque a diferença entre elas costuma ser o achado.

O quinto funil é a razão de o repositório existir. Um pipeline de ideias toma suas decisões mais
caras — quais ideias ganham um MVP — com menos dados do que qualquer outro funil da empresa. O
módulo `ideation` trata cada gate como um problema de medição com preço em cada tipo de erro, e o
[`docs/ciclo-ideia-mvp.md`](docs/ciclo-ideia-mvp.md) transforma isso num playbook com um template
para cada gate.

## Módulos

| Módulo | A pergunta que responde | Docs |
| --- | --- | --- |
| `funilab.synth` | Com que dados eu testo sem expor um negócio real? | [`DISCLAIMER.md`](DISCLAIMER.md) |
| `funilab.core` | Qual é a taxa de conversão, e quanto dela é definição? | — |
| `funilab.marketing` | Quanto custa um cliente, e qual canal o conquistou? | — |
| `funilab.sales` | Quanto o pipeline aberto vai realmente fechar? | — |
| `funilab.supply` | Quanto da operação é trabalho feito duas vezes? | — |
| `funilab.management` | Para onde vai o benefício anunciado, e por que o portfólio fica mais lento? | — |
| `funilab.ideation` | Quais ideias merecem um MVP, e quanta evidência compra essa decisão? | [README](src/funilab/ideation/README.md) · [playbook](docs/ciclo-ideia-mvp.md) |

Sequência de construção e regra de seleção em [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Instalação

```bash
git clone https://github.com/fabiojmjr-oss/estrutura-de-funis.git
cd estrutura-de-funis
make install
make check
```

## Trinta segundos

```python
import pandas as pd
from funilab.core import conversion_sensitivity
from funilab.marketing import MARKETING
from funilab.synth import generate_marketing

data = generate_marketing()  # reprodutível só a partir da semente
print(
    conversion_sensitivity(  # uma base de leads, cinco convenções
        data.events,
        MARKETING,
        start=pd.Timestamp("2025-10-01"),
        end=pd.Timestamp("2025-12-31"),
        window=pd.Timedelta(days=120),
    )
)
```

---

## Dez coisas que ele demonstra

### 1. A conversão do último trimestre cai pela metade, e nada aconteceu

A mesma base de leads, medida de cinco formas, em dois trimestres:

| Convenção | T3 (entrada jul–set) | T4 (entrada out–dez) |
| --- | --- | --- |
| Período: entradas em cada etapa contadas pela própria data | 2,33% | 2,46% |
| Coorte, o que atingiu até 31/dez | 2,45% | **1,23%** |
| Coorte, convertida em até 120 dias | 2,41% | 1,23% |
| Coorte, só leads cujos 120 dias já passaram | **2,68%** | — (nenhum) |

A coorte do T4 mostra metade da do T3. Nada mudou nos leads: um lead que entrou em novembro ainda
não teve os 30 a 60 dias que um ciclo de vendas leva. **Nenhuma coorte do T4 maturou, então a única
afirmação defensável sobre a conversão do T4 hoje é "ainda não se sabe"** — e o número de período,
que parece tranquilizadoramente estável, divide os clientes deste trimestre pelos leads deste
trimestre, que são outras pessoas. A coorte madura do T3 converte 2,68%, número que nenhuma das
outras convenções reporta para nenhum dos trimestres.

### 2. "Ataque a pior etapa" é verdade em pontos e falso em percentual

No funil maduro (36,8% → 32,0% → 22,4%), um **ganho relativo de 10% vale exatamente +10% de saída
em qualquer etapa**. Um ganho de um ponto vale +4,47% de saída na última etapa e +2,72% na
primeira, porque um ponto é uma fatia maior de uma taxa menor. As duas afirmações são aritmética;
nenhuma diz qual ganho é mais barato de comprar, e isso é a única coisa que decide onde o dinheiro
vai. `lever_table` devolve as duas colunas para que a discussão tenha de ser sobre custo.

### 3. O canal mais barato vira o mais caro trocando uma convenção

R$ 2,03 mi de mídia compraram 472 clientes de canais pagos. **O CAC blended é 2.569 e o CAC pago é
4.294** — o blended parece 40% mais barato porque divide a mesma verba por 789 clientes, 317 dos
quais vieram de indicação e busca orgânica, que a verba não comprou.

A atribuição então decide qual canal pago vence:

| Canal | CAC, primeiro toque | CAC, último toque | Posição primeiro → último |
| --- | --- | --- | --- |
| Eventos | **3.161** | **9.238** | 1 → 3 |
| Busca paga | 3.559 | 1.957 | 2 → 1 |
| Social pago | 8.189 | 4.649 | 3 → 2 |

Eventos abre jornadas e busca paga as fecha. **A mesma verba e os mesmos clientes tornam Eventos o
canal mais barato ou o mais caro, por um fator de 2,9**, e a decisão de orçamento vira numa
convenção que quase nunca está no slide.

### 4. Uma taxa de etapa de 109,5%

Uma oportunidade em cinco é criada direto em proposta — uma RFP que chega. Contar só as etapas que
foram registradas coloca **1.842 negócios em proposta contra 1.682 em qualificação, uma taxa de
etapa de 109,5%**. Inferir que um negócio em proposta passou pela qualificação dá 75,4%. Qualquer
meta de conversão por etapa definida sobre o dado registrado está definida sobre um artefato.

A taxa de ganho tem o mesmo problema em outra forma: **21,5% por quantidade e 15,6% por valor** nos
mesmos negócios fechados, porque negócios grandes fecham menos. Citar uma sem nomear a base é como
vendas e financeiro reportam taxas de ganho diferentes a partir do mesmo CRM.

### 5. Probabilidades melhores não consertam a previsão. Tirar os negócios mortos conserta.

O pipeline sintético guarda o desfecho final de cada negócio aberto, então a previsão pode ser
avaliada em vez de discutida. Pipeline aberto em 31/dez: R$ 22,1 mi em 333 negócios.

| Previsão | Ganho esperado | Erro contra o que foi ganho |
| --- | --- | --- |
| Probabilidades padrão do CRM (10/25/50/75%) | 7,97 mi | **+45,8%** |
| Taxa histórica de ganho por etapa | 8,19 mi | **+49,9%** |
| Histórica, negócios parados zerados | 5,38 mi | **−1,5%** |

Trocar os números redondos do CRM pelo histórico do próprio pipeline — o conselho padrão —
**piora levemente a previsão**. O erro não está nas probabilidades; está em 83 negócios somando
R$ 7,8 mi que estão na etapa há mais tempo que 85% dos negócios já ganhos a partir dela. Eles acabam
ganhando 4,8% das vezes, contra 43,6% dos demais. A idade na etapa é a evidência, e ela já está no
CRM.

### 6. Rendimento final de 99,3% numa operação que mexe duas vezes em um pedido a cada quatro

| Etapa | Rendimento de primeira passagem | Rendimento final |
| --- | --- | --- |
| Crédito | 92,9% | 99,8% |
| Separação | 95,0% | 99,9% |
| Conferência | 96,5% | 99,9% |
| Expedição | 97,5% | 99,9% |
| Entrega | 91,8% | 99,8% |
| **Cadeia** | **76,2% (RTY)** | **99,3%** |

O funil de atendimento quase não perde nada, por isso o relatório dele é verde. **O rendimento
acumulado (RTY) é 76,2%: 23,5% dos pedidos foram manuseados duas vezes em algum ponto**, e essas
repetições são a fábrica oculta que o funil não mostra porque só conta quem chegou.

A checagem de pedido perfeito saiu contra a expectativa e está reportada assim: o produto das
quatro taxas componentes (85,86%) e a taxa conjunta medida (85,85%) concordam em um centésimo de
ponto aqui, porque o fator comum mexe pouco em cada componente. A hipótese de independência
costuma ser apontada como a falha de multiplicar componentes; neste dado ela não custa nada, e
`perfect_order` devolve as duas para que isso seja medido, não suposto, em qualquer direção.

### 7. Mais benefício entregue sem medição do que entregue com medição

Acompanhando as iniciativas propostas um ano inteiro antes do horizonte, do anúncio ao resultado:

| Barra | R$ mi | Fração do anunciado |
| --- | --- | --- |
| Anunciado | 134,4 | 100% |
| Não aprovado | −59,5 | −44,3% |
| Parado antes de financiamento, início ou entrega | −38,7 | −28,8% |
| **Entregue, benefício nunca medido** | **−14,6** | **−10,9%** |
| Ainda em andamento | −2,9 | −2,1% |
| Entregue abaixo do plano | −4,4 | −3,2% |
| **Realizado e medido** | **14,3** | **10,6%** |

A ponte reconcilia exatamente. As rejeições na aprovação são o gate funcionando. A linha que não é
fica na terceira posição de baixo para cima dos vazamentos: **R$ 14,6 mi de benefício planejado
foram entregues e nunca medidos, mais que os 14,3 mi que foram** — o portfólio não consegue dizer
se o seu maior resultado isolado aconteceu.

### 8. Todo projeto está no prazo e o portfólio está ficando mais lento

Lei de Little na execução: o trabalho em andamento subiu de 47,2 iniciativas no primeiro semestre
para 68,2 no segundo. **O lead time medido no que terminou é 149 dias; WIP dividido por vazão
implica 197.** A diferença é o estoque de trabalho ainda dentro do sistema, que o número medido não
enxerga porque só conta o que saiu. Com a mesma vazão, cortar o WIP pela metade implica 98 dias —
começar menos é o jeito mais barato de terminar antes, e não precisa de orçamento.

### 9. O score de triagem é a evidência mais fraca do ciclo, e faz o maior corte

RICE e ICE são pontuados na captação, antes de qualquer evidência existir. Contra o desfecho que
deveriam antecipar:

| Score | Ideias boas no top 20% | Correlação de postos com o valor |
| --- | --- | --- |
| RICE | 26,2% | 0,200 |
| ICE | 23,8% | 0,155 |
| *Taxa base* | *17,4%* | — |

No portfólio de 628 ideias usado nos achados 9 e 10, o melhor score eleva a fração de ideias boas
em nove pontos sobre escolher ao acaso. **Usado para cortar 40% da lista, ele elimina 25 das 109
ideias boas antes de alguém falar com um cliente**; usado para cortar 70%, como faz a política mais
rígida abaixo, elimina 64. Um score é apoio de conversa. Cinco entrevistas com clientes custam
R$ 2.000 e são evidência melhor que qualquer score.

A própria evidência precisa de leitura: 2 de 5 entrevistados confirmando uma dor é 40% contra uma
barra de 35%, e uma leitura pontual aprova. A probabilidade a posteriori de a taxa real passar a
barra é 0,58.

### 10. Mais rigor perde dinheiro; evidência calibrada ganha mais

Cinco políticas de gate, cada uma replicada 30 vezes num portfólio de 628 ideias com verdade
conhecida (valor líquido médio e a faixa de 2,5–97,5% das rodadas, R$ mi):

| Política | MVPs construídos | Boas escaladas | Ruins escaladas | Valor líquido | Faixa |
| --- | --- | --- | --- | --- | --- |
| Sem gates (constrói tudo) | 628 | 109 | 519 | **−124,6** | — |
| Intuição (score de feeling, amostras pequenas lidas pelo valor pontual) | 85,8 | 50,4 | 4,7 | 19,8 | 13,3 – 25,6 |
| Evidência (corte por RICE, amostras maiores, posterior de 80%) | 77,5 | 58,5 | 0,2 | 24,3 | 16,7 – 31,2 |
| Rigor máximo (corte de 70%, amostras grandes, 95%) | 41,1 | 31,7 | 0,0 | 16,6 | 10,9 – 19,6 |
| **Calibrada** (sem corte por score, 5 entrevistas, 60% com segunda rodada) | **110,4** | **87,1** | 2,5 | **31,5** | **26,9 – 35,8** |

Três resultados. **Os gates são onde está o dinheiro**: sem eles o ciclo perde R$ 124,6 mi, quase
tudo escalando 519 ideias que nunca foram boas. **Rigor não é virtude em si**: o rigor máximo não
escala nenhuma ideia ruim e ainda assim é o que menos ganha entre as políticas com gate, porque uma
ideia boa perdida vale cerca de duas vezes o que uma ruim escalada custa, e uma barra de 95% com
corte de 70% por score é construída para cometer exatamente esse erro. E **a política calibrada
constrói mais MVPs e ganha mais dinheiro** — sua pior rodada (26,9) fica acima da melhor da
intuição (25,6) — porque gasta em evidência barata para toda ideia em vez de num score, e define a
barra de confiança pelo custo de cada erro, não por quão rigorosa ela soa.

A política calibrada foi escolhida por busca em grade no portfólio da semente 42. Todos os números
acima vêm de um **portfólio independente (semente 2026)**, para que a busca não avalie a si mesma.

Um defeito foi encontrado no caminho e mudou o desenho. Com o prior uniforme que a maioria dos
tutoriais bayesianos usa por padrão, um smoke test com barra de 4% começa com 96% de confiança de
que a ideia passa, e **dois visitantes que vão embora bastam para aprovar a 80%** (a posterior é
0,88). O prior padrão aqui é neutro na barra — chances exatamente iguais antes de qualquer
evidência — e o teste que reproduz o defeito continua na suíte.

---

## Exemplos

Sete scripts executáveis, cada um imprimindo o raciocínio por trás dos números, não só os números.
Todos são executados pela suíte de testes.

| Script | A pergunta que ele percorre |
| --- | --- |
| [`01_conversion_definition.py`](examples/01_conversion_definition.py) | Quanto de uma taxa de conversão é definição e não desempenho |
| [`02_marketing_acquisition.py`](examples/02_marketing_acquisition.py) | Quanto custa um cliente, e qual canal merece o crédito |
| [`03_sales_forecast.py`](examples/03_sales_forecast.py) | Quanto o pipeline aberto vai fechar, e por que o CRM superestima |
| [`04_supply_hidden_factory.py`](examples/04_supply_hidden_factory.py) | O rendimento final do funil de atendimento, e a fábrica escondida atrás dele |
| [`05_strategy_execution.py`](examples/05_strategy_execution.py) | Para onde vai o benefício anunciado, e por que o portfólio fica mais lento |
| [`06_idea_scoring.py`](examples/06_idea_scoring.py) | Se o score de triagem prevê algo, e quanta evidência um gate precisa |
| [`07_idea_to_mvp.py`](examples/07_idea_to_mvp.py) | O ciclo completo da ideia captada à solução escalada, sob cinco políticas |

## O ciclo ideia → MVP

O playbook em [`docs/ciclo-ideia-mvp.md`](docs/ciclo-ideia-mvp.md) percorre as sete etapas de ponta
a ponta — captação, triagem, problema, solução, MVP, validação, escala — com a pergunta que cada
gate responde, a evidência que exige, a barra definida antes, e a função que a lê. A pasta
[`templates/`](templates/) tem um cartão para cada uma: canvas da ideia, roteiro de entrevista,
cartão de experimento, checklist de gate e scorecard de MVP.

---

## Princípios de projeto

**Toda convenção é um argumento.** Etapas puladas, base coorte ou período, janela de maturidade,
modelo de atribuição, base da taxa de ganho, prior. Nenhuma tem padrão silencioso onde a escolha
muda a resposta.

**Devolver toda definição legítima.** Cinco convenções de conversão, quatro taxas de ganho, quatro
modelos de atribuição, rendimento de primeira passagem ao lado do final, produto ao lado do
conjunto.

**Avaliar contra a verdade onde o dado sintético permite.** O gerador leva negócios abertos e
ideias até o fim e guarda o desfecho à parte, então previsões e políticas de gate são pontuadas
contra o que aconteceu, não umas contra as outras.

**Nunca reportar uma estimativa pontual estocástica como resposta.** Políticas de gate são
replicadas e carregam uma faixa; uma diferença dentro da faixa não é reportada como vitória.

**Ajustar numa amostra, reportar em outra.** A política calibrada foi escolhida num portfólio e
todo número publicado vem de um segundo.

**Reportar o resultado que contradiz o discurso.** Probabilidades melhores de CRM pioraram a
previsão; a hipótese de independência do pedido perfeito não custou nada; rigor máximo ganhou
menos. Os três estão no README porque saíram assim.

**Reconciliar exatamente ou falhar.** A ponte de benefício levanta erro em vez de desenhar uma
barra que não fecha.

**Testar contra cálculo à mão.** Todo módulo é testado em fixtures pequenas o bastante para
calcular no papel; a distribuição Beta é testada contra formas fechadas, não contra si mesma.

**Nenhum dado real, nunca.** Ver [`DISCLAIMER.md`](DISCLAIMER.md).

**O README está sob teste.** Todo número acima é verificado em `tests/test_readme_claims.py`, e os
exemplos também são executados lá.

## Limitações

- O dado sintético é **plausível**, não calibrado. Nenhum número aqui é desempenho de negócio real,
  e o ranking de políticas de gate em particular depende do custo de um MVP em relação ao valor de
  uma ideia boa: mude essa razão e a política calibrada muda junto. O método se transfere; a
  política, não.
- Os gates são binários com no máximo uma rodada extra. Pipelines reais pivotam — uma ideia que
  falha no gate de solução costuma voltar com outra solução — e pivôs não são modelados.
- A evidência de ideias é simulada como sorteios binomiais independentes. Entrevistas reais não são
  independentes nem imparciais (perguntas indutoras, clientes simpáticos), então amostras reais
  carregam menos informação que o mesmo número de simuladas.
- A atribuição é por regra. Ainda não há modelo orientado a dados (Shapley ou Markov), e nenhum dos
  modelos por regra é estimativa causal do efeito de um canal.
- A previsão de vendas se avalia contra desfechos que só o dado sintético fornece. Em dado real, a
  mesma comparação precisa de um backtest sobre trimestres fechados.
- A Lei de Little é aplicada a uma etapa com uma única classe de trabalho; iniciativas de tamanhos
  muito diferentes dividem uma só contagem de WIP.

## Desenvolvimento

```bash
make install    # instalação editável com as ferramentas de desenvolvimento
make check      # lint, formatação, tipos e a suíte rápida - o que libera um push
make check-all  # o acima mais todo número documentado re-derivado
make claims     # re-deriva todo número citado num README
```

**109 testes, divididos por custo.** 88 deles rodam em poucos segundos e liberam cada push; o
restante re-deriva todo número citado acima, replica as políticas de gate e executa todos os
exemplos. A cobertura de linhas é reportada pelo `make check` e é o único número sobre o
repositório que não está sob teste.

## Licença

MIT. Ver [`LICENSE`](LICENSE).
