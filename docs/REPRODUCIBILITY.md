# Reproducibility

[Home](../README.md) · [Evidence routes](EVIDENCE_ROUTES.md)

## Supported now

Python 3.10+ and its standard library suffice for the public checks:

```bash
python scripts/verify_package.py
python scripts/show_frozen_table.py --table main
python scripts/show_frozen_table.py --table control
python scripts/show_frozen_table.py --table path
python -m unittest discover -s tests -v
```

The verifier checks SHA256, schemas, seeds, coverage, direct result-value bindings, local Markdown links, Python syntax, privacy patterns and file sizes. It does not import reference implementations, load models, deserialize scientific tensors, train, infer or overwrite results. The table command only displays existing CSV cells to stdout. These are validation and display entrypoints, not a simulation of successful scientific reproduction.

## Target construction

The [reference implementation map](../studies/mlbd2026_wrong_label_organization/scripts/reference/README.md) provides actual CLINC150 R1/R2 and BANKING77 R1/R2 constructors, frozen local-subset construction, concentration-matched CONTROL builders and invariant validators. Source snapshots retain original logic and historical relative paths.

Required original Source prediction arrays, target arrays, CLINC membership assets and the full historical layout are **not packaged**. Construction cannot be reproduced from this checkout alone. BANKING77 split authority and target hashes are described in [BANK_PACKAGE](../studies/mlbd2026_wrong_label_organization/configs/BANK_PACKAGE.json); seed derivations are preserved in [its protocol](../studies/mlbd2026_wrong_label_organization/configs/banking_protocol/FROZEN_BANKING77_PROTOCOL.json). No replacement synthetic targets were invented for this delivery.

The safe current first stage is `python scripts/verify_package.py`. A later construction adapter must accept separately acquired, hash-verified Source arrays and write to a fresh external directory, then run independent invariant checks. Such an adapter is not currently available; do not execute the historical builder in a canonical namespace.

## Student comparisons

Original model/data/checkpoint assets, pristine initialization tensors, complete support modules and epoch order arrays are unbundled. Historical training code is inspectable but **not a turnkey training route**. No new 48-fit or 16-fit batch launcher is supplied.

RoBERTa and XLNet have distinct recipes. Do not apply the CLINC150 RoBERTa 35-epoch/2,100-step recipe to XLNet. CLINC150 XLNet path uses 20 epochs, batch 32 with a final batch of 24, 1,880 steps and 188 warmup steps; all 16 cells are fresh. [Runtime/config map](../studies/mlbd2026_wrong_label_organization/configs/README.md).

The frozen environment contract and actual runtime receipt record Python/package/CUDA identities for the path experiment. They are historical evidence, not a tested universal installation lock. Clean environment installation and GPU reproduction were not performed during packaging. The old July `requirements.txt` was not silently repurposed as a current training environment.

## Tables and figures

Tables I, II and III map to `TABLE_1_DATA.csv`, `CONTROL_TABLE_DATA.csv`, and `M3_RESULT_TABLE_DATA.csv` plus `M3_SUMMARY_DATA.csv`. The public viewer displays their original values. The [historical table builder](../studies/mlbd2026_wrong_label_organization/scripts/reference/tables/build_freeze.py) is supplied for provenance; it depends on the original archive and is not run here.

The [standalone Figure 1 source](../studies/mlbd2026_wrong_label_organization/figures/figure1_source.tex) is a real, separately maintained figure file, not manuscript text. The [historical figure generator](../studies/mlbd2026_wrong_label_organization/scripts/reference/figures/generate_figures.py) records Figure 2 generation from frozen display summaries but also contains an older schematic Figure 1. It has top-level plotting actions: inspect, do not import. Its historical paths/toolchain are unbundled. Clean figure regeneration is not tested in this delivery.

The small SVGs on the homepage are repository navigation diagrams, not scientific result plots.

## What verification does not prove

Hash identity establishes that the package matches the selected source snapshot, including explicitly redacted locations. It does not prove experimental validity, independently regenerate logits, validate future claims, or close absent dependency bindings. No published reproduction badge or complete portability claim is made.
