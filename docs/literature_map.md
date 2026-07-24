# Literature Map

This file separates paper-level claims from project-level interpretations. Details marked `TODO: verify` should be checked against the original paper before formal citation.

| Paper | Research Problem | Data Workflow | Main Method | Main Conclusion | Limitations | Relation to This Project |
|---|---|---|---|---|---|---|
| AI Models Collapse When Trained on Recursively Generated Data | How recursive training on generated data can affect model distributions | Recursive use of generated data | TODO: verify exact setup | Recursive generated-data training can lose distribution tails and low-probability modes | TODO: verify scope and model settings | Provides the model collapse phenomenon that motivates stable recursive training |
| Collapse or Thrive: Perils and Promises of Synthetic Data in a Self-Generating World | How different synthetic data workflows affect degradation or stability | Compares workflows such as full replacement, historical accumulation, and fixed-budget sampling | TODO: verify exact experiments | Data workflow strongly affects whether recursive training collapses or remains useful | TODO: verify datasets and assumptions | Motivates studying data mixing strategy, not only data quantity |
| Beyond Model Collapse: Scaling Up with Synthesized Data Requires Verification | Whether scaling synthetic data requires verification | Synthetic data generation with verification | Verification-based filtering | More synthetic data does not replace reliable verification | TODO: verify exact verifier design | Supports the need for trusted anchor-set evaluation |
| Escaping Model Collapse via Synthetic Data Verification: Near-term Improvements and Long-term Convergence | Long-term effect of repeated verifier-filtered synthetic data | Multi-round synthetic data with verifier use | Repeated verification workflow | Fixed verification may inject verifier knowledge and bias over time | TODO: verify formal conclusions | Suggests that verification itself has bias, motivating generator failure analysis |

## Notes

- Literature-supported findings should be cited carefully.
- Project interpretations should be labeled as inferences.
- Working hypotheses should not be presented as established results.