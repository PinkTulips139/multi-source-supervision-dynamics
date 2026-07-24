# Research Questions and Hypotheses

## Main Research Question

Can generator error correlation guide more stable synthetic data mixing for recursive training than source count or equal mixing alone?

## RQ1

Do multiple synthetic data generators necessarily provide more effective information than a single generator?

Supporting evidence would show that lower-correlated generator groups improve stability under the same data budget. Refuting evidence would show that generator count alone explains stability equally well or better.

## RQ2

Does generator error correlation predict cross-generation model degradation?

Supporting evidence would show a relationship between error correlation and degradation slope. Refuting evidence would show weak or inconsistent association after controlling for generator error rate and data budget.

## RQ3

Under the same generator count and synthetic data budget, do low-correlation source combinations preserve long-tail coverage better?

Supporting evidence would show better long-tail recall, lower tail loss, or better semantic coverage. Refuting evidence would show no difference or worse coverage.

## RQ4

Can correlation-aware source weighting improve stability compared with equal mixing and random mixing?

Supporting evidence would show lower degradation, better coverage, or better error stability under comparable cost. Refuting evidence would show that the weighting method adds no measurable benefit.

## RQ5

How should coverage loss be balanced against low error correlation?

Supporting evidence would show that adding coverage constraints prevents the method from over-selecting narrow but low-correlated sources. Refuting evidence would show that the coverage term is unnecessary or harmful.

## Working Hypotheses

- H1: Multiple generators do not necessarily provide more effective information than a single generator.
- H2: Error correlation among generators may predict recursive degradation better than generator count alone.
- H3: Lower-correlated source combinations may improve long-term stability under fixed data budgets.
- H4: Correlation-aware weighting may outperform equal mixing and random mixing.

All hypotheses are unvalidated at this stage.