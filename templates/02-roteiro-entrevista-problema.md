# Roteiro de entrevista de problema

> Gate 2. Princípios do *The Mom Test* (Rob Fitzpatrick): pergunte sobre o passado e o
> comportamento, nunca peça opinião sobre a sua ideia. **Não apresente a solução.**
> Ver [playbook](../docs/ciclo-ideia-mvp.md#gate-2--problema-triada--problema-validado).

**Ideia:** ____ · **Entrevistado (perfil, sem dado pessoal):** ____ · **Data:** ____

## Abertura (2 min)

"Estou tentando entender como [segmento] lida com [contexto]. Não tenho nada para vender."

## Perguntas (20 min)

1. Conte a última vez que [situação do problema] aconteceu. O que você fez?
2. Com que frequência isso acontece?
3. O que você já tentou para resolver? Quanto isso custou (tempo, dinheiro, retrabalho)?
4. O que acontece se não resolver?
5. Quem mais é afetado? Quem decide sobre isso?
6. Se pudesse mudar uma coisa nesse processo, qual seria? *(só no fim)*

## Evitar

- "Você usaria…?", "Você pagaria…?", "Não seria ótimo se…?" — respostas sobre o futuro são
  educadas, não evidência.

## Registro (preencher logo após)

| Critério | Sim / Não | Evidência (citação ou fato) |
| --- | --- | --- |
| Relatou o problema espontaneamente, num caso concreto | | |
| Já gastou tempo ou dinheiro tentando resolver | | |
| **Conta como "dor confirmada"** (as duas acima) | | |

## Consolidação do gate

| Rodada | Entrevistas (n) | Dor confirmada (k) | `prob_above(k, n, 0.35)` | Decisão |
| --- | --- | --- | --- | --- |
| 1 | 5 | | | go ≥ 0,60 · kill ≤ 0,20 · senão rodada 2 |
| 2 | +5 | | | go ≥ 0,60 · senão kill |
