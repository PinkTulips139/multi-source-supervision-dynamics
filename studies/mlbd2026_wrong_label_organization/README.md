# MLBD2026 study: Wrong-label organization

[Home](../../README.md) · [Evidence routes](../../docs/EVIDENCE_ROUTES.md) · [Reproduction](../../docs/REPRODUCIBILITY.md)

*Wrong-Label Organization in Multi-Source Supervision: Controlled Effects and Optimization-Path Sensitivity* is a controlled single-generation empirical study. The study directory name identifies the project's manuscript track, not conference acceptance.

Question: with fixed inputs, truth, Source correctness, true-label target mass and Source × truth wrong-label marginals, can changing wrong-label identity/input assignment alter Student behavior?

Three hard-label Sources (BERT-base-uncased, RoBERTa-base, DeBERTa-v3-small) form equal-weight targets. Main comparisons use REAL/R1/R2 with RoBERTa-base and XLNet-base-cased on CLINC150 and BANKING77: 48 fits, four seeds. Separate concentration-matched CONTROL contrasts cover all four settings. The path extension uses 16 fresh CLINC150 × XLNet fits, REAL/CONTROL under two presentation orders.

![48 main fits and 16 fresh path fits; concentration controls are separate and all current evidence is single-generation](../../docs/assets/diagrams/experiment-matrix.svg)

## Results and reading order

1. [Table I](results/TABLE_1_DATA.csv): eight main rows with mean and ordered seed signs for Secondary, LocalNLL, Primary and Complement.
2. [Table II](results/CONTROL_TABLE_DATA.csv): concentration-matched contrasts; three settings with both local endpoints positive across all seeds, one non-unanimous setting.
3. [Table III](results/M3_RESULT_TABLE_DATA.csv) and [summaries](results/M3_SUMMARY_DATA.csv): all four absolute path arm values and differences of differences; no seed excluded.
4. [Evidence routes](../../docs/EVIDENCE_ROUTES.md): seed-level values, invariants, diagnostics and actual implementation snapshots.
5. [Limitations](../../docs/KNOWN_LIMITATIONS.md): small seed count, sequential design, mixed directions and unidentified mediator.

All contrasts use REAL minus comparator; positive NLL is worse under REAL. Frozen seed order: 167174636, 1852328752, 1231418446, 1461753708. LocalNLL path interaction `++++` coexists with Secondary `+-++`; the large seed response is retained.

## What is packaged

Frozen result CSVs; selected seed-level evidence and receipts; [configs](configs/README.md); [source/package hash manifest](manifests/evidence_manifest.json); [historical construction/training/validation code](scripts/reference/README.md); standalone Figure 1 source; historical table and figure generation code. This package does not modify manuscript text.

## What is not packaged

Raw dataset text, pretrained or trained weights, full logits and target tensors, complete split/order membership assets, all historical support modules, manuscript PDF/Overleaf and internal audit/chat material. Original contracts retain external dependency names for provenance. Clean training reproduction is not currently available from this checkout alone.

Current scientific conclusion: wrong-label organization can matter, consequences are setting-dependent, concentration-only sufficiency is weakened in three settings, and controlled path sensitivity is observed in one setting. Static diagnostics do not supply a unified mediator. Recursive propagation and mitigation are future work.
