from __future__ import annotations

import csv, hashlib, json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
PROTOCOL_DIR = ROOT / "reports/research/submission_mlbd2026/mlbd2026_banking77_protocol_freeze_v1_20260920T143149Z"
READY_DIR = ROOT / "reports/research/submission_mlbd2026/mlbd2026_banking77_asset_and_split_readiness_v1_20260920T144526Z"
SOURCE_DIR = ROOT / "reports/research/submission_mlbd2026/mlbd2026_banking77_source_execution_v1_20260921T031659Z"
PRED_ROOT = SOURCE_DIR / "formal_source_outputs"
SOURCES = ("SOURCE_BERT", "SOURCE_ROBERTA", "SOURCE_DEBERTA")
EXPECTED_PRED_HASH = {
    "SOURCE_BERT": "96f1c134f074472038878af66aacdd6dff169658e97b64b49ce849506f2c612a",
    "SOURCE_ROBERTA": "4726aee8539d1cf480e138fdaf6e0013fb7a70c74be3f1419b12820727012ee4",
    "SOURCE_DEBERTA": "40cea54db46bf17668741ab7977046f4462a36627661cb6f6eb27b43439023d4",
}

def sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def canonical_hash(rows: list[dict]) -> str:
    payload = "".join(json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for x in rows)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def write_json(name: str, obj: object) -> None:
    (OUT / name).write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

def write_csv(name: str, rows: list[dict], fields: list[str]) -> None:
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)

def main() -> None:
    protocol = json.loads((PROTOCOL_DIR / "FROZEN_BANKING77_PROTOCOL.json").read_text(encoding="utf-8"))
    source_status = json.loads((SOURCE_DIR / "STAGE_STATUS.json").read_text(encoding="utf-8"))
    source_recompute = json.loads((SOURCE_DIR / "INDEPENDENT_RECOMPUTATION.json").read_text(encoding="utf-8"))
    final_validator = json.loads((SOURCE_DIR / "FINAL_VALIDATOR_REPORT.json").read_text(encoding="utf-8"))
    if protocol["status"] != "FROZEN" or source_status["status"] != "PASS" or source_recompute["status"] != "PASS":
        raise RuntimeError("AUTHORITY_STATUS_FAIL")

    loaded = {}
    source_receipt = {}
    for source in SOURCES:
        p = PRED_ROOT / source / "OFFICIAL_TEST_PREDICTIONS.npz"
        actual_hash = sha_file(p)
        if actual_hash != EXPECTED_PRED_HASH[source]:
            raise RuntimeError(f"PREDICTION_HASH_FAIL:{source}")
        z = np.load(p, allow_pickle=False)
        required = {"canonical_sample_ids", "truth_ids", "predicted_ids", "logits", "probabilities"}
        if set(z.files) != required:
            raise RuntimeError(f"PREDICTION_SCHEMA_FAIL:{source}:{z.files}")
        ids = z["canonical_sample_ids"].astype(str)
        truth = z["truth_ids"].astype(np.int64)
        pred = z["predicted_ids"].astype(np.int64)
        if ids.shape != (3080,) or truth.shape != (3080,) or pred.shape != (3080,) or len(set(ids.tolist())) != 3080:
            raise RuntimeError(f"PREDICTION_COUNT_FAIL:{source}")
        if not np.array_equal(pred, np.argmax(z["logits"], axis=1)):
            raise RuntimeError(f"ARGMAX_FAIL:{source}")
        loaded[source] = (ids, truth, pred)
        prov = json.loads((PRED_ROOT / source / "OFFICIAL_TEST_PREDICTION_PROVENANCE.json").read_text(encoding="utf-8"))
        source_key = source.replace("SOURCE_", "").lower()
        source_receipt[source] = {
            "prediction_path": str(p.relative_to(ROOT)).replace("\\", "/"),
            "prediction_sha256": actual_hash,
            "selected_checkpoint_weight_sha256": final_validator["sources"][source_key]["selected_checkpoint_weight_sha256"],
            "selected_checkpoint_config_sha256": prov["checkpoint"]["checkpoint_config_sha256"],
            "model_id": prov["model_id"], "revision": prov["revision"], "rows": 3080,
        }
    ref_ids, ref_truth, _ = loaded[SOURCES[0]]
    if any(not np.array_equal(ref_ids, loaded[s][0]) or not np.array_equal(ref_truth, loaded[s][1]) for s in SOURCES[1:]):
        raise RuntimeError("THREE_WAY_ALIGNMENT_FAIL")
    if list(ref_ids) != sorted(ref_ids.tolist()):
        raise RuntimeError("CANONICAL_ORDER_FAIL")

    membership = {}
    with (READY_DIR / "03_SPLIT_MEMBERSHIP_MANIFEST.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            membership[row["canonical_sample_id"]] = row
    if any(i not in membership or membership[i]["role"] != "OFFICIAL_TEST" for i in ref_ids):
        raise RuntimeError("OFFICIAL_TEST_MEMBERSHIP_FAIL")
    if any(int(membership[i]["label_id"]) != int(y) for i, y in zip(ref_ids, ref_truth)):
        raise RuntimeError("TRUTH_MAPPING_FAIL")

    pred_matrix = np.column_stack([loaded[s][2] for s in SOURCES])
    local_rows = []
    complement_rows = []
    for idx, (sid, y) in enumerate(zip(ref_ids.tolist(), ref_truth.tolist())):
        ps = pred_matrix[idx].tolist()
        wrong = [p for p in ps if p != y]
        counts = Counter(wrong)
        shared = [label for label, n in counts.items() if n >= 2]
        if len(shared) > 1:
            raise RuntimeError(f"NONUNIQUE_SHARED_WRONG:{sid}")
        base = {"canonical_sample_id": sid, "truth_id": int(y)}
        if shared:
            w = int(shared[0])
            agreeing = [SOURCES[j].replace("SOURCE_", "").lower() for j, p in enumerate(ps) if p == w and p != y]
            local_rows.append({**base, "shared_wrong_id": w, "agreeing_sources": "|".join(agreeing),
                               "bert_prediction": ps[0], "roberta_prediction": ps[1], "deberta_prediction": ps[2]})
        else:
            complement_rows.append(base)
    local_hash = canonical_hash(local_rows)
    complement_hash = canonical_hash(complement_rows)
    write_csv("02_LOCAL_SHARED_FAILURE_MEMBERSHIP.csv", local_rows, list(local_rows[0]) if local_rows else ["canonical_sample_id","truth_id","shared_wrong_id","agreeing_sources","bert_prediction","roberta_prediction","deberta_prediction"])
    write_csv("03_COMPLEMENT_MEMBERSHIP.csv", complement_rows, ["canonical_sample_id", "truth_id"])
    intents = len({r["truth_id"] for r in local_rows})
    composition = Counter("TRIPLE" if len(r["agreeing_sources"].split("|")) == 3 else r["agreeing_sources"] for r in local_rows)
    subset = {
        "status": "FROZEN_FROM_FORMAL_SOURCE_PREDICTIONS",
        "size": len(local_rows), "fraction_of_3080": len(local_rows) / 3080,
        "intents_represented": intents, "membership_sha256": local_hash,
        "complement_size": len(complement_rows), "complement_sha256": complement_hash,
        "source_composition": dict(sorted(composition.items())),
        "truth_intent_distribution": {str(k): v for k, v in sorted(Counter(r["truth_id"] for r in local_rows).items())},
        "shared_wrong_label_distribution": {str(k): v for k, v in sorted(Counter(r["shared_wrong_id"] for r in local_rows).items())},
        "no_go_gate": "PASS" if len(local_rows) >= 20 and len(complement_rows) > 0 else "FAIL",
        "rule": protocol["local_subset"]["inclusion"],
    }
    write_json("04_LOCAL_SUBSET_AND_GATE.json", subset)
    write_json("01_SOURCE_INPUT_RECEIPT.json", {
        "status": "PASS", "three_way_sample_alignment": True, "three_way_truth_alignment": True,
        "official_test_membership_rows": 3080, "sources": source_receipt,
        "immutable_after_receipt": True,
    })

    supervision_ids = sorted(k for k, v in membership.items() if v["role"] == "STUDENT_SUPERVISION")
    if len(supervision_ids) != 3066:
        raise RuntimeError("SUPERVISION_MEMBERSHIP_COUNT_FAIL")
    # Formal test artifacts cannot be reused as supervision predictions: the ID sets are disjoint by contract.
    test_set = set(ref_ids.tolist()); supervision_set = set(supervision_ids)
    overlap = test_set & supervision_set
    candidate_files = [p for p in ROOT.glob("reports/research/submission_mlbd2026/mlbd2026_banking77_*/**/*SUPERVISION*PREDICTION*.npz") if OUT not in p.parents]
    availability = {
        "required_membership": "STUDENT_SUPERVISION", "required_rows_per_source": 3066,
        "required_sources": list(SOURCES), "formal_artifacts_found": [str(p.relative_to(ROOT)).replace("\\", "/") for p in candidate_files],
        "official_test_rows_cannot_substitute": True, "official_test_supervision_id_overlap": len(overlap),
        "status": "MISSING_FORMAL_SOURCE_PREDICTIONS_ON_STUDENT_SUPERVISION",
        "consequence": "REAL/R1/R2 targets cannot be constructed without new Source inference from the already-frozen selected checkpoints.",
    }
    write_json("05_SUPERVISION_PREDICTION_AVAILABILITY.json", availability)

    stage_status = "NO_GO" if subset["no_go_gate"] == "FAIL" else "FAIL"
    blocker = "SOURCE_SUPPORT_NO_GO" if stage_status == "NO_GO" else "MISSING_3066x3_FORMAL_SOURCE_SUPERVISION_PREDICTIONS"
    write_json("STAGE_STATUS.json", {
        "stage": "MLBD2026_BANKING77_LOCAL_SUBSET_AND_TARGET_CONSTRUCTION_FREEZE_V1",
        "status": stage_status, "return_code": 1,
        "source_inputs": "PASS", "local_subset": subset, "blocker": blocker,
        "real_target": "NOT_CONSTRUCTED", "r1_target": "NOT_CONSTRUCTED", "r2_target": "NOT_CONSTRUCTED",
        "independent_recomputation": "PENDING", "student_input_package_ready": False,
        "formal_student_fits": 0, "source_training": 0, "student_training": 0,
        "student_inference": 0, "gpu": 0, "autodl": 0, "git_writes": 0,
        "created_utc": datetime.now(timezone.utc).isoformat(),
    })
    print(json.dumps({"stage_status": stage_status, "blocker": blocker, "local_subset": subset}, indent=2))

if __name__ == "__main__":
    main()
