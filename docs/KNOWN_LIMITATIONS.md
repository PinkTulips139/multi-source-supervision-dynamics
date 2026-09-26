# Known limitations and claim boundaries

[Home](../README.md) · [Chronology](EXPERIMENTAL_CHRONOLOGY.md)

1. Current evidence is single-generation. Recursive propagation, collapse and mitigation remain future work. This is an empirical study, not a new algorithm.
2. The complete dataset × Student matrix was not preregistered from the outset. Later extensions followed earlier observed results, while their own protocols were frozen before their outcomes.
3. Four paired Student seeds provide limited precision. R1/R2 reuse REAL and do not constitute eight independent replications. Two realizations do not characterize a realization distribution.
4. Datasets differ jointly in label space, split, Source training/panel quality and local subset. The comparison does not isolate pure dataset or architecture causation. Matching numeric seeds across architectures does not match stochastic trajectories.
5. CLINC150 official test data were previously used for Source evaluation and formal Source selection. They were held out from Student training but were not project-wide untouched test data.
6. R1/R2 can change target concentration. CONTROL preserves concentration but changes a different set of rows and uses one realization per dataset. No retained-effect percentage, mediation fraction, smoothness-zero claim or unique identity mechanism follows.
7. CONTROL has positive contrasts across seeds for both local endpoints in three settings; CLINC150 × XLNet is non-unanimous. Four-setting measurement coverage is not four-setting confirmation.
8. Shared-wrong transfer can dissociate from true-label NLL; local degradation does not establish robust global degradation. Mixed signs do not prove absence of an effect or equivalence.
9. Tested static diagnostics are exploratory and provide no unified explanation. A technical validation PASS does not make a diagnostic scientifically supportive.
10. The path intervention is one fixed intervention in CLINC150 × XLNet. It does not isolate batch order, dropout, learning rate or Adam as mediator. LocalNLL interaction is positive in all four seeds, but magnitudes are heterogeneous; Secondary directions are mixed.
11. Seed 1852328752 strongly influences the path mean and Secondary direction. All four seeds and all absolute arm values are retained. Medians and leave-one-out summaries are post-hoc descriptive, not confirmatory exclusions.
12. No pooled significance claim, sample-level pseudo-replication, universal lower-correlation advantage, unique mechanism or validated mitigation is warranted.

Packaging limitation: original raw data, logits, weights, order files and the complete historical dependency graph are not bundled. Hash verification supports artifact identity, not independent regeneration of every scientific result. [Reproduction status](REPRODUCIBILITY.md).
