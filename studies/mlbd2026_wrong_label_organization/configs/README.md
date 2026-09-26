# Frozen configs and identities

[Study](../README.md) · [Manifest](../manifests/evidence_manifest.json)

| File | Role |
| --- | --- |
| [SEED_ORDER](SEED_ORDER.json) | Ordered four-seed display and pairing authority |
| [CLINC_CONTRACT](CLINC_CONTRACT.json) | CLINC RoBERTa recipe and initial main comparison contract; machine-location fields redacted |
| [ENDPOINT_CONTRACT](ENDPOINT_CONTRACT.json) | CLINC fixed local subset and evaluation semantics; one external location redacted |
| [BANK_PACKAGE](BANK_PACKAGE.json) | 3,066 supervision rows, target identities and 304/3,080 local/test membership identities |
| [BANKING77 protocol](banking_protocol/FROZEN_BANKING77_PROTOCOL.json) | Split, Source identities, R1/R2 realization seed derivations and study design |
| [CLINC CONTROL construction](clinc_control/03_CONSTRUCTION_FREEZE.json) | Hash-derived single realization; whole-triple permutation |
| [BANK CONTROL construction](banking_control/CONSTRUCTION_PREFREEZE.json) | Independent dataset-specific construction freeze |
| [Path recipe](path_protocol/RUNTIME_AND_RECIPE_BINDING.json) | XLNet effective recipe, tokenizer/model revisions and runtime requirements |
| [Path order rule](path_protocol/PI1_ORDER_CONSTRUCTION_SPEC.json) | Reverse full minibatch blocks; hold partial batch last |
| [Path allowlist](path_runtime/SIXTEEN_FIT_ALLOWLIST.json) | Four seeds × REAL/CONTROL × PI0/PI1; all fresh |
| [Environment contract](path_runtime/ENVIRONMENT_CONTRACT.json) | Historical required package versions; not a universal install lock |
| [Installed receipt](path_runtime/INSTALLED_RUNTIME_RECEIPT.json) | Actual runtime build evidence, with machine-location fields redacted |
| [Cell binding](path_runtime/SIXTEEN_CELL_RUNTIME_BINDING.json) | Common runtime binding across the sixteen cells |

Keep freeze-time status fields unchanged: zero completed fits or authorization false in a prospective contract is historical state, not current completion state. [Execution completion](../evidence/PATH_EXECUTION_STATUS.json) is a distinct artifact.

Seeds for reorganization are distinct from Student seeds. BANKING77 R1/R2 seeds are stored as strings to preserve exact 64-bit integers. Never cast them through floating-point spreadsheet cells. The exact seed derivations remain in the protocols/constructors; do not replace them with the Student seed list.

No paths in these contracts authorize execution. `EXTERNAL_ASSET/...` denotes a redacted machine location, not a supplied file. The manifest records the original hash and each changed JSON selector. Raw input and epoch order files are not bundled.
