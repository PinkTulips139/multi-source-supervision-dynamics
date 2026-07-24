# Method Hypothesis

## Error Correlation

For a trusted anchor set, each generator can be represented by a binary error vector:

```text
e_i(x) = 1 if generator i fails on anchor sample x
       = 0 otherwise
```

The correlation between two generators can then be estimated from their error vectors. A high correlation means the generators tend to fail on the same anchor samples.

## Error Correlation Matrix R

Let `R` denote the generator error correlation matrix. Each entry `R_ij` describes the shared failure tendency between generator `i` and generator `j`.

Possible variants include:

- Pearson correlation over binary error vectors
- Jaccard similarity over error sets
- Common error rate
- Conditional co-failure probability

The exact estimator is not finalized.

## Source Weights w

Let `w` be the mixing weight vector over synthetic data sources. Each `w_i` represents the proportion of data sampled from generator `i`.

A preliminary objective is:

```text
min_w  w^T R w + lambda * CoverageLoss(w)

subject to:
  w_i >= 0
  sum_i w_i = 1
```

This is a preliminary formulation, not a final algorithm.

## Static and Dynamic Weighting

Static weighting would estimate `R` once and use a fixed source mixture. Dynamic weighting would update `R`, coverage estimates, or source weights across recursive generations.

## Difference From Ordinary Disagreement

Model disagreement measures whether generators predict different labels. Error correlation focuses on shared failures against trusted anchor labels. Two generators can disagree often but still share important failure regions, or agree often while being correct on most samples.

## Difference From Source Count

Source count assumes that more generators mean more diversity. Error correlation tests whether this diversity is effective or only nominal.

## Difference From Equal Mixing

Equal mixing gives every generator the same weight. Correlation-aware mixing aims to reduce over-reliance on sources with redundant errors while preserving coverage.

## Open Problems

- How large should the trusted anchor set be?
- Which error correlation estimator is most stable?
- How should coverage loss be defined?
- How should generator quality and correlation be balanced?
- How can the method avoid overfitting to the anchor set?