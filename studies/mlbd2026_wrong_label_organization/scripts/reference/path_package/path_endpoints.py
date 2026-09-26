"""Future-only independent paired final endpoint extraction from saved logits."""
from pathlib import Path
import numpy as np

from consequence_runtime import SEEDS, load_bindings, validate_seed_assets
from consequence_validator import validate_fit, _support_core


KEYS = ("Primary", "Secondary", "LocalNLL", "Complement")


def _load(path, bindings):
    with np.load(path, allow_pickle=False) as a:
        if set(a.files) != {"logits", "truth_ids", "example_ids"}:
            raise ValueError("Prediction schema")
        logits = a["logits"].copy()
        if a["example_ids"].tolist() != bindings["test_ids"] or not np.array_equal(a["truth_ids"], bindings["test_truth"]):
            raise ValueError("Prediction ID/truth mismatch")
    if logits.dtype != np.float32 or logits.shape != (4500, 150) or not np.isfinite(logits).all():
        raise ValueError("Prediction logits")
    return logits


def _single(logits, bindings):
    z = logits.astype(np.float64)
    z -= z.max(axis=1, keepdims=True)
    lp = z - np.log(np.exp(z).sum(axis=1, keepdims=True))
    p = np.exp(lp)
    truth = bindings["test_truth"]
    local = bindings["frozen129_mask"]
    idx = np.flatnonzero(local)
    nll = -lp[np.arange(4500), truth]
    return dict(Primary=float(nll.mean()),
                Secondary=float(p[idx, bindings["shared_wrong"]].mean()),
                LocalNLL=float(nll[local].mean()),
                Complement=float(nll[~local].mean()))


def aggregate(project_root, package_root):
    root = Path(project_root)
    package = Path(package_root)
    bindings = load_bindings(package, root)
    support, _ = validate_seed_assets(package, root, "PI0")
    core = _support_core(support)
    namespace = root / "reports/research/submission_mlbd2026/MLBD2026_OPTIMIZATION_PATH_INTERACTION_EXECUTION_V1"
    rows = []
    max_error = 0.0
    for seed in SEEDS:
        by_order = {}
        for order_id in ("PI0", "PI1"):
            outputs = {}
            logits = {}
            for condition in ("REAL", "CONTROL"):
                fit = namespace / f"SEED_{seed}" / order_id / condition
                if validate_fit(fit, package, root, seed, order_id, condition)["status"] != "PASS":
                    raise ValueError("Per-fit validator")
                logits[condition] = _load(fit / "predictions/TEST.npz", bindings)
                outputs[condition] = _single(logits[condition], bindings)
            paired = core.endpoints(logits["REAL"], logits["CONTROL"],
                                    bindings["test_truth"], bindings["frozen129_mask"], bindings["shared_wrong"])
            for key in KEYS:
                difference = outputs["REAL"][key] - outputs["CONTROL"][key]
                error = abs(difference - paired[key])
                if error > 1e-12:
                    raise ValueError("Independent paired endpoint discrepancy")
                max_error = max(max_error, error)
            by_order[order_id] = dict(Y_REAL=outputs["REAL"], Y_CONTROL=outputs["CONTROL"], D=paired)
        for key in ("Secondary", "LocalNLL"):
            rows.append(dict(seed=seed, endpoint=key,
                             Y_REAL_PI0=by_order["PI0"]["Y_REAL"][key],
                             Y_CONTROL_PI0=by_order["PI0"]["Y_CONTROL"][key],
                             D_PI0=by_order["PI0"]["D"][key],
                             Y_REAL_PI1=by_order["PI1"]["Y_REAL"][key],
                             Y_CONTROL_PI1=by_order["PI1"]["Y_CONTROL"][key],
                             D_PI1=by_order["PI1"]["D"][key],
                             I=by_order["PI1"]["D"][key] - by_order["PI0"]["D"][key]))
    return dict(status="PASS", comparison="REAL_MINUS_CONTROL", interaction="D_PI1_MINUS_D_PI0",
                rows=rows, max_absolute_discrepancy=max_error, numerical_tolerance=1e-12,
                no_p_values=True, no_bootstrap=True)
