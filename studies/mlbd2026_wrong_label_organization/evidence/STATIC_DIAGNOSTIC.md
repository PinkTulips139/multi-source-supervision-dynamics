# Final mechanism diagnostic report

STAGE = PASS
TECHNICAL_PASS = YES
FOUR_SETTINGS_COMPLETED = 4/4
REPRESENTATION_ALIGNMENT = MIXED
SECONDARY_GRADIENT_ALIGNMENT = MIXED
LOCALNLL_GRADIENT_ALIGNMENT = MIXED
MECHANISM_SUPPORTED = PARTIAL_SETTING_SPECIFIC_ASSOCIATION_ONLY; NOT_A_UNIFIED_EXPLANATION
FALSIFICATION_CHECKS = PASS

Completed16 exact pristine seed-state reconstructions,32 seed/realization score groups and96 fixed metric comparisons. Each per-sample CSV has6,928 rows; no local sample excluded. There are no additional fits.

Zero Δq, target-swap sign reversal, direct loss-gradient difference versus separate two-arm gradient subtraction, explicit analytic softmax residual, order permutation, head-only parameter boundary and immutable weights all passed. Maximum gradient difference discrepancy=7.4267848815257054e-17; analytic/direct discrepancy=7.2749965773777348e-17, below frozen per-coordinate absolute+relative tolerance. Independent stdlib metric recomputation passed all96 comparisons, maximum discrepancy=1.1102230246251565e-16. All76 final setting artifact hashes passed post-run verification. Model and tokenizer identities and16/16 full/head gates passed.

## Scientific verdict (distinct from technical PASS)

The three diagnostic families are MIXED across their full frozen scope. BANKING77 representation alignment gives positive rho and positive Q4−Q1 in all16 relevant comparisons, but does not generalize consistently to CLINC150; strict sign agreement and sparse CLINC scores materially limit interpretation. Head-gradient alignment is heterogeneous and fails to supply a coherent explanation of CLINC150 XLNet versus BANKING77 XLNet LocalNLL. Technical PASS does not mean the proposed mechanism is established.

CLINC150_XLNET_MECHANISM_INTERPRETATION = no consistent explanatory alignment; output redistribution remains descriptive evidence.
BANKING77_MECHANISM_INTERPRETATION = limited pristine-representation association with shared-wrong transfer; gradient diagnostics mixed.
CROSS_SETTING_EXPLANATORY_POWER = PARTIAL_AND_INSUFFICIENT_FOR_KEY_LOCALNLL_DIFFERENCE.

The comprehensive per-setting table and Q1–Q5 answers are in07_CROSS_SETTING_MECHANISM_COMPARISON.md. No pooled correlation or inferential rescue is used. R1/R2 share REAL; repeated seed comparisons of identical A_repr are not independently learned representations. Two realizations do not estimate a realization distribution. The analysis is post-hoc exploratory; BANKING77 XLNet was an outcome-informed extension after RoBERTa, not a fully preregistered2×2.

## Limits and forbidden claims

These are first-order, head-level, pristine-representation/gradient diagnostics, not full Transformer causal mechanism proof. No architecture causal effect, representation-level mediator, unique/universal mechanism, or smoothness irrelevance is established. Full training includes evolving backbone representations, optimizer dynamics and long trajectories absent here. Frozen class-stratified A_repr has many zeros and tied quartiles; no sample deletion or metric replacement is permitted. Unsupported individual rows are retained.

## Next recommendation: B only

The central cross-setting difference remains unexplained. A separately authorized BANKING77 concentration-matched CONTROL feasibility/protocol review is worth considering to test whether its consequences persist at fixed per-example target concentration. That would close a specific within-BANKING77 smoothness alternative, not prove the gradient mechanism, and its feasibility must not be assumed. Failure of the present diagnostic is not evidence for concentration or authorization for outcome-driven rescue. No CONTROL design/construction/training is performed now; no additional experiment is mandatory by this report.

TRAINING = 0
OPTIMIZER_STEPS = 0
NEW_FITS = 0
GIT_WRITES = 0
GPU_COMPUTE = YES (authorized pristine forward/head autograd only)
SCIENTIFIC_RETRIES = 0
ENGINEERING_REMEDIATIONS = 2 (variable shadowing; adapter path routing, both preserved)
REMOTE_FREE_BYTES_AFTER = 28658462720

STOP_REASON = authorized diagnostic complete, results and failures preserved; awaiting human review. No next stage started. No automatic shutdown authorization is inferred from earlier unrelated stages.
