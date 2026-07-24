# Roadmap

## Phase 0: Repository and Research Material Organization

- Initialize repository structure.
- Create README files and research documentation.
- Record progress and reproducibility rules.

Status: in progress.

## Phase 1: Gaussian Mixture Minimum Viable Experiment

- Implement controllable synthetic generators.
- Control generator error rate and error correlation.
- Simulate recursive training over multiple generations.

Status: planned.

## Phase 2: Error Correlation Estimation

- Define anchor-set evaluation protocol.
- Compare binary error correlation, Jaccard co-failure, and common error rate.
- Test estimator stability under different anchor sizes.

Status: planned.

## Phase 3: Correlation-Aware Mixing Method

- Implement equal mixing, random mixing, quality-only weighting, and correlation-aware weighting.
- Add coverage-aware regularization.
- Compare static and dynamic weighting.

Status: planned.

## Phase 4: Text Task Validation

- Select one or more text classification datasets.
- Construct multiple generators.
- Evaluate recursive training stability.

Status: planned.

## Phase 5: Ablation and Robustness Analysis

- Vary generator count, error correlation, data budget, and seed.
- Analyze long-tail performance and distribution drift.

Status: planned.

## Phase 6: Paper Writing and Reproducibility Packaging

- Write final method and experimental sections.
- Package configs, commands, and result tables.
- Prepare limitations and future work.

Status: planned.