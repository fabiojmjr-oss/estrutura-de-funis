"""The idea-to-solution cycle's stage order.

Seven stages and six gates. Each gate asks one question and names the evidence that answers it;
the playbook in ``docs/ciclo-ideia-mvp.md`` describes them in full.

==========================  ===============================================================
Stage reached               The question the gate before it answered
==========================  ===============================================================
Captada                     (entry) Is it written down in a form someone else can judge?
Triada                      Is it worth an hour? (score, strategic fit)
Problema validado           Does the problem exist, for whom, and does it hurt? (interviews)
Solução validada            Will they act on the proposed solution? (smoke test)
MVP construído              Is the smallest build that tests value affordable? (build)
MVP validado                Do the people who use it keep using it? (retention / PMF survey)
Escalada                    Does the unit economics survive scale? (investment decision)
==========================  ===============================================================
"""

from __future__ import annotations

from ..core import Funnel

IDEA_TO_SOLUTION = Funnel(
    "ideation",
    (
        "Captada",
        "Triada",
        "Problema validado",
        "Solução validada",
        "MVP construído",
        "MVP validado",
        "Escalada",
    ),
)
