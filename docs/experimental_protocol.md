# Experimental Protocol

This document describes planned experiments only. No formal experiments have been completed yet.

## Phase 1: Controlled Gaussian Mixture Experiment

The first phase uses a controllable Gaussian mixture setting to test whether the pipeline can detect and use error correlation.

Variables to control:

- Number of generators
- Single-generator error rate
- Generator error correlation
- Synthetic data ratio
- Head and long-tail proportions
- Number of recursive training generations
- Random seeds

Planned outputs:

- Per-generation performance
- Distribution coverage
- Tail recall
- Error correlation matrix
- Common error rate
- Degradation slope

## Phase 2: Real Text Classification Experiment

Candidate datasets:

- IMDb
- SST-2
- AG News

Candidate generator construction methods:

- Different model architectures
- Different training data subsets
- Different random seeds
- Different training checkpoints
- Different prompting or decoding strategies

Planned workflow:

1. Build or select multiple synthetic data generators.
2. Evaluate generator failures on a trusted anchor set.
3. Estimate the error correlation matrix.
4. Compare equal mixing, random mixing, and correlation-aware weighting.
5. Run recursive retraining across multiple generations.
6. Evaluate stability, coverage, and degradation.

## Baselines

Planned baselines:

- Single-generator synthetic data
- Equal multi-generator mixing
- Random source mixing
- Quality-only weighting
- Correlation-aware weighting

## Reproducibility Requirements

Every run should save:

- Dataset version
- Random seed
- Generator configuration
- Training configuration
- Mixing weights
- Output path
- Evaluation command
- Environment information

No result should be reported without a reproducible run record.