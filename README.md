# Correlation-Aware Recursive Training

**Research in Progress**

This repository documents an ongoing research project. The hypotheses and proposed method have not yet been empirically validated.

## One-line Summary

This project studies whether error correlation among multiple synthetic data generators can help design more stable recursive training workflows.

## Project Status

Current status:

- Initial literature mapping has been completed.
- The research area has been organized into a preliminary map.
- Initial research questions and working hypotheses have been formulated.
- A preliminary experimental framework, baselines, and evaluation protocol have been drafted.
- Formal experiments have not yet been completed.
- The core hypotheses have not yet been validated.
- No paper-level empirical conclusion is claimed in this repository.

## Motivation

Recursive training with synthetic data can amplify errors, reduce coverage, and gradually distort the data distribution. Prior work often describes synthetic data workflows using the number of data sources, the number of generators, or the synthetic data ratio. However, nominal source diversity does not necessarily imply independent information.

Multiple generators may share the same base model, similar training data, similar capability boundaries, or similar failure modes. If they make correlated errors on the same regions of the data space, simply mixing them equally may not prevent long-term degradation.

## Core Research Question

Can generator error correlation provide a more informative signal than source count alone for designing stable recursive synthetic data mixing strategies?

## Preliminary Hypotheses

These are working hypotheses, not experimental conclusions:

1. Multiple generators do not necessarily provide more effective information than a single generator.
2. Error correlation among generators may predict recursive degradation better than generator count alone.
3. Under the same generator count and data budget, lower-correlated source combinations may lead to better long-term stability.
4. Dynamically adjusting source weights according to error correlation structure may outperform equal mixing and random mixing.

## Planned Framework

```text
Multiple Generators
-> Trusted Anchor-Set Evaluation
-> Error Correlation Matrix
-> Correlation-Aware Source Weighting
-> Recursive Retraining
-> Long-Term Stability Evaluation
```

A preliminary formulation is:

```text
min_w  w^T R w + lambda * CoverageLoss(w)

subject to:
  w_i >= 0
  sum_i w_i = 1
```

where `R` is a generator error correlation matrix and `w` is the vector of source mixing weights. This is a preliminary formulation, not a finalized algorithm.

## Current Progress Checklist

- [x] Initial literature mapping
- [x] Research problem formulation
- [x] Preliminary hypothesis design
- [x] Initial evaluation protocol
- [ ] Gaussian mixture simulation
- [ ] Multi-generator construction
- [ ] Correlation-aware mixing implementation
- [ ] Text classification experiments
- [ ] Ablation studies
- [ ] Final empirical conclusions

## Planned Experiments

1. Controlled Gaussian mixture simulation
   - Control generator count, generator error rate, generator error correlation, synthetic data ratio, long-tail coverage, recursive generations, and random seeds.
2. Real text classification experiments
   - Candidate datasets: IMDb, SST-2, and AG News.
   - Candidate generator construction methods: different architectures, data subsets, random seeds, checkpoints, prompts, or decoding strategies.

No formal experiment results are available yet.

## Evaluation Dimensions

Planned evaluation dimensions include accuracy, Macro-F1, cross-generation degradation slope, generator error correlation, common error rate, long-tail recall, semantic or class coverage, output entropy, distribution shift, error inheritance, error amplification, and computational/data cost.

## Repository Structure

```text
correlation-aware-recursive-training/
├── README.md
├── README_zh.md
├── AGENTS.md
├── .gitignore
├── requirements.txt
├── docs/
│   ├── research_overview.md
│   ├── literature_map.md
│   ├── research_questions.md
│   ├── method_hypothesis.md
│   ├── experimental_protocol.md
│   ├── evaluation_rubric.md
│   ├── roadmap.md
│   ├── progress_log.md
│   └── references.md
├── experiments/
│   ├── gaussian_mixture/
│   │   └── README.md
│   └── text_classification/
│       └── README.md
├── configs/
│   └── README.md
├── results/
│   └── README.md
└── notebooks/
    └── README.md
```

## Reproducibility Principles

Future experiments should fix random seeds, save configuration files, record software environments, preserve commands, and separate hypotheses from observed results.

## Limitations and Disclaimer

This repository is at the research planning and early design stage. It does not yet contain validated empirical findings, production-ready code, or final claims about model performance.

## Documentation

- [Research overview](docs/research_overview.md)
- [Literature map](docs/literature_map.md)
- [Research questions](docs/research_questions.md)
- [Method hypothesis](docs/method_hypothesis.md)
- [Experimental protocol](docs/experimental_protocol.md)
- [Evaluation rubric](docs/evaluation_rubric.md)
- [Roadmap](docs/roadmap.md)
- [Progress log](docs/progress_log.md)
- [References](docs/references.md)