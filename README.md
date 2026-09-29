# funilab — funnel structures, measured

[![ci](https://github.com/fabiojmjr-oss/estrutura-de-funis/actions/workflows/ci.yml/badge.svg)](https://github.com/fabiojmjr-oss/estrutura-de-funis/actions/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)
[![pages](https://github.com/fabiojmjr-oss/estrutura-de-funis/actions/workflows/pages.yml/badge.svg)](https://github.com/fabiojmjr-oss/estrutura-de-funis/actions/workflows/pages.yml)

Five funnels — marketing, sales, supply chain, strategy execution and, at the centre, the full
cycle from a captured idea to a scaled solution — on one funnel engine, with the synthetic data
to exercise all of it. A Python library, tested and typed, and an interactive web interface in
HTML, CSS and JavaScript that works on desktop and phone, offline, and from a shared link. Sister repository of
[`ferramentas-de-trabalho`](https://github.com/fabiojmjr-oss/ferramentas-de-trabalho), built to
the same rules.

**[Open the interactive page →](https://fabiojmjr-oss.github.io/estrutura-de-funis/)** · **[Leia em português →](README.pt-BR.md)**

---

## Why this exists

A funnel is a chain of ratios, and the arithmetic of a ratio is never where a funnel report goes
wrong. It goes wrong on conventions nobody writes down: whether a deal created at proposal passed
qualification, whether this month's customers are divided by this month's leads or by the leads
that produced them, whether a cohort that entered last week counts as having failed to convert.

This repository takes the same position as its sister: those conventions belong in code, as
arguments, with tests. Where a funnel metric has more than one legitimate definition, the
function returns all of them, because the gap between them is usually the finding.

The fifth funnel is the reason the repository exists. An idea pipeline takes its most expensive
decisions — which ideas get an MVP — on the least data of any funnel in a company. The
`ideation` module treats every gate as a measurement problem with a price on each kind of error,
and [`docs/ciclo-ideia-mvp.md`](docs/ciclo-ideia-mvp.md) turns that into a playbook with a
template for every gate.

## Modules

| Module | The question it answers | Docs |
| --- | --- | --- |
| `funilab.synth` | What data do I test against without exposing a real business? | [`DISCLAIMER.md`](DISCLAIMER.md) |
| `funilab.core` | What is the conversion rate, and how much of it is definition? | — |
| `funilab.marketing` | What does a customer cost, and which channel earned it? | — |
| `funilab.sales` | What will the open pipeline actually close? | — |
| `funilab.supply` | How much of the operation is doing work twice? | — |
| `funilab.management` | Where does announced benefit go, and why does the portfolio slow down? | — |
| `funilab.ideation` | Which ideas deserve an MVP, and how much evidence buys that decision? | [README](src/funilab/ideation/README.md) · [playbook](docs/ciclo-ideia-mvp.md) |

Build sequence and selection rule in [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Install

```bash
git clone https://github.com/fabiojmjr-oss/estrutura-de-funis.git
cd estrutura-de-funis
make install
make check
```

## Thirty seconds

```python
import pandas as pd
from funilab.core import conversion_sensitivity
from funilab.marketing import MARKETING
from funilab.synth import generate_marketing

data = generate_marketing()  # reproducible from the seed alone
print(
    conversion_sensitivity(  # one lead base, five conventions
        data.events,
        MARKETING,
        start=pd.Timestamp("2025-10-01"),
        end=pd.Timestamp("2025-12-31"),
        window=pd.Timedelta(days=120),
    )
)
```

---

## Ten things it demonstrates

### 1. The latest quarter's conversion halves, and nothing happened

The same lead base, measured five ways, for two quarters:

| Convention | Q3 (entered Jul–Sep) | Q4 (entered Oct–Dec) |
| --- | --- | --- |
| Period: stage entries counted by their own date | 2.33% | 2.46% |
| Cohort, whatever it reached by 31 Dec | 2.45% | **1.23%** |
| Cohort, converted within 120 days | 2.41% | 1.23% |
| Cohort, only leads whose 120 days had elapsed | **2.68%** | — (none) |

Q4's cohort reads half of Q3's. Nothing about the leads changed: a lead that entered in November
has not had the 30 to 60 days a sales cycle takes. **No Q4 cohort has matured, so the only
defensible statement about Q4's conversion today is "not yet known"** — and the period number,
which looks reassuringly stable, divides this quarter's customers by this quarter's leads, who
are different people. The matured Q3 cohort converts at 2.68%, a figure neither of the other
conventions reports for either quarter.

### 2. "Fix the worst stage" is true in points and false in percent

On the matured funnel (36.8% → 32.0% → 22.4%), a **10% relative lift is worth exactly +10% of
output at every stage**. A one-point lift is worth +4.47% of output at the last stage and +2.72%
at the first, because a point is a larger share of a smaller rate. Both statements are arithmetic;
neither says which lift is cheaper to buy, and that is the only thing that decides where the money
goes. `lever_table` returns both columns so the argument has to be about cost.

### 3. The cheapest channel becomes the most expensive by changing one convention

Media spend of BRL 2.03M bought 472 customers from paid channels. **Blended CAC reads 2,569 and
paid CAC 4,294** — blended looks 40% cheaper because it divides the same spend by 789 customers,
317 of whom came from referral and organic search that the spend did not buy.

Attribution then decides which paid channel wins:

| Channel | CAC, first touch | CAC, last touch | Rank first → last |
| --- | --- | --- | --- |
| Events | **3,161** | **9,238** | 1 → 3 |
| Paid search | 3,559 | 1,957 | 2 → 1 |
| Paid social | 8,189 | 4,649 | 3 → 2 |

Events opens journeys and paid search closes them. **The same spend and the same customers make
Events the cheapest channel or the most expensive, by a factor of 2.9**, and the budget decision
flips on a convention that is almost never on the slide.

### 4. A step rate of 109.5%

One opportunity in five is created directly at proposal — an inbound request for proposal. Counting
only the stages that were logged puts **1,842 deals at proposal against 1,682 at qualification, a
step rate of 109.5%**. Inferring that a deal at proposal passed qualification gives 75.4%. Any
stage-conversion target set on the logged data is set on an artefact.

The win rate has the same problem in a different form: **21.5% by count and 15.6% by value** on the
same closed deals, because large deals close less often. Quoting one without naming the basis is
how sales and finance report different win rates from one CRM.

### 5. Better odds do not fix the forecast. Removing dead deals does.

The synthetic pipeline carries each open deal's eventual outcome, so the forecast can be graded
instead of argued about. Open pipeline at 31 December: BRL 22.1M across 333 deals.

| Forecast | Expected won | Error against what was won |
| --- | --- | --- |
| CRM default probabilities (10/25/50/75%) | 7.97M | **+45.8%** |
| Historical stage win rates | 8.19M | **+49.9%** |
| Historical, stale deals at zero | 5.38M | **−1.5%** |

Replacing the CRM's round numbers with the pipeline's own history — the standard advice —
**makes the forecast slightly worse**. The error is not in the odds; it is in 83 deals carrying
BRL 7.8M that have sat in their stage longer than 85% of the deals ever won from it. They go on to
win 4.8% of the time, against 43.6% for the rest. Age in stage is the evidence, and it is already
in the CRM.

### 6. A final yield of 99.3% on an operation that touches one order in four twice

| Stage | First-pass yield | Final yield |
| --- | --- | --- |
| Credit | 92.9% | 99.8% |
| Picking | 95.0% | 99.9% |
| Checking | 96.5% | 99.9% |
| Dispatch | 97.5% | 99.9% |
| Delivery | 91.8% | 99.8% |
| **Chain** | **76.2% (RTY)** | **99.3%** |

The fulfilment funnel loses almost nothing, which is why its report is green. **Rolled throughput
yield is 76.2%: 23.5% of orders were handled twice somewhere**, and those repeat attempts are the
hidden factory the funnel cannot show because it only counts who arrived.

The perfect-order check came out against expectation and is reported as such: the product of the
four component rates (85.86%) and the measured joint rate (85.85%) agree to a hundredth of a point
here, because the shared driver moves each component only slightly. The independence assumption
is usually cited as the flaw in multiplying components; on this data it costs nothing, and
`perfect_order` returns both so that is measured rather than assumed either way.

### 7. More benefit delivered unmeasured than delivered measured

Following the initiatives proposed a full year before the horizon from announcement to income
statement:

| Bar | BRL M | Share of announced |
| --- | --- | --- |
| Announced | 134.4 | 100% |
| Not approved | −59.5 | −44.3% |
| Stopped before funding, start or delivery | −38.7 | −28.8% |
| **Delivered, benefit never measured** | **−14.6** | **−10.9%** |
| Still in flight | −2.9 | −2.1% |
| Under-delivered against plan | −4.4 | −3.2% |
| **Realised and measured** | **14.3** | **10.6%** |

The bridge reconciles exactly. The rejections at approval are the gate working. The line that is
not is the third from the bottom of the leakage: **BRL 14.6M of planned benefit was delivered and
never measured, more than the 14.3M that was** — the portfolio cannot say whether its largest single
outcome happened.

### 8. Every project is on schedule and the portfolio is getting slower

Little's law on execution: work in progress rose from 47.2 initiatives in the first half to 68.2 in
the second. **Lead time measured on what finished is 149 days; WIP divided by throughput implies
197.** The difference is the backlog still inside the system, which the measured figure cannot see
because it only counts what left. At the same throughput, halving WIP implies 98 days — starting
less is the cheapest way to finish sooner, and it needs no budget.

### 9. The triage score is the weakest evidence in the cycle, and it makes the biggest cut

RICE and ICE are scored at capture, before any evidence exists. Against the outcome they are meant
to anticipate:

| Score | Good ideas in its top 20% | Rank correlation with value |
| --- | --- | --- |
| RICE | 26.2% | 0.200 |
| ICE | 23.8% | 0.155 |
| *Base rate* | *17.4%* | — |

On the 628-idea portfolio used throughout findings 9 and 10, the better score lifts the share of
good ideas by nine points over picking at random. **Used to
cut 40% of the list, it removes 25 of the 109 good ideas before anyone has spoken to a customer**;
used to cut 70%, as the strictest policy below does, it removes 64. A score is a conversation aid.
Five customer interviews cost BRL 2,000 and are better evidence than any score.

The evidence itself needs reading: 2 of 5 interviewees confirming a pain is 40% against a 35% bar,
and a point reading passes it. The posterior probability that the true rate clears the bar is 0.58.

### 10. More rigour loses money; calibrated evidence makes the most

Five gate policies, each replicated 30 times on a portfolio of 628 ideas whose truth is known
(mean net value, and the 2.5–97.5% range of runs, BRL M):

| Policy | MVPs built | Good scaled | Bad scaled | Net value | Range |
| --- | --- | --- | --- | --- | --- |
| No gates (build everything) | 628 | 109 | 519 | **−124.6** | — |
| Intuition (gut score, small samples read at face value) | 85.8 | 50.4 | 4.7 | 19.8 | 13.3 – 25.6 |
| Evidence (RICE cut, larger samples, 80% posterior) | 77.5 | 58.5 | 0.2 | 24.3 | 16.7 – 31.2 |
| Maximum rigour (70% cut, large samples, 95%) | 41.1 | 31.7 | 0.0 | 16.6 | 10.9 – 19.6 |
| **Calibrated** (no score cut, 5 interviews, 60% with a second round) | **110.4** | **87.1** | 2.5 | **31.5** | **26.9 – 35.8** |

Three results. **Gates are where the money is**: without them the cycle loses BRL 124.6M, almost all
of it scaling 519 ideas that were never good. **Rigour is not a virtue in itself**: maximum rigour
scales no bad idea and still makes the least of any gated policy, because a missed good idea is
worth about twice what a scaled bad one costs, and a 95% bar with a 70% score cut is built to make
exactly that error. And **the calibrated policy builds the most MVPs and makes the most money** —
its worst run (26.9) is above intuition's best (25.6) — because it spends on cheap evidence for
every idea instead of on a score, and sets its confidence bar from the cost of each error rather
than from how rigorous it sounds.

The ranges above overlap between calibrated and evidence, and that overlap is mostly luck the two
policies share: which ideas happened to impress their interviewees. `paired_difference` runs both
on the same draws and measures the difference directly. **Calibrated beats evidence in 60 of 60
paired runs, by BRL 5.1M on average (2.5–97.5% range +0.55M to +9.92M).** The same test does *not*
separate evidence from intuition: the range crosses zero and evidence comes out ahead in 85% of
runs, so the README makes no claim that the textbook upgrade beats gut feel on this portfolio.

The calibrated policy was chosen by a grid search on the seed-42 portfolio. Every figure above is
from an **independent portfolio (seed 2026)**, so the search is not grading itself.

One defect was caught on the way and changed the design. With the uniform prior most Bayesian
tutorials default to, a smoke test with a 4% bar starts at 96% confidence that the idea clears it,
and **two visitors who both leave are enough to pass at 80%** (the posterior is 0.88). The default
prior here is neutral at the bar — exactly even odds before any evidence — and the test that
reproduces the defect stays in the suite.

---

## Examples

Seven runnable scripts, each printing the reasoning behind its figures rather than only the
figures. Every one of them is executed by the test suite.

| Script | The question it works through |
| --- | --- |
| [`01_conversion_definition.py`](examples/01_conversion_definition.py) | How much of a conversion rate is definition rather than performance |
| [`02_marketing_acquisition.py`](examples/02_marketing_acquisition.py) | What a customer costs, and which channel deserves the credit |
| [`03_sales_forecast.py`](examples/03_sales_forecast.py) | What the open pipeline will actually close, and why the CRM overstates it |
| [`04_supply_hidden_factory.py`](examples/04_supply_hidden_factory.py) | The fulfilment funnel's final yield, and the factory hidden behind it |
| [`05_strategy_execution.py`](examples/05_strategy_execution.py) | Where announced benefit goes, and why the portfolio keeps slowing down |
| [`06_idea_scoring.py`](examples/06_idea_scoring.py) | Whether the triage score predicts anything, and how much evidence a gate needs |
| [`07_idea_to_mvp.py`](examples/07_idea_to_mvp.py) | The full cycle from captured idea to scaled solution, under five gate policies |

## The web interface

`web/` is a static page — HTML, CSS and plain JavaScript modules, no framework and no build step —
that puts every funnel under the user's hands: move a slider, pick an attribution model, change a
gate policy, and the numbers are recomputed in the browser.

```bash
make web-data   # export the figures and portfolios from the Python library
make web        # serve on http://127.0.0.1:8000/
```

| Tab | What you can do |
| --- | --- |
| Visão geral | The five funnels and the finding each one hides |
| Construtor | Type or load any funnel: step rates with 95% intervals, levers, reverse funnel |
| Multicanal | Switch attribution model and scale each channel's spend: CAC and rank per channel |
| Vendas | Swap stage odds (CRM, history, your own), toggle stale deals, grade the forecast |
| Supply | Set first-pass yield per stage: RTY against final yield, rework per 100 orders |
| Gestão | The benefit bridge as a waterfall; Little's law with your WIP and throughput |
| Ideia → MVP | Build a gate policy and simulate it on the 628-idea portfolio; a gate calculator with the posterior curve and the sample a decision needs |

**One scenario, every channel.** The same page is built to travel:

| Channel | How |
| --- | --- |
| Desktop, tablet, phone | Responsive to 360 px with no sideways scroll; charts switch to a stacked layout on narrow screens |
| Shared link | Every control writes to the URL, so a link reopens the exact scenario — native share sheet on phones, WhatsApp, e-mail, LinkedIn and copy on desktop |
| Installed app, offline | A web app manifest and a service worker: installable, and usable offline after the first visit |
| Paper | Print or save as PDF, with the scenario's parameters and link printed above the results |
| Spreadsheet | CSV of the current tab (semicolon-separated with a BOM, so Excel in Portuguese opens it directly) |
| Accessibility | Keyboard-navigable tabs, visible focus, light and dark themes, reduced motion |

**Two engines, one answer.** The JavaScript engine re-implements the arithmetic so the page needs
no server — which is exactly how two implementations drift. `python -m funilab.export` therefore
also writes test vectors (`web/data/parity.json`), and the JavaScript suite asserts the Beta
distribution, the neutral prior, gate decisions, sample sizes, Wilson intervals and attribution
against Python's answers. The gate simulator uses a different random stream, so it is held to the
distribution instead: the no-gates policy must match Python exactly, and every gated policy's
mean must land inside the range Python reports. A Python test fails if the committed data is
stale.

## The idea-to-MVP cycle

The playbook in [`docs/ciclo-ideia-mvp.md`](docs/ciclo-ideia-mvp.md) (in Portuguese) runs the
seven stages end to end — capture, triage, problem, solution, MVP, validation, scale — with the
question each gate answers, the evidence it requires, the bar set in advance, and the function
that reads it. The [`templates/`](templates/) directory has a card for each: idea canvas,
interview script, experiment card, gate checklist and MVP scorecard.

---

## Design principles

**Every convention is an argument.** Skipped stages, cohort or period basis, maturity window,
attribution model, win-rate basis, prior. None has a silent default where the choice moves the
answer.

**Return every legitimate definition.** Five conversion conventions, four win rates, four
attribution models, first-pass beside final yield, product beside joint.

**Grade against the truth where synthetic data allows it.** The generator plays open deals and
ideas to their end and keeps the outcome aside, so forecasts and gate policies are scored against
what happened rather than against each other.

**Never report a stochastic point estimate as an answer.** Gate policies are replicated and carry
a range; a difference inside the range is not reported as a win.

**Compare policies on the same draws.** Two overlapping ranges do not mean two policies are
indistinguishable; the paired difference does the deciding.

**Tune on one sample, report on another.** The calibrated policy was selected on one portfolio and
every published figure comes from a second.

**Report the result that contradicts the pitch.** Better CRM odds made the forecast worse; the
perfect-order independence assumption cost nothing; maximum rigour made the least money. All
three are in the README because they came out that way.

**Reconcile exactly or fail.** The benefit bridge raises rather than draw a bar that misses.

**Test against hand calculations.** Every module is tested on fixtures small enough to compute on
paper; the Beta distribution is tested against closed forms, not against itself.

**No real data, ever.** See [`DISCLAIMER.md`](DISCLAIMER.md).

**The README is under test.** Every figure above is asserted in `tests/test_readme_claims.py`, and
the examples are executed there too.

## Limitations

- The synthetic data is **plausible**, not calibrated. No figure here is the performance of a real
  business, and the gate-policy ranking in particular depends on the cost of an MVP relative to
  the value of a good idea: change that ratio and the calibrated policy changes with it. The
  method transfers; the policy does not.
- Gates are binary with at most one extra round. Real pipelines pivot — an idea that fails the
  solution gate often returns with a different solution — and pivots are not modelled.
- Idea evidence is simulated as independent binomial draws. Real interviews are neither
  independent nor unbiased (leading questions, friendly customers), so real samples carry less
  information than the same number of simulated ones.
- Attribution is rule-based. There is no data-driven (Shapley or Markov) model yet, and none of the
  rule-based models is a causal estimate of a channel's effect.
- The sales forecast grades itself against eventual outcomes that only synthetic data provides.
  On real data the same comparison needs a backtest over closed quarters.
- Little's law is applied to one stage with a single class of work; initiatives of very different
  size share one WIP count.

## Development

```bash
make install     # editable install with the dev tools
make check       # lint, format, types and the fast suite - what gates a push
make check-all   # the above plus every documented figure re-derived
make claims      # re-derive every number quoted in a README
make js-install  # the web tooling (ESLint, Playwright)
make js-check    # JavaScript lint, engine and parity tests
make e2e         # the page in Chromium: desktop, phone, shared link, injection, preview, dark, print, offline
```

**117 tests, split by cost.** 94 of them run in a few seconds and gate every push; the rest
re-derive every figure quoted above, replicate the gate policies, execute every example and check
that the web data is current. The web interface adds **19 JavaScript tests** (engine and parity)
and **8 browser tests**, in their own CI job.
Statement coverage is reported by `make check` and is the one repository figure not under test.

## License

MIT. See [`LICENSE`](LICENSE).
