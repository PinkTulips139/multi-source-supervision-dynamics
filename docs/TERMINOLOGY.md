# Terminology and endpoints

[Home](../README.md) · [Evidence routes](EVIDENCE_ROUTES.md)

| Term | Meaning |
| --- | --- |
| Source | One of three fixed hard-label classifiers within a dataset setting |
| Student | Learner receiving input text and aggregate soft targets |
| REAL | Targets from original Source predictions; not ground-truth supervision |
| R1 / R2 | Two fixed wrong-label reorganization realizations, not Student seeds or algorithms |
| CONTROL | Whole ordered triples permuted within truth/correctness/vote-partition strata |
| Local subset L | Official-test examples where at least two original REAL Sources share the same wrong label |
| Shared-wrong label w | Repeated erroneous label defining L; unique with three Sources |
| Primary | Mean true-label negative log probability over the entire official test set T |
| Secondary | Mean Student probability of w over L |
| LocalNLL | Mean true-label negative log probability over L |
| Complement | Mean true-label negative log probability over T minus L |

The frozen local subset is Source-defined before the relevant Student outcomes. It is not selected again for R1, R2 or CONTROL. CLINC150 has |T|=4,500 and |L|=129; BANKING77 has |T|=3,080 and |L|=304.

For class k and training row i, raw q(i,k) is the fraction of the three Source labels equal to k. Training uses `0.9*q + 0.1/K`. This is aggregated hard-label supervision, not averaging native Source probabilities.

NLL uses natural logarithms (nats); Secondary uses unscaled probability. Ordinary contrasts are REAL minus comparator: positive NLL means worse true-label scoring under REAL; positive Secondary means more probability on the specific shared-wrong label. Probability and NLL magnitudes are not directly comparable.

`Primary = (|L|/|T|)*LocalNLL + (1-|L|/|T|)*Complement` holds for absolute values and paired contrasts over the same fixed partition. Secondary is not part of this decomposition.

Path experiment: `D(pi)=Y_REAL,pi - Y_CONTROL,pi`, `I=D(pi1)-D(pi0)`. Pi1 reverses the order of full minibatch blocks within each epoch, keeping within-batch order and the final partial batch unchanged. This jointly intervenes on presentation, sample-to-learning-rate-step and sample-to-RNG association and resulting parameter/optimizer trajectories.

The [frozen contracts](../studies/mlbd2026_wrong_label_organization/configs/README.md) retain original terminology such as `DIRECTION_SCRAMBLED`, `SCRAMBLED_R1` and `SCRAMBLED_R2`; public prose uses R1/R2 without changing artifact identities.
