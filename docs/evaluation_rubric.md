# Evaluation Rubric

| Metric | What It Measures | Why It Is Needed | Possible Limitations |
|---|---|---|---|
| Accuracy / Macro-F1 | Overall predictive performance | Basic task-level utility | May hide long-tail degradation |
| Per-generation performance change | Performance at each recursive generation | Shows whether recursive training is stable | Sensitive to seed and data split |
| Cross-generation degradation slope | Rate of performance decline across generations | Summarizes long-term stability | Linear slope may oversimplify nonlinear collapse |
| Generator error correlation | Shared failure structure among generators | Core variable in this project | Depends on anchor-set quality and size |
| Common error rate | Fraction of samples failed by multiple generators | Captures redundant mistakes | Does not capture semantic severity |
| Long-tail Recall | Performance on rare or tail regions | Model collapse often affects tails | Requires reliable tail definition |
| Class or semantic cluster coverage | Coverage of label or semantic regions | Prevents low-correlation but narrow-source selection | Clustering may be noisy |
| Output entropy | Confidence or uncertainty of predictions | May detect distribution drift or uncertainty | Calibration may be poor |
| Distribution shift | Difference between real and synthetic or across generations | Measures recursive distribution drift | Metric choice matters |
| Error inheritance and amplification | Whether errors persist or grow across generations | Directly measures recursive failure propagation | Needs careful sample tracking |
| Computational and data cost | Training, inference, and data generation cost | Needed for practical system design | Cost differs by hardware and implementation |

## Reporting Rule

Metrics should be reported with seeds, configurations, and limitations. No metric should be used to claim final superiority before experiments are complete.