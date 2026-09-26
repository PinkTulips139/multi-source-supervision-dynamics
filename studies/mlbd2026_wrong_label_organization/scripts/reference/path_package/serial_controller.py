"""Future-only serial controller. No CLI and no execution authorization in this package."""
from pathlib import Path
import json
import os
import subprocess
import sys

from consequence_runtime import read_json, sha, validate_package_manifest
from consequence_validator import validate_fit


def _rng_pair_check(fit, reference):
    a = read_json(fit / "provenance/INITIAL.json")
    b = read_json(reference / "provenance/INITIAL.json")
    if a["rng"] != b["rng"] or a["initial_state"] != b["initial_state"]:
        raise ValueError("Within-seed initial RNG/init mismatch")
    with (fit / "logs/TRAIN.jsonl").open(encoding="utf-8") as fa, (reference / "logs/TRAIN.jsonl").open(encoding="utf-8") as fb:
        for n, (xa, xb) in enumerate(zip(fa, fb), 1):
            ra, rb = json.loads(xa), json.loads(xb)
            for field in ("rng_before_forward", "rng_after_forward"):
                if ra[field] != rb[field]:
                    raise ValueError(f"Same-step RNG stream mismatch at {n}: {field}")
    with (fit / "logs/EPOCH.jsonl").open(encoding="utf-8") as fa, (reference / "logs/EPOCH.jsonl").open(encoding="utf-8") as fb:
        for n, (xa, xb) in enumerate(zip(fa, fb), 1):
            ra, rb = json.loads(xa), json.loads(xb)
            for field in ("state_parameter_names", "no_state_parameter_names"):
                if ra[field] != rb[field]:
                    raise ValueError(f"Adam state coverage mismatch at epoch {n}: {field}")


def execute_once(project_root, package_root, authorization):
    project_root = Path(project_root).resolve()
    package_root = Path(package_root).resolve()
    authorization = Path(authorization).resolve()
    validate_package_manifest(package_root)
    contract = read_json(package_root / "PATH_CONTRACT.json")
    allow = read_json(package_root.parent / "SIXTEEN_FIT_ALLOWLIST.json")
    auth = read_json(authorization)
    if auth.get("stage") != "MLBD2026_OPTIMIZATION_PATH_INTERACTION_EXECUTION_V1" or auth.get("human_authorized") is not True:
        raise ValueError("Formal execution not authorized")
    if auth.get("package_manifest_sha256") != sha(package_root / "PACKAGE_MANIFEST.json") or auth.get("fit_matrix") != contract["fit_matrix"]:
        raise ValueError("Authorization matrix/package mismatch")
    if auth.get("execution_package_manifest_sha256") != sha(package_root.parent / "EXECUTION_PACKAGE_MANIFEST.json"):
        raise ValueError("Execution package manifest mismatch")
    package_meta=read_json(package_root.parent / "EXECUTION_PACKAGE_MANIFEST.json")
    if package_meta["allowlist_sha256"] != sha(package_root.parent / "SIXTEEN_FIT_ALLOWLIST.json") or \
       package_meta["order_matrix_sha256"] != sha(package_root.parent / "ORDER_IDENTITY_MATRIX.json"):
        raise ValueError("Allowlist/order manifest drift")
    if read_json(package_root.parent / "PREFLIGHT_STATUS.json").get("status") != "PASS":
        raise ValueError("Zero-step preflight is not complete PASS")
    if auth.get("preflight_status_sha256") != sha(package_root.parent / "PREFLIGHT_STATUS.json"):
        raise ValueError("Preflight receipt mismatch")
    if len(allow["cells"]) != 16 or len(contract["fit_matrix"]) != 16:
        raise ValueError("Exactly16 allowlist")
    completed = {}
    log_root = project_root / contract["execution_namespace_relative_path"] / "controller_logs"
    if log_root.exists():
        raise FileExistsError("Controller log namespace already exists")
    log_root.mkdir(parents=True, exist_ok=False)
    for cell in allow["cells"]:
        seed, order_id, condition = cell["seed"], cell["order_id"], cell["condition"]
        fit = project_root / cell["output_relative_path"]
        if fit.exists():
            raise FileExistsError("No overwrite/retry: " + str(fit))
        env = os.environ.copy()
        env["PYTHONHASHSEED"] = str(seed)
        env["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
        command = [sys.executable, str(package_root / "fit_entry.py"), str(package_root),
                   str(project_root), str(seed), order_id, condition, str(fit), str(authorization)]
        stem = f"{cell['index']:02d}_SEED_{seed}_{order_id}_{condition}"
        with (log_root / (stem + ".stdout.log")).open("x", encoding="utf-8") as stdout, \
             (log_root / (stem + ".stderr.log")).open("x", encoding="utf-8") as stderr:
            result = subprocess.run(command, env=env, stdout=stdout, stderr=stderr, check=False)
        if result.returncode != 0:
            raise RuntimeError("Fit process failed; inspect formal status and logs; no retry")
        result = validate_fit(fit, package_root, project_root, seed, order_id, condition)
        if result["status"] != "PASS": raise ValueError("Per-fit validator failed")
        references = [path for (s, _, _), path in completed.items() if s == seed]
        for reference in references:
            _rng_pair_check(fit, reference)
        completed[(seed, order_id, condition)] = fit
    if len(completed) != 16:
        raise ValueError("Incomplete 16-cell matrix")
    return completed


if __name__ == "__main__":
    raise SystemExit("No execution CLI; a separate human-authorized stage must call execute_once")
