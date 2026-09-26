# Third-party notices

[Rights notice](RIGHTS_NOTICE.md) · [Reproduction](docs/REPRODUCIBILITY.md)

Upstream sources checked on 2026-09-26. This table reports upstream terms and model-card metadata, not a new license grant. No dataset text, pretrained weights or library source is vendored in this package. The research's exact model revisions are recorded in its frozen contracts.

| Component | Upstream rights source | Citation / scope |
| --- | --- | --- |
| CLINC150 | [CLINC license](https://github.com/clinc/oos-eval/blob/master/LICENSE): CC BY 3.0 | Larson et al., *An Evaluation Dataset for Intent Classification and Out-of-Scope Prediction*, EMNLP-IJCNLP 2019; [official dataset and citation](https://github.com/clinc/oos-eval) |
| BANKING77 | [PolyAI dataset license](https://github.com/PolyAI-LDN/task-specific-datasets/blob/master/LICENSE): CC BY 4.0 | Casanueva et al., *Efficient Intent Detection with Dual Sentence Encoders*; use [upstream citation](https://github.com/PolyAI-LDN/task-specific-datasets) |
| BERT-base-uncased | [Model card](https://huggingface.co/google-bert/bert-base-uncased): Apache-2.0 metadata | Obtain weights and citation from upstream; not bundled |
| RoBERTa-base | [Model card](https://huggingface.co/FacebookAI/roberta-base): MIT metadata | Upstream model grant does not license this repository |
| DeBERTa-v3-small | [Model card](https://huggingface.co/microsoft/deberta-v3-small): MIT metadata | Observe model-specific terms and citations |
| XLNet-base-cased | [Model card](https://huggingface.co/xlnet/xlnet-base-cased): MIT metadata | Use the frozen research revision, not an unpinned replacement |
| Transformers | [Upstream license](https://github.com/huggingface/transformers/blob/main/LICENSE): Apache-2.0 | Dependency only |
| PyTorch | [Upstream license](https://github.com/pytorch/pytorch/blob/main/LICENSE): BSD-style terms and component notices | Check the exact distribution's bundled notices |
| NumPy | [Upstream license](https://github.com/numpy/numpy/blob/main/LICENSE.txt): BSD-3-Clause | Bundled dependencies may carry additional terms |
| Matplotlib | [Upstream license](https://matplotlib.org/stable/project/license.html) | Used by historical figure code; not required by public read-only checks |
| SentencePiece, Tokenizers, Safetensors and CUDA components | See the [frozen environment](studies/mlbd2026_wrong_label_organization/configs/path_runtime/ENVIRONMENT_CONTRACT.json) | Exact distribution/component terms are not fully reviewed here; human confirmation is required before redistributing binaries |

No upstream bibliography is rewritten into a guessed project citation. Dataset/model citation instructions remain available at their official sources. Downloading exact assets for future reproduction and redistributing those assets are separate decisions.
