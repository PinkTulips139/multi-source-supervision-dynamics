from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value: object) -> None:
    temp = path.with_suffix(path.suffix + ".partial")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def pair_metrics(truth: np.ndarray, a: np.ndarray, b: np.ndarray) -> tuple[int, int, float | None]:
    both = (a != truth) & (b != truth)
    count = int(both.sum())
    same = int(((a == b) & both).sum())
    return count, same, None if count == 0 else same / count


def target_descriptors(target: np.ndarray, pred: np.ndarray) -> dict:
    entropy = -np.where(target > 0, target * np.log(np.where(target > 0, target, 1.0)), 0.0).sum(axis=1)
    unique = np.array([len(set(row.tolist())) for row in pred])
    return {"mean_target_entropy": float(entropy.mean()), "unanimous_proportion": float((unique == 1).mean()), "two_vs_one_proportion": float((unique == 2).mean()), "three_way_disagreement_proportion": float((unique == 3).mean())}


def main() -> int:
    status = json.loads((HERE / "STAGE_STATUS.json").read_text(encoding="utf-8"))
    spec = json.loads((HERE / "MANIPULATION_PREFLIGHT_SPEC.json").read_text(encoding="utf-8"))
    metrics = json.loads((HERE / "MANIPULATION_METRICS.json").read_text(encoding="utf-8"))
    preservation = json.loads((HERE / "PRESERVATION_VALIDATION.json").read_text(encoding="utf-8"))
    alignment = json.loads((HERE / "CHATGPT_CODEX_ALIGNMENT_PACKET.json").read_text(encoding="utf-8"))
    real = np.load(HERE / "supervision/CONDITION_REAL_SUPERVISION.npz")
    scrambled = np.load(HERE / "supervision/CONDITION_DIRECTION_SCRAMBLED_SUPERVISION.npz")
    truth = real["truth_ids"]
    rp = real["source_predictions"]
    sp = scrambled["source_predictions"]
    rt = real["targets"]
    st = scrambled["targets"]
    checks = {
        "stage_complete": status["status"] == "REAL_CLINC150_STUDENT_CONSEQUENCE_MANIPULATION_PREFLIGHT_COMPLETE",
        "return_code_zero": status["return_code"] == 0,
        "manifest_success": status["manifest"] == "SUCCESS",
        "source_inference_count_three": status["source_dev_inference_count"] == 3,
        "source_training_zero": status["source_training_count"] == 0,
        "student_training_zero": status["student_training_count"] == 0,
        "shape_real_predictions": rp.shape == (3000, 3),
        "shape_scrambled_predictions": sp.shape == (3000, 3),
        "shape_real_targets": rt.shape == (3000, 150),
        "shape_scrambled_targets": st.shape == (3000, 150),
        "truth_range": bool(((truth >= 0) & (truth < 150)).all()),
        "prediction_ranges": bool(((rp >= 0) & (rp < 150)).all() and ((sp >= 0) & (sp < 150)).all()),
        "target_rows_sum_one": bool(np.allclose(rt.sum(1), 1.0, atol=1e-7) and np.allclose(st.sum(1), 1.0, atol=1e-7)),
        "source_weights_equal": bool(np.array_equal(real["source_weights"], scrambled["source_weights"]) and np.allclose(real["source_weights"], [1 / 3] * 3)),
        "example_ids_equal_unique": bool(np.array_equal(real["example_ids"], scrambled["example_ids"]) and len(set(real["example_ids"].tolist())) == 3000),
        "truth_equal": bool(np.array_equal(truth, scrambled["truth_ids"])),
        "preservation_validator_pass": preservation["validator"] == "PASS",
        "marginal_quality_preserved": preservation["marginal_quality_preserved"] is True,
        "per_example_error_identity_preserved": preservation["per_example_error_identity_preserved"] is True,
        "per_intent_confusion_marginals_preserved": preservation["per_intent_confusion_marginals_preserved"] is True,
        "alignment_outcome_matches": alignment["manipulation_gate_outcome"] == metrics["manipulation_gate_outcome"],
        "student_consequence_unverified": alignment["student_consequence_real_data_verified"] is False,
        "no_execution_authorization": alignment["current_execution_authorization"] == "NONE_FOR_NEW_RESEARCH_EXECUTION",
        "report_exists": (HERE / "REAL_CLINC150_MINIMAL_STUDENT_CONSEQUENCE_MANIPULATION_PREFLIGHT_V1_RESUME_EXECUTION_20260907.md").is_file(),
        "canonical_csv_exists": (HERE / "CANONICAL_DEV_REAL_AND_SCRAMBLED_PREDICTIONS.csv.gz").is_file(),
    }
    for source_index, source in enumerate(("bert", "roberta", "deberta")):
        checks[f"{source}_correct_wrong_vector"] = bool(np.array_equal(rp[:, source_index] == truth, sp[:, source_index] == truth))
        for truth_id in range(150):
            mask = truth == truth_id
            real_wrong = sorted(rp[mask, source_index][rp[mask, source_index] != truth_id].tolist())
            scrambled_wrong = sorted(sp[mask, source_index][sp[mask, source_index] != truth_id].tolist())
            if real_wrong != scrambled_wrong:
                checks[f"{source}_per_intent_multiset"] = False
                break
        else:
            checks[f"{source}_per_intent_multiset"] = True
    for a, b, key in ((0, 1, "bert_roberta"), (0, 2, "bert_deberta"), (1, 2, "roberta_deberta")):
        rb, rs, rf = pair_metrics(truth, rp[:, a], rp[:, b])
        sb, ss, sf = pair_metrics(truth, sp[:, a], sp[:, b])
        recorded = metrics["pairwise"][key]
        checks[f"{key}_both_wrong_preserved"] = rb == sb == recorded["real"]["both_wrong_count"] == recorded["scrambled"]["both_wrong_count"]
        checks[f"{key}_same_fraction_recomputed"] = abs(rf - recorded["real"]["same_wrong_label_fraction"]) < 1e-15 and abs(sf - recorded["scrambled"]["same_wrong_label_fraction"]) < 1e-15
    real_desc = target_descriptors(rt, rp)
    scrambled_desc = target_descriptors(st, sp)
    checks["real_target_descriptors_recomputed"] = all(abs(real_desc[k] - metrics["real_target_metrics"][k]) < 1e-12 for k in real_desc)
    checks["scrambled_target_descriptors_recomputed"] = all(abs(scrambled_desc[k] - metrics["scrambled_target_metrics"][k]) < 1e-12 for k in scrambled_desc)
    recomputed_l1 = float(np.abs(rt - st).sum(axis=1).mean())
    recomputed_changed = float(np.any(rt != st, axis=1).mean())
    checks["mean_target_l1_difference_recomputed"] = abs(recomputed_l1 - metrics["mean_target_l1_difference"]) < 1e-12
    checks["target_changed_example_proportion_recomputed"] = abs(recomputed_changed - metrics["target_changed_example_proportion"]) < 1e-12
    for source in ("bert", "roberta", "deberta"):
        source_status = json.loads((HERE / f"source_{source}/RUN_STATUS.json").read_text(encoding="utf-8"))
        source_validation = json.loads((HERE / f"source_{source}/VALIDATION_REPORT.json").read_text(encoding="utf-8"))
        checks[f"{source}_source_status_success"] = source_status["status"] == "SUCCESS" and source_status["return_code"] == 0
        checks[f"{source}_source_validator_pass"] = source_validation["validator"] == "PASS" and all(source_validation["checks"].values())
    checks["legal_outcome"] = metrics["manipulation_gate_outcome"] in {"STUDENT_CONSEQUENCE_MANIPULATION_READY", "INSUFFICIENT_DIRECTIONAL_CONTRAST"}
    validator = "PASS" if all(checks.values()) else "FAIL"
    report = {"validator": validator, "checks_passed": sum(checks.values()), "checks_total": len(checks), "checks": checks, "validation_scope": "Independent file-level recomputation of preservation, pairwise directional metrics, target descriptors, and execution boundaries."}
    write_json(HERE / "VALIDATION_REPORT.json", report)
    status["validator"] = validator
    write_json(HERE / "STAGE_STATUS.json", status)
    manifest = json.loads((HERE / "stage_manifest.json").read_text(encoding="utf-8"))
    manifest["validator"] = validator
    write_json(HERE / "stage_manifest.json", manifest)
    if validator != "PASS":
        return 1
    inventory = []
    for path in sorted(HERE.rglob("*")):
        if path.is_file() and path.name != "FILE_INVENTORY_AND_SHA256.json":
            inventory.append({"relative_path": path.relative_to(HERE).as_posix(), "size_bytes": path.stat().st_size, "sha256": sha256(path)})
    write_json(HERE / "FILE_INVENTORY_AND_SHA256.json", {"stage_name": spec["stage_name"], "files": inventory})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
