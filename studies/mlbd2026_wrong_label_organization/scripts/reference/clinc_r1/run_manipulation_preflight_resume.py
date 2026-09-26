from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import os
import sys
import traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer, DebertaV2ForSequenceClassification, DebertaV2Tokenizer

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
SPEC_PATH = HERE / "MANIPULATION_PREFLIGHT_SPEC.json"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_label_mapping_digest(mapping: dict) -> str:
    canonical = (
        json.dumps(
            {"mapping_rule": mapping["mapping_rule"], "labels": mapping["labels"]},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def write_json(path: Path, value: object) -> None:
    temp = path.with_suffix(path.suffix + ".partial")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def write_csv_gz(path: Path, fields: list[str], rows: list[dict]) -> None:
    with gzip.open(path, "wt", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def encode(tokenizer, rows: list[list[str]], label2id: dict[str, int], max_length: int):
    texts = [row[0] for row in rows]
    labels = torch.tensor([label2id[row[1]] for row in rows], dtype=torch.long)
    enc = tokenizer(texts, padding="max_length", truncation=True, max_length=max_length, return_tensors="pt")
    keys = [key for key in ("input_ids", "attention_mask", "token_type_ids") if key in enc]
    return keys, TensorDataset(*[enc[key] for key in keys], labels)


@torch.inference_mode()
def infer(model, loader, keys: list[str], device: torch.device):
    model.eval()
    logits_parts = []
    truth_parts = []
    for batch in loader:
        inputs = {key: tensor.to(device, non_blocking=True) for key, tensor in zip(keys, batch[:-1])}
        labels = batch[-1].to(device, non_blocking=True)
        logits = model(**inputs).logits
        if not torch.isfinite(logits).all():
            raise RuntimeError("Non-finite dev logits")
        logits_parts.append(logits.float().cpu())
        truth_parts.append(labels.cpu())
    logits = torch.cat(logits_parts).numpy().astype(np.float32)
    truth = torch.cat(truth_parts).numpy().astype(np.int64)
    shifted = logits - logits.max(axis=1, keepdims=True)
    probabilities = np.exp(shifted).astype(np.float32)
    probabilities /= probabilities.sum(axis=1, keepdims=True)
    predicted = probabilities.argmax(axis=1).astype(np.int64)
    if not np.isfinite(probabilities).all() or not np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-5):
        raise RuntimeError("Invalid dev probabilities")
    loss = float(F.cross_entropy(torch.from_numpy(logits), torch.from_numpy(truth), reduction="mean").item())
    return logits, probabilities, truth, predicted, loss


def wrong_metrics(truth: np.ndarray, a: np.ndarray, b: np.ndarray) -> dict:
    both = (a != truth) & (b != truth)
    count = int(both.sum())
    same = int(((a == b) & both).sum())
    return {
        "both_wrong_count": count,
        "same_wrong_label_count": same,
        "different_wrong_label_count": count - same,
        "same_wrong_label_fraction": None if count == 0 else same / count,
    }


def target_metrics(target: np.ndarray, predictions: np.ndarray) -> dict:
    positive = target > 0
    entropy = -np.where(positive, target * np.log(np.where(positive, target, 1.0)), 0.0).sum(axis=1)
    unique_counts = np.array([len(set(row.tolist())) for row in predictions], dtype=np.int64)
    return {
        "entropy_unit": "natural_log_nats",
        "mean_target_entropy": float(entropy.mean()),
        "unanimous_proportion": float((unique_counts == 1).mean()),
        "two_vs_one_proportion": float((unique_counts == 2).mean()),
        "three_way_disagreement_proportion": float((unique_counts == 3).mean()),
    }


def build_targets(predictions: np.ndarray, num_labels: int) -> np.ndarray:
    targets = np.zeros((len(predictions), num_labels), dtype=np.float32)
    rows = np.arange(len(predictions))
    for source_index in range(predictions.shape[1]):
        targets[rows, predictions[:, source_index]] += np.float32(1.0 / predictions.shape[1])
    if not np.allclose(targets.sum(axis=1), 1.0, atol=1e-7):
        raise RuntimeError("Target rows do not sum to one")
    return targets


def main() -> int:
    status = {
        "stage_name": "REAL_CLINC150_MINIMAL_STUDENT_CONSEQUENCE_MANIPULATION_PREFLIGHT_V1_RESUME_EXECUTION",
        "status": "RUNNING",
        "return_code": None,
        "manifest": "PENDING",
        "validator": "PENDING",
        "source_dev_inference_count": 0,
        "source_training_count": 0,
        "student_training_count": 0,
        "started_utc": now(),
    }
    write_json(HERE / "STAGE_STATUS.json", status)
    try:
        spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        if spec["control_seed"] != 20260907 or spec["student_training_authorized"]:
            raise RuntimeError("Spec authorization mismatch")
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA unavailable")
        device = torch.device("cuda:0")

        dataset_path = PROJECT / spec["dataset_relative_path"]
        mapping_path = PROJECT / spec["label_mapping_relative_path"]
        domain_path = PROJECT / spec["domain_mapping_relative_path"]
        for path, expected in ((dataset_path, spec["dataset_sha256"]), (domain_path, spec["domain_mapping_sha256"])):
            if sha256(path) != expected:
                raise RuntimeError(f"Input hash mismatch: {path}")
        data = json.loads(dataset_path.read_text(encoding="utf-8"))
        mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
        domains = json.loads(domain_path.read_text(encoding="utf-8"))
        mapping_canonical_digest = canonical_label_mapping_digest(mapping)
        if mapping_canonical_digest != spec["label_mapping_sha256"]:
            raise RuntimeError("Canonical label mapping digest mismatch")
        if mapping.get("canonical_sha256") != spec["label_mapping_sha256"]:
            raise RuntimeError("Embedded canonical label mapping digest mismatch")
        if len(data["val"]) != 3000 or len(mapping["labels"]) != 150:
            raise RuntimeError("Official dev or label count mismatch")
        id2label = {int(item["id"]): item["label"] for item in mapping["labels"]}
        label2id = {label: idx for idx, label in id2label.items()}
        label_domain = {label: domain for domain, labels in domains.items() for label in labels}
        if len(label_domain) != 150 or set(label_domain) != set(label2id):
            raise RuntimeError("Domain mapping mismatch")
        truth_expected = np.array([label2id[row[1]] for row in data["val"]], dtype=np.int64)
        example_ids = np.array([f"clinc150:dev:{i:06d}" for i in range(3000)])

        predictions = []
        source_metrics = {}
        source_provenance = []
        for source in spec["sources"]:
            status["current_source"] = source["key"]
            status["current_source_state"] = "PREFLIGHT"
            write_json(HERE / "STAGE_STATUS.json", status)
            run_status_path = PROJECT / source["run_status_relative_path"]
            validation_path = PROJECT / source["validation_relative_path"]
            checkpoint = PROJECT / source["best_checkpoint_relative_path"]
            run_status = json.loads(run_status_path.read_text(encoding="utf-8"))
            validation = json.loads(validation_path.read_text(encoding="utf-8"))
            if run_status.get("status") != "SUCCESS" or validation.get("validator") != "PASS":
                raise RuntimeError(f"Frozen Source upstream invalid: {source['key']}")
            if run_status.get("repository") != source["repository"] or run_status.get("revision") != source["revision"]:
                raise RuntimeError(f"Frozen Source identity mismatch: {source['key']}")
            if Path(run_status.get("best_checkpoint", "")) != checkpoint:
                raise RuntimeError(f"Best checkpoint binding mismatch: {source['key']}")
            status["current_source_state"] = "INFERENCE_RUNNING"
            write_json(HERE / "STAGE_STATUS.json", status)
            if source["key"] == "deberta":
                tokenizer = DebertaV2Tokenizer.from_pretrained(checkpoint, local_files_only=True)
                model = DebertaV2ForSequenceClassification.from_pretrained(checkpoint, local_files_only=True, use_safetensors=True)
            else:
                tokenizer = AutoTokenizer.from_pretrained(checkpoint, local_files_only=True, use_fast=True)
                model = AutoModelForSequenceClassification.from_pretrained(checkpoint, local_files_only=True, use_safetensors=True)
            keys, dataset = encode(tokenizer, data["val"], label2id, spec["max_sequence_length"])
            loader = DataLoader(dataset, batch_size=64, shuffle=False, num_workers=0, pin_memory=True)
            model.to(device)
            logits, probabilities, truth, predicted, log_loss = infer(model, loader, keys, device)
            if not np.array_equal(truth, truth_expected):
                raise RuntimeError(f"Truth alignment mismatch: {source['key']}")
            accuracy = float((predicted == truth).mean())
            if abs(accuracy - float(source["expected_best_dev_accuracy"])) > 1e-12:
                raise RuntimeError(f"Dev accuracy does not reproduce best-checkpoint metric: {source['key']} {accuracy}")
            source_dir = HERE / f"source_{source['key']}"
            source_dir.mkdir(exist_ok=False)
            np.savez_compressed(source_dir / "DEV_SCORES.npz", logits=logits, probabilities=probabilities, truth_ids=truth, predicted_ids=predicted)
            pred_rows = []
            for i, (truth_id, pred_id) in enumerate(zip(truth, predicted)):
                truth_label = id2label[int(truth_id)]
                pred_rows.append({
                    "example_id": example_ids[i], "truth_label": truth_label, "truth_id": int(truth_id),
                    "predicted_label": id2label[int(pred_id)], "predicted_id": int(pred_id),
                    "domain": label_domain[truth_label], "correct": int(pred_id == truth_id),
                })
            write_csv_gz(source_dir / "DEV_PREDICTIONS.csv.gz", ["example_id", "truth_label", "truth_id", "predicted_label", "predicted_id", "domain", "correct"], pred_rows)
            metrics = {"source": source["key"], "dev_count": 3000, "dev_accuracy": accuracy, "dev_log_loss": log_loss, "dev_error_count": int((predicted != truth).sum()), "inference_count": 1, "training_count": 0}
            write_json(source_dir / "SOURCE_DEV_METRICS.json", metrics)
            probability_row_sums = probabilities.sum(axis=1)
            source_checks = {
                "inference_return_code_zero": True,
                "status_success": True,
                "prediction_count_3000": len(pred_rows) == 3000,
                "example_id_unique": len(set(example_ids.tolist())) == 3000,
                "missing_predictions_zero": predicted.shape == (3000,),
                "duplicate_predictions_zero": len(pred_rows) == len(set(example_ids.tolist())),
                "logits_finite": bool(np.isfinite(logits).all()),
                "probabilities_finite": bool(np.isfinite(probabilities).all()),
                "probability_row_sums_valid": bool(np.allclose(probability_row_sums, 1.0, atol=1e-5)),
                "truth_mapping_aligned": bool(np.array_equal(truth, truth_expected)),
                "predicted_labels_in_range": bool(((predicted >= 0) & (predicted < 150)).all()),
                "training_count_zero": True,
            }
            if not all(source_checks.values()):
                raise RuntimeError(f"Source output validation failed: {source['key']}")
            write_json(source_dir / "RUN_STATUS.json", {
                "source": source["key"], "status": "SUCCESS", "return_code": 0,
                "manifest": "SUCCESS", "inference_count": 1, "training_count": 0,
                "prediction_count": 3000, "checkpoint": str(checkpoint),
            })
            write_json(source_dir / "VALIDATION_REPORT.json", {
                "source": source["key"], "validator": "PASS", "checks": source_checks,
            })
            source_metrics[source["key"]] = metrics
            source_provenance.append({
                "source": source["key"], "repository": source["repository"], "revision": source["revision"],
                "best_checkpoint": str(checkpoint), "checkpoint_model_sha256": sha256(checkpoint / "model.safetensors"),
                "run_status_sha256": sha256(run_status_path), "upstream_validation_sha256": sha256(validation_path),
                "tokenizer_class": source["tokenizer_class"], "dev_inference_count": 1,
            })
            predictions.append(predicted)
            status["source_dev_inference_count"] += 1
            status["current_source_state"] = "SUCCESS"
            write_json(HERE / "STAGE_STATUS.json", status)
            del model, tokenizer, loader, dataset
            torch.cuda.empty_cache()

        real_predictions = np.stack(predictions, axis=1)
        scrambled_predictions = real_predictions.copy()
        audit_rows = []
        source_preservation = {}
        for source_index, source in enumerate(spec["sources"]):
            before = real_predictions[:, source_index]
            after = scrambled_predictions[:, source_index]
            for truth_id in range(spec["num_labels"]):
                wrong_idx = np.where((truth_expected == truth_id) & (before != truth_id))[0]
                values = before[wrong_idx].copy()
                rng = np.random.default_rng(np.random.SeedSequence([spec["control_seed"], source_index + 1, truth_id]))
                after[wrong_idx] = rng.permutation(values)
                before_multiset = Counter(values.tolist())
                after_multiset = Counter(after[wrong_idx].tolist())
                audit_rows.append({
                    "source": source["key"], "truth_id": truth_id, "truth_label": id2label[truth_id],
                    "error_count_real": len(wrong_idx), "error_count_scrambled": int((after[truth_expected == truth_id] != truth_id).sum()),
                    "wrong_label_multiset_real_sha256": hashlib.sha256(json.dumps(sorted(before_multiset.items())).encode()).hexdigest(),
                    "wrong_label_multiset_scrambled_sha256": hashlib.sha256(json.dumps(sorted(after_multiset.items())).encode()).hexdigest(),
                    "multiset_equal": before_multiset == after_multiset,
                })
            real_correct = before == truth_expected
            scrambled_correct = after == truth_expected
            per_intent_ok = all(row["multiset_equal"] and row["error_count_real"] == row["error_count_scrambled"] for row in audit_rows if row["source"] == source["key"])
            source_preservation[source["key"]] = {
                "example_count_equal": len(before) == len(after) == 3000,
                "overall_correct_wrong_vector_equal": bool(np.array_equal(real_correct, scrambled_correct)),
                "overall_accuracy_equal": float(real_correct.mean()) == float(scrambled_correct.mean()),
                "per_truth_intent_error_count_equal": per_intent_ok,
                "per_truth_intent_wrong_label_multiset_equal": per_intent_ok,
                "labels_in_range": bool(((after >= 0) & (after < 150)).all()),
                "correct_examples_unchanged": bool(np.array_equal(before[real_correct], after[real_correct])),
            }

        preservation = {
            "validator": "PASS" if all(all(values.values()) for values in source_preservation.values()) else "FAIL",
            "source_results": source_preservation,
            "source_weights_real": spec["source_weights"],
            "source_weights_scrambled": spec["source_weights"],
            "source_weights_equal": spec["source_weights"] == [1 / 3, 1 / 3, 1 / 3],
            "marginal_quality_preserved": all(item["overall_accuracy_equal"] for item in source_preservation.values()),
            "per_example_error_identity_preserved": all(item["overall_correct_wrong_vector_equal"] for item in source_preservation.values()),
            "per_intent_confusion_marginals_preserved": all(item["per_truth_intent_wrong_label_multiset_equal"] for item in source_preservation.values()),
        }
        if preservation["validator"] != "PASS" or not preservation["source_weights_equal"]:
            raise RuntimeError("Preservation validator failed")

        real_targets = build_targets(real_predictions, spec["num_labels"])
        scrambled_targets = build_targets(scrambled_predictions, spec["num_labels"])
        conditions = HERE / "supervision"
        conditions.mkdir(exist_ok=False)
        np.savez_compressed(conditions / "CONDITION_REAL_SUPERVISION.npz", example_ids=example_ids, truth_ids=truth_expected, source_predictions=real_predictions, targets=real_targets, source_weights=np.array(spec["source_weights"], dtype=np.float64))
        np.savez_compressed(conditions / "CONDITION_DIRECTION_SCRAMBLED_SUPERVISION.npz", example_ids=example_ids, truth_ids=truth_expected, source_predictions=scrambled_predictions, targets=scrambled_targets, source_weights=np.array(spec["source_weights"], dtype=np.float64), control_seed=np.array([spec["control_seed"]], dtype=np.int64))
        write_json(HERE / "PRESERVATION_VALIDATION.json", preservation)
        with (HERE / "PER_INTENT_PRESERVATION_AUDIT.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(audit_rows[0]))
            writer.writeheader()
            writer.writerows(audit_rows)

        pair_keys = ((0, 1, "bert_roberta"), (0, 2, "bert_deberta"), (1, 2, "roberta_deberta"))
        pairs = {}
        differences = []
        for a, b, key in pair_keys:
            real = wrong_metrics(truth_expected, real_predictions[:, a], real_predictions[:, b])
            scrambled = wrong_metrics(truth_expected, scrambled_predictions[:, a], scrambled_predictions[:, b])
            if real["both_wrong_count"] != scrambled["both_wrong_count"]:
                raise RuntimeError(f"Both-wrong preservation failed: {key}")
            delta = scrambled["same_wrong_label_fraction"] - real["same_wrong_label_fraction"]
            pairs[key] = {"real": real, "scrambled": scrambled, "scrambled_minus_real_fraction": delta, "real_minus_scrambled_fraction": -delta}
            differences.append(delta)
        directional_changed = any(abs(delta) > 0 for delta in differences)
        pairwise_real_same_sum = sum(item["real"]["same_wrong_label_count"] for item in pairs.values())
        pairwise_scrambled_same_sum = sum(item["scrambled"]["same_wrong_label_count"] for item in pairs.values())
        decreased = sum(delta < 0 for delta in differences)
        increased = sum(delta > 0 for delta in differences)
        clear_change = directional_changed and decreased >= 2 and increased == 0 and pairwise_scrambled_same_sum < pairwise_real_same_sum
        outcome = "STUDENT_CONSEQUENCE_MANIPULATION_READY" if clear_change else "INSUFFICIENT_DIRECTIONAL_CONTRAST"
        metrics = {
            "source_dev_metrics": source_metrics,
            "pairwise": pairs,
            "directional_alignment_changed": directional_changed,
            "clear_directional_change": clear_change,
            "pairs_decreased": decreased,
            "pairs_increased": increased,
            "pairwise_real_same_wrong_count_sum": pairwise_real_same_sum,
            "pairwise_scrambled_same_wrong_count_sum": pairwise_scrambled_same_sum,
            "real_target_metrics": target_metrics(real_targets, real_predictions),
            "scrambled_target_metrics": target_metrics(scrambled_targets, scrambled_predictions),
            "mean_target_l1_difference": float(np.abs(real_targets - scrambled_targets).sum(axis=1).mean()),
            "target_changed_example_proportion": float(np.any(real_targets != scrambled_targets, axis=1).mean()),
            "manipulation_gate_outcome": outcome,
            "target_entropy_is_descriptive_only": True,
            "target_l1_is_descriptive_only": True,
        }
        write_json(HERE / "MANIPULATION_METRICS.json", metrics)

        canonical_rows = []
        for i in range(3000):
            truth_label = id2label[int(truth_expected[i])]
            canonical_rows.append({
                "example_id": example_ids[i], "truth_label": truth_label, "truth_id": int(truth_expected[i]), "domain": label_domain[truth_label],
                "bert_real_pred": int(real_predictions[i, 0]), "roberta_real_pred": int(real_predictions[i, 1]), "deberta_real_pred": int(real_predictions[i, 2]),
                "bert_scrambled_pred": int(scrambled_predictions[i, 0]), "roberta_scrambled_pred": int(scrambled_predictions[i, 1]), "deberta_scrambled_pred": int(scrambled_predictions[i, 2]),
            })
        write_csv_gz(HERE / "CANONICAL_DEV_REAL_AND_SCRAMBLED_PREDICTIONS.csv.gz", list(canonical_rows[0]), canonical_rows)

        report = f"""# REAL_CLINC150_MINIMAL_STUDENT_CONSEQUENCE_MANIPULATION_PREFLIGHT_V1_RESUME_EXECUTION

## Executive status

`MANIPULATION_GATE_OUTCOME={outcome}`. Three frozen Source checkpoints each performed one official-dev inference; Source training and Student training were zero.

The supervision pool is CLINC150 official dev (3000 examples, 150 intents × 20). It was used for frozen Source checkpoint selection and is therefore not independent of Source model selection. Official test was not used to construct supervision and remains reserved for future held-out Student evaluation.

## Fixed manipulation

REAL uses the three original hard predictions with equal 1/3 weights. DIRECTION_SCRAMBLED uses the single fixed control seed 20260907 and independently permutes each Source's wrong-label multiset within each truth intent. Correct predictions are unchanged. No permutation seed search or optimization occurred.

## Source dev results

| Source | Dev accuracy | Dev error count |
|---|---:|---:|
| BERT | {source_metrics['bert']['dev_accuracy']:.9f} | {source_metrics['bert']['dev_error_count']} |
| RoBERTa | {source_metrics['roberta']['dev_accuracy']:.9f} | {source_metrics['roberta']['dev_error_count']} |
| DeBERTa | {source_metrics['deberta']['dev_accuracy']:.9f} | {source_metrics['deberta']['dev_error_count']} |

## Preservation

- `MARGINAL_QUALITY_PRESERVED={str(preservation['marginal_quality_preserved']).lower()}`
- `PER_EXAMPLE_ERROR_IDENTITY_PRESERVED={str(preservation['per_example_error_identity_preserved']).lower()}`
- `PER_INTENT_CONFUSION_MARGINALS_PRESERVED={str(preservation['per_intent_confusion_marginals_preserved']).lower()}`
- source weights remain 1/3, 1/3, 1/3.

## Directional contrast

| Pair | Both wrong | REAL same fraction | SCRAMBLED same fraction | SCRAMBLED−REAL |
|---|---:|---:|---:|---:|
| BERT–RoBERTa | {pairs['bert_roberta']['real']['both_wrong_count']} | {pairs['bert_roberta']['real']['same_wrong_label_fraction']:.9f} | {pairs['bert_roberta']['scrambled']['same_wrong_label_fraction']:.9f} | {pairs['bert_roberta']['scrambled_minus_real_fraction']:.9f} |
| BERT–DeBERTa | {pairs['bert_deberta']['real']['both_wrong_count']} | {pairs['bert_deberta']['real']['same_wrong_label_fraction']:.9f} | {pairs['bert_deberta']['scrambled']['same_wrong_label_fraction']:.9f} | {pairs['bert_deberta']['scrambled_minus_real_fraction']:.9f} |
| RoBERTa–DeBERTa | {pairs['roberta_deberta']['real']['both_wrong_count']} | {pairs['roberta_deberta']['real']['same_wrong_label_fraction']:.9f} | {pairs['roberta_deberta']['scrambled']['same_wrong_label_fraction']:.9f} | {pairs['roberta_deberta']['scrambled_minus_real_fraction']:.9f} |

`DIRECTIONAL_ALIGNMENT_CHANGED={str(directional_changed).lower()}`; `CLEAR_DIRECTIONAL_CHANGE={str(clear_change).lower()}`.

## Student-visible target descriptors

| Condition | Mean entropy (nats) | Unanimous | 2-vs-1 | 3-way |
|---|---:|---:|---:|---:|
| REAL | {metrics['real_target_metrics']['mean_target_entropy']:.9f} | {metrics['real_target_metrics']['unanimous_proportion']:.9f} | {metrics['real_target_metrics']['two_vs_one_proportion']:.9f} | {metrics['real_target_metrics']['three_way_disagreement_proportion']:.9f} |
| SCRAMBLED | {metrics['scrambled_target_metrics']['mean_target_entropy']:.9f} | {metrics['scrambled_target_metrics']['unanimous_proportion']:.9f} | {metrics['scrambled_target_metrics']['two_vs_one_proportion']:.9f} | {metrics['scrambled_target_metrics']['three_way_disagreement_proportion']:.9f} |

- Mean per-example target L1 difference: {metrics['mean_target_l1_difference']:.9f}
- Proportion with changed Student-visible target: {metrics['target_changed_example_proportion']:.9f}

Entropy and L1 distance are descriptive only and are not new causal variables or primary scientific estimands.

## Manipulation interpretation

The transformation uses truth labels to permute wrong labels within truth intent. It is a controlled causal-style supervision manipulation, not a deployable source-generation algorithm. It asks whether changing cross-source wrong-label directional alignment while fixing source marginal quality, per-example error identity, and per-intent confusion marginals is suitable for a later downstream Student consequence test.

## Boundary

This preflight establishes whether a fixed within-truth-class wrong-label permutation creates usable directional contrast while preserving specified source marginals. It does not establish Student consequence. `STUDENT_TRAINING_COUNT=0`; official test was not used; no Source retraining, weighting, Bootstrap, Step04, or recursive training occurred.

The only possible next stage after human review of a READY outcome is a separately authorized minimal Student consequence experiment design/execution contract. This stage does not authorize it.
"""
        (HERE / "REAL_CLINC150_MINIMAL_STUDENT_CONSEQUENCE_MANIPULATION_PREFLIGHT_V1_RESUME_EXECUTION_20260907.md").write_text(report, encoding="utf-8")

        provenance = {
            "created_utc": now(), "execution_location": "AutoDL 316 / autodl316-correlation", "remote_stage_path": str(HERE),
            "formal_dataset": "CLINC150", "dataset_revision": spec["dataset_revision"], "dataset_sha256": spec["dataset_sha256"],
            "label_mapping_raw_file_sha256": sha256(mapping_path), "canonical_label_mapping_digest": mapping_canonical_digest,
            "domain_mapping_sha256": spec["domain_mapping_sha256"],
            "sources": source_provenance, "source_dev_inference_count": 3, "source_training_count": 0,
            "student_training_count": 0, "student_inference_count": 0, "control_seed": spec["control_seed"],
            "permutation_seed_search": False, "official_test_read": False, "git_write_performed": False,
        }
        write_json(HERE / "PROVENANCE.json", provenance)
        alignment = {
            "alignment_status": "PASS", "alignment_packet_type": "REAL_CLINC150_MINIMAL_STUDENT_CONSEQUENCE_MANIPULATION_PREFLIGHT_V1_RESUME_EXECUTION", "stage_status": "REAL_CLINC150_STUDENT_CONSEQUENCE_MANIPULATION_PREFLIGHT_COMPLETE",
            "formal_dataset": "CLINC150", "formal_source_set_selected": True, "formal_student_model": "ELECTRA-small",
            "student_near_term_role": "DOWNSTREAM_CONSEQUENCE_PROBE", "future_recursive_learner_selected": False,
            "student_consequence_manipulation_type": spec["manipulation_type"],
            "student_supervision_pool": "CLINC150_OFFICIAL_DEV", "manipulation_seed": spec["control_seed"], "source_dev_inference_count": 3,
            "source_dev_accuracies": {key: value["dev_accuracy"] for key, value in source_metrics.items()},
            "pairwise_real_both_wrong_counts": {key: value["real"]["both_wrong_count"] for key, value in pairs.items()},
            "pairwise_scrambled_both_wrong_counts": {key: value["scrambled"]["both_wrong_count"] for key, value in pairs.items()},
            "marginal_quality_preserved": preservation["marginal_quality_preserved"], "per_example_error_identity_preserved": preservation["per_example_error_identity_preserved"],
            "per_intent_confusion_marginals_preserved": preservation["per_intent_confusion_marginals_preserved"],
            "pairwise_real_same_wrong_label_fractions": {key: value["real"]["same_wrong_label_fraction"] for key, value in pairs.items()},
            "pairwise_scrambled_same_wrong_label_fractions": {key: value["scrambled"]["same_wrong_label_fraction"] for key, value in pairs.items()},
            "pairwise_directional_alignment_deltas": {key: value["real_minus_scrambled_fraction"] for key, value in pairs.items()},
            "real_mean_target_entropy": metrics["real_target_metrics"]["mean_target_entropy"],
            "scrambled_mean_target_entropy": metrics["scrambled_target_metrics"]["mean_target_entropy"],
            "real_target_pattern_proportions": {key: value for key, value in metrics["real_target_metrics"].items() if key.endswith("_proportion")},
            "scrambled_target_pattern_proportions": {key: value for key, value in metrics["scrambled_target_metrics"].items() if key.endswith("_proportion")},
            "mean_target_l1_difference": metrics["mean_target_l1_difference"],
            "target_changed_example_proportion": metrics["target_changed_example_proportion"],
            "directional_alignment_changed": directional_changed, "manipulation_gate_outcome": outcome,
            "student_training_count": 0, "student_consequence_real_data_verified": False, "human_decision_required": True,
            "current_execution_authorization": "NONE_FOR_NEW_RESEARCH_EXECUTION", "not_a_frozen_protocol": True, "not_an_execution_authorization": True,
        }
        write_json(HERE / "CHATGPT_CODEX_ALIGNMENT_PACKET.json", alignment)
        status.update({
            "status": "REAL_CLINC150_STUDENT_CONSEQUENCE_MANIPULATION_PREFLIGHT_COMPLETE", "return_code": 0, "manifest": "SUCCESS", "validator": "PENDING",
            "completed_utc": now(), "source_dev_inference_count": 3, "real_supervision_ready": True, "scrambled_supervision_ready": True,
            "marginal_quality_preserved": preservation["marginal_quality_preserved"], "per_example_error_identity_preserved": preservation["per_example_error_identity_preserved"],
            "per_intent_confusion_marginals_preserved": preservation["per_intent_confusion_marginals_preserved"],
            "directional_alignment_changed": directional_changed, "manipulation_gate_outcome": outcome, "student_training_count": 0,
            "human_decision_required": True,
        })
        write_json(HERE / "STAGE_STATUS.json", status)
        write_json(HERE / "stage_manifest.json", {
            "stage_name": status["stage_name"], "status": status["status"], "return_code": 0, "manifest": "SUCCESS", "validator": "PENDING",
            "authorization_scope": "THREE_FROZEN_SOURCE_OFFICIAL_DEV_INFERENCES_AND_FIXED_MANIPULATION_PREFLIGHT_ONLY",
            "source_training_count": 0, "student_training_count": 0, "official_test_read": False, "git_write_performed": False,
        })
        return 0
    except Exception as exc:
        status.update({"status": "MANIPULATION_PREFLIGHT_FAILED", "return_code": 1, "manifest": "FAILED", "validator": "NOT_RUN", "completed_utc": now(), "error_type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc()})
        write_json(HERE / "STAGE_STATUS.json", status)
        write_json(HERE / "stage_manifest.json", {"stage_name": status["stage_name"], "status": status["status"], "return_code": 1, "manifest": "FAILED", "validator": "NOT_RUN", "source_training_count": 0, "student_training_count": 0, "git_write_performed": False})
        print(traceback.format_exc(), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
