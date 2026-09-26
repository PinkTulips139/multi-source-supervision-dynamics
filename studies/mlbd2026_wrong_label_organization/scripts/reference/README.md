# Historical implementation snapshots

[Study](../../README.md) · [Reproduction limits](../../../../docs/REPRODUCIBILITY.md) · [Manifest](../../manifests/evidence_manifest.json)

These are actual project files, copied byte-for-byte from their recorded source locations. They are for inspection, **not standalone entrypoints**. Their parent-directory assumptions, relative historical references and missing external assets remain unchanged to preserve provenance. Some builders write outputs and the figure generator executes plotting at import time. The public verifier parses Python syntax without importing these files.

| Folder | Inspect for |
| --- | --- |
| [clinc_r1](clinc_r1/run_manipulation_preflight_resume.py) | Original CLINC R1 construction and preservation logic |
| [clinc_r2](clinc_r2/generate_validate.py) | Independent fixed R2 realization and validation |
| [banking_subset](banking_subset/construct_and_audit.py) | Source-defined frozen local membership |
| [banking_targets](banking_targets/construct_targets.py) | R1/R2 PCG64 seed rules, aggregation and invariants |
| [clinc_control](clinc_control/build_freeze.py) | Truth/correctness/vote-partition strata and cyclic whole-triple assignment |
| [banking_control](banking_control/build_control_once.py) | BANKING77 matched-control construction |
| [path_package](path_package/consequence_worker.py) | Remediated path runtime worker, validators and endpoint extraction |
| [tables](tables/build_freeze.py) | Actual table/claim freeze generator; archive-dependent |
| [figures](figures/generate_figures.py) | Actual historical figure generation; includes an older schematic |

The path package comes from the later runtime-binding remediation, not the superseded initial preflight package. It still depends on historical support code and hash-bound data/model/order assets outside this public subset. Import-time or CLI success is not claimed.

A portable rewrite needs an explicit dependency mapping and invariant-preserving verification before any training authorization. No artificial smoke results, replacement dataset or newly trained checkpoint is provided here.
