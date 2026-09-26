# Evidence routes

[Home](../README.md) · [Study](../studies/mlbd2026_wrong_label_organization/README.md)

Every imported artifact has a source-relative locator, original SHA256 and packaged SHA256 in the [manifest](../studies/mlbd2026_wrong_label_organization/manifests/evidence_manifest.json). Historical identifiers below resolve to packaged files, not external working directories.

## Result tables

| Question | Display artifact | Underlying evidence |
| --- | --- | --- |
| Main eight comparison rows | [Table I](../studies/mlbd2026_wrong_label_organization/results/TABLE_1_DATA.csv) | [MAIN_MATRIX](../studies/mlbd2026_wrong_label_organization/evidence/MAIN_MATRIX.csv), [MAIN_SEEDS](../studies/mlbd2026_wrong_label_organization/evidence/MAIN_SEEDS.csv) |
| Four control settings | [Table II](../studies/mlbd2026_wrong_label_organization/results/CONTROL_TABLE_DATA.csv) | [CLINC RoBERTa](../studies/mlbd2026_wrong_label_organization/evidence/CROB_VALUES.csv), [CLINC XLNet](../studies/mlbd2026_wrong_label_organization/evidence/CXL_VALUES.csv), [BANKING77](../studies/mlbd2026_wrong_label_organization/evidence/BANK_CONTROL_VALUES.csv) |
| Absolute path arm values and interactions | [Table III](../studies/mlbd2026_wrong_label_organization/results/M3_RESULT_TABLE_DATA.csv), [summary](../studies/mlbd2026_wrong_label_organization/results/M3_SUMMARY_DATA.csv) | [M3_TABLE](../studies/mlbd2026_wrong_label_organization/evidence/M3_TABLE.csv), [execution matrix](../studies/mlbd2026_wrong_label_organization/evidence/M3_MATRIX.json), [completion](../studies/mlbd2026_wrong_label_organization/evidence/PATH_EXECUTION_STATUS.json), [historical recomputation receipt](../studies/mlbd2026_wrong_label_organization/evidence/M3_RECOMPUTE.json) |
| Numeric seed ordering | [SEED_ORDER](../studies/mlbd2026_wrong_label_organization/configs/SEED_ORDER.json) | [CLINC contract](../studies/mlbd2026_wrong_label_organization/configs/CLINC_CONTRACT.json), [BANK package](../studies/mlbd2026_wrong_label_organization/configs/BANK_PACKAGE.json), [path allowlist](../studies/mlbd2026_wrong_label_organization/configs/path_runtime/SIXTEEN_FIT_ALLOWLIST.json) |

Table generation source is the [historical freeze builder](../studies/mlbd2026_wrong_label_organization/scripts/reference/tables/build_freeze.py). `scripts/show_frozen_table.py` only displays the already generated CSV; it does not regenerate scientific means.

## Construction and invariants

| Component | Evidence / implementation |
| --- | --- |
| CLINC R1 fixed correctness and marginals | [preservation receipt](../studies/mlbd2026_wrong_label_organization/evidence/CLINC_PRESERVATION.json), [original constructor](../studies/mlbd2026_wrong_label_organization/scripts/reference/clinc_r1/run_manipulation_preflight_resume.py) |
| CLINC R2 fixed realization | [generator and validator](../studies/mlbd2026_wrong_label_organization/scripts/reference/clinc_r2/generate_validate.py) |
| BANK R1/R2 | [constructor/invariant checks](../studies/mlbd2026_wrong_label_organization/scripts/reference/banking_targets/construct_targets.py), [R1 receipt](../studies/mlbd2026_wrong_label_organization/evidence/BANK_R1_GATE.json), [R2 receipt](../studies/mlbd2026_wrong_label_organization/evidence/BANK_R2_GATE.json) |
| Frozen test-side membership | [BANK construction](../studies/mlbd2026_wrong_label_organization/scripts/reference/banking_subset/construct_and_audit.py), [BANK_LOCAL](../studies/mlbd2026_wrong_label_organization/evidence/BANK_LOCAL.json), [CLINC endpoint contract](../studies/mlbd2026_wrong_label_organization/configs/ENDPOINT_CONTRACT.json) |
| CLINC CONTROL | [construction](../studies/mlbd2026_wrong_label_organization/scripts/reference/clinc_control/build_freeze.py), [independent validator](../studies/mlbd2026_wrong_label_organization/scripts/reference/clinc_control/validate_control.py), [seed/construction freeze](../studies/mlbd2026_wrong_label_organization/configs/clinc_control/03_CONSTRUCTION_FREEZE.json) |
| BANK CONTROL | [construction](../studies/mlbd2026_wrong_label_organization/scripts/reference/banking_control/build_control_once.py), [independent validator](../studies/mlbd2026_wrong_label_organization/scripts/reference/banking_control/independent_validate.py), [invariants](../studies/mlbd2026_wrong_label_organization/configs/banking_control/02_CONTROL_INVARIANTS.json) |
| Path intervention | [order specification](../studies/mlbd2026_wrong_label_organization/configs/path_protocol/PI1_ORDER_CONSTRUCTION_SPEC.json), [order manifest](../studies/mlbd2026_wrong_label_organization/configs/path_protocol/PI1_ORDER_MANIFEST.json), [runtime code](../studies/mlbd2026_wrong_label_organization/scripts/reference/path_package/consequence_runtime.py) |
| Evaluation endpoints | [definitions](TERMINOLOGY.md), [saved-logit endpoint implementation](../studies/mlbd2026_wrong_label_organization/scripts/reference/path_package/path_endpoints.py) |

An invariant receipt is evidence of a prior validation. Running the public verifier does not repeat tensor-level validation without the original arrays. Input manifests record identities, but raw datasets and the full row/order assets are not bundled.

## Mechanism diagnostics

Output decomposition: [DECOMP_VALUES](../studies/mlbd2026_wrong_label_organization/evidence/DECOMP_VALUES.csv) → [frozen Figure 2 display data](../studies/mlbd2026_wrong_label_organization/results/FIGURE_B_OUTPUT_DATA.csv). Representation/gradient diagnostics: [STATIC_DIAGNOSTIC](../studies/mlbd2026_wrong_label_organization/evidence/STATIC_DIAGNOSTIC.md). Transfer proxy: [PROXY_FINAL](../studies/mlbd2026_wrong_label_organization/evidence/PROXY_FINAL.md). These reports retain historical language and locations; none identifies a universal mediator.

The [claim boundary matrix](../studies/mlbd2026_wrong_label_organization/evidence/SYN_CLAIM_BOUNDARY_MATRIX.csv) and [descriptive sensitivity artifact](../studies/mlbd2026_wrong_label_organization/evidence/SYN_DESCRIPTIVE_SENSITIVITY_SUMMARY.csv) retain counterexamples and extreme-seed influence. Leave-one-out summaries are post-hoc descriptive; all four seeds remain in primary results.
