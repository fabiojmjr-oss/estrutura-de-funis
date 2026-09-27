# Roadmap

Seven modules in the first wave, and a short list for the next. The sequence mirrors the sister
repository: the foundation generates the data every later module consumes, and each wave is
shippable on its own.

Selection rule — a module earns a place only if it answers a question someone accountable for the
funnel actually has, and if the answer would change a decision. A metric that is interesting but
decision-neutral is left out.

## Status

| # | Module | Question it answers | Wave |
| --- | --- | --- | --- |
| 0 | `funilab.synth` | What data do I test against without exposing a real business? | 1 — done |
| 1 | `funilab.core` | What is the conversion rate, and how much of it is definition? | 1 — done |
| 2 | `funilab.marketing` | What does a customer cost, and which channel earned it? | 1 — done |
| 3 | `funilab.sales` | What will the open pipeline actually close? | 1 — done |
| 4 | `funilab.supply` | How much of the operation is doing work twice? | 1 — done |
| 5 | `funilab.management` | Where does announced benefit go, and why does the portfolio slow down? | 1 — done |
| 6 | `funilab.ideation` | Which ideas deserve an MVP, and how much evidence buys that decision? | 1 — done |

## Wave 1 — foundation and five funnels *(complete)*

One engine (`core`) with every convention as an argument, a generator that keeps each entity's
eventual outcome aside, and one module per funnel. The idea-to-MVP cycle is the centre: it has a
playbook (`docs/ciclo-ideia-mvp.md`) and six templates.

Two results came out against the design and were kept. The first version of the evidence module
used a uniform prior, and its own example showed a smoke test "passing" on two visitors who both
left; the default is now a prior neutral at the bar, and the test that reproduces the defect stays.
And the "Evidence" gate policy — larger samples and an 80% posterior — did not clearly beat
intuition until the score cut was removed and the confidence bar was set from the cost of each
error; the calibrated policy was then selected on one portfolio and reported on another.

## Wave 2 — candidates

| Candidate | Question | Why it would change a decision |
| --- | --- | --- |
| Pivot model in `ideation` | What is an idea that failed a gate worth if it returns with a new segment? | Kill-versus-pivot is the most frequent gate decision and the least measured |
| Hierarchical prior from history | How much does a portfolio's past shorten each new experiment? | Smaller samples at the same confidence are cheaper gates |
| Data-driven attribution (Markov removal effect) | Which channel's removal loses the most customers? | Rule-based attribution flips the budget (finding 3); a data-driven model can arbitrate |
| Pipeline backtest in `sales` | How would the forecast have scored over past closed quarters? | Real data has no eventual outcome; a backtest is the substitute |
| Cross-funnel study | Marketing → sales → supply as one chain: where does a point of conversion buy the most margin? | Funnels are managed by different owners and optimised separately |
