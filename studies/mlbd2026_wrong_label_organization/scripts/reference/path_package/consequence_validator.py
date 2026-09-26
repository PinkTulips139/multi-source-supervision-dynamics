"""Fail-closed per-fit validator for formal XLNet consequence outputs."""
from pathlib import Path
import json, math
import numpy as np
from consequence_runtime import CONDITIONS, ORDERS, read_json, sha, load_bindings, validate_seed_assets
from trajectory_logger import ordered_id_digest, validate_step_row

def _support_core(support):
    import importlib.util
    spec = importlib.util.spec_from_file_location("frozen_v5_readiness_core", support / "readiness_core.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def validate_checkpoint(checkpoint, support, seed):
    import torch
    from safetensors import safe_open
    support=Path(support);core=_support_core(support)
    protocol=read_json(support/"package/FROZEN_SECOND_STUDENT_ADEQUACY_PROTOCOL.json")
    model,_=core.build(support/"model_assets",protocol,seed)
    expected={name:tuple(t.shape) for name,t in model.state_dict().items()};del model
    with safe_open(str(checkpoint),framework="pt",device="cpu") as f:
        if set(f.keys())!=set(expected):raise ValueError("Checkpoint key identity")
        for name in f.keys():
            tensor=f.get_tensor(name)
            if tuple(tensor.shape)!=expected[name] or tensor.dtype!=torch.float32 or not torch.isfinite(tensor).all():raise ValueError("Checkpoint tensor: "+name)
    return dict(status="PASS",tensor_count=len(expected),all_fp32_finite=True)

def validate_fit(fit, package_root, project_root, seed, order_id, condition):
    fit = Path(fit); package_root = Path(package_root)
    if condition not in CONDITIONS or order_id not in ORDERS or seed not in (167174636,1852328752,1231418446,1461753708) or fit.name!=condition or fit.parent.name!=order_id or fit.parent.parent.name!=f"SEED_{seed}": raise ValueError("Fit identity")
    bindings = load_bindings(package_root, project_root)
    support, seeds = validate_seed_assets(package_root, project_root, order_id)
    status = read_json(fit / "status/COMPLETE.json")
    if status != dict(status="COMPLETE", seed=seed, order_id=order_id, condition=condition, steps=1880, epochs=20):
        raise ValueError("Incomplete/status")
    provenance = read_json(fit / "provenance/INITIAL.json")
    matrix=read_json(package_root.parent/"ORDER_IDENTITY_MATRIX.json")
    expected_order=next(x for x in matrix["seeds"] if x["seed"]==seed)[order_id]
    if provenance["seed"] != seed or provenance["order_id"]!=order_id or provenance["condition"] != condition or provenance["initial_state"] != seeds[str(seed)]["initial"] or provenance["order"] != expected_order:
        raise ValueError("Seed/init/order provenance")
    contract = read_json(package_root / "PATH_CONTRACT.json")
    pair=next(x for x in read_json(package_root/"FOUR_REAL_PAIRINGS.json") if x["seed"]==seed)
    if provenance["initial_state"]["full_digest"]!=pair["initial_state"]["full_digest"] or provenance["initial_state"]["head_digest"]!=pair["initial_state"]["head_digest"] or provenance["recipe"]!="R0" or not provenance["optimizer_state_initially_empty"]:
        raise ValueError("Initial/head/recipe pairing")
    role = next(x for x in contract["assets"] if x["role"] == condition)
    if provenance["supervision_sha256"] != role["sha256"] or provenance["package_manifest_sha256"] != sha(package_root / "PACKAGE_MANIFEST.json"):
        raise ValueError("Supervision/package provenance")
    manifest = read_json(fit / "manifest/MANIFEST.json")
    for row in manifest["files"]:
        if sha(fit / row["path"]) != row["sha256"]: raise ValueError("Fit artifact hash")
    required = {"checkpoint/model.safetensors", "predictions/TEST.npz", "metrics/METRICS.json", "logs/TRAIN.jsonl", "logs/EPOCH.jsonl", "provenance/INITIAL.json", "status/COMPLETE.json"}
    if not required.issubset({x["path"] for x in manifest["files"]}): raise ValueError("Incomplete artifact set")
    checkpoint_validation=validate_checkpoint(fit/"checkpoint/model.safetensors",support,seed)
    with np.load(fit / "predictions/TEST.npz", allow_pickle=False) as a:
        logits=a["logits"]; truth=a["truth_ids"]
        if logits.shape != (4500,150) or logits.dtype != np.float32 or not np.isfinite(logits).all() or a["example_ids"].tolist() != bindings["test_ids"] or not np.array_equal(truth, bindings["test_truth"]):
            raise ValueError("Prediction/test identity")
        metrics = _support_core(support).evaluate(logits, truth)
    stored = read_json(fit / "metrics/METRICS.json")
    if abs(metrics["mean_unsmoothed_nll"]-stored["test_true_label_logloss"]) > 1e-12 or metrics["correct_count"] != stored["test_correct_count"]:
        raise ValueError("Independent metric recomputation")
    recipe=read_json(support/"package/FROZEN_SECOND_STUDENT_ADEQUACY_PROTOCOL.json")["R0"]
    logs=[json.loads(x) for x in (fit/"logs/TRAIN.jsonl").read_text(encoding="utf-8").splitlines()]
    schedule=seeds[str(seed)]["schedule"]
    if len(logs)!=1880 or any((not validate_step_row(x)) or x["global_step"]!=n+1 or x["epoch"]!=n//94+1 or x["batch_index"]!=n%94 or x["ordered_ID_sha256"]!=ordered_id_digest(schedule[n//94]["example_ids"][(n%94)*32:(n%94+1)*32]) or any(lr!=_support_core(support).lr_at(recipe,n) for lr in x["lr_by_group"]) for n,x in enumerate(logs)):
        raise ValueError("Training log")
    if logs[0]["rng_before_forward"] != provenance["rng"]:
        raise ValueError("Initial-to-first-forward RNG drift")
    epoch_logs=[json.loads(x) for x in (fit/"logs/EPOCH.jsonl").read_text(encoding="utf-8").splitlines()]
    if len(epoch_logs)!=20 or any(x["epoch"]!=i+1 or x["optimizer_step_min_max"]!=[(i+1)*94,(i+1)*94] for i,x in enumerate(epoch_logs)):
        raise ValueError("Epoch trajectory")
    return dict(status="PASS", seed=seed, order_id=order_id, condition=condition, checkpoint=checkpoint_validation, independent_recomputation=True,
                test_true_label_logloss=metrics["mean_unsmoothed_nll"], accuracy=metrics["correct_count"]/4500)

def validate_schema_mock(record):
    required={"seed","condition","initial_state_digest","head_digest","order_sha256","supervision_sha256","output_namespace"}
    if set(record)!=required or record["condition"] not in CONDITIONS or record["seed"] not in (167174636,1852328752,1231418446,1461753708):
        raise ValueError("Mock schema")
    if len({record[x] for x in ("initial_state_digest","head_digest","order_sha256","supervision_sha256")}) < 4:
        raise ValueError("Missing identities")
    return True
