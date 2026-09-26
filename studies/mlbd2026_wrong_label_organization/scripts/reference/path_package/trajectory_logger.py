"""Read-only scalar/RNG trajectory logger for the frozen XLNet path experiment.

This module never seeds, samples, changes model mode, or calls forward/backward/step.
"""
import hashlib
import json
import math
import random

import numpy as np


HEAD = frozenset((
    "sequence_summary.summary.weight", "sequence_summary.summary.bias",
    "logits_proj.weight", "logits_proj.bias",
))


def _canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def ordered_id_digest(ids):
    return _sha(_canonical(list(ids)))


def rng_snapshot(torch, include_cuda=True):
    version, internal, gauss = random.getstate()
    py = [version, list(internal), None if gauss is None else gauss.hex()]
    name, keys, pos, has_gauss, cached = np.random.get_state()
    np_state = (name.encode("ascii") + b"\0" +
                str(keys.dtype).encode("ascii") + b"\0" +
                _canonical(list(keys.shape)) + b"\0" +
                keys.astype("<u4", copy=False).tobytes() + b"\0" +
                _canonical([int(pos), int(has_gauss), float(cached).hex()]))
    cpu = torch.get_rng_state().detach().cpu().contiguous().numpy()
    out = {
        "python_random": _sha(_canonical(py)),
        "numpy_legacy_random": _sha(np_state),
        "torch_cpu": _sha(b"uint8\0" + _canonical([int(cpu.size)]) + cpu.tobytes()),
        "torch_cuda_all_logical_devices": [],
    }
    if include_cuda:
        for state in torch.cuda.get_rng_state_all():
            arr = state.detach().cpu().contiguous().numpy()
            out["torch_cuda_all_logical_devices"].append(
                _sha(b"uint8\0" + _canonical([int(arr.size)]) + arr.tobytes()))
    return out


def _l2(tensors, torch):
    terms = []
    for tensor in tensors:
        copy = tensor.detach().to(device="cpu", dtype=torch.float64)
        value = float(torch.sum(copy * copy).item())
        if not math.isfinite(value):
            raise ValueError("Nonfinite trajectory tensor norm")
        terms.append(value)
    return math.sqrt(math.fsum(terms)) if terms else None


def epoch_summary(model, optimizer, torch):
    rows = sorted(model.named_parameters(), key=lambda x: x[0])
    parts = {"head": [], "backbone": []}
    for name, parameter in rows:
        parts["head" if name in HEAD else "backbone"].append((name, parameter))
    out = {"parameter_counts": {p: len(rows) for p, rows in parts.items()},
           "no_state_parameter_names": [], "state_parameter_names": []}
    steps = []
    for part, named in parts.items():
        out[part + "_parameter_L2"] = _l2([p for _, p in named], torch)
        first, second = [], []
        for name, p in named:
            state = optimizer.state.get(p)
            if not state:
                out["no_state_parameter_names"].append(name)
                continue
            if "exp_avg" not in state or "exp_avg_sq" not in state or "step" not in state:
                raise ValueError("Partial Adam state: " + name)
            out["state_parameter_names"].append(name)
            first.append(state["exp_avg"])
            second.append(state["exp_avg_sq"])
            step = state["step"]
            steps.append(int(step.item() if hasattr(step, "item") else step))
        out[part + "_Adam_exp_avg_L2"] = _l2(first, torch)
        out[part + "_Adam_exp_avg_sq_L2"] = _l2(second, torch)
    out["optimizer_step_min_max"] = [min(steps), max(steps)] if steps else None
    out["state_parameter_count"] = len(out["state_parameter_names"])
    out["no_state_parameter_count"] = len(out["no_state_parameter_names"])
    return out


def validate_step_row(row):
    required = {"epoch", "batch_index", "global_step", "batch_size",
                "ordered_ID_sha256", "lr_by_group", "loss",
                "preclip_grad_norm", "rng_before_forward", "rng_after_forward"}
    if set(row) != required:
        raise ValueError("Trajectory step schema")
    if not (1 <= row["epoch"] <= 20 and 0 <= row["batch_index"] < 94 and
            row["global_step"] == (row["epoch"] - 1) * 94 + row["batch_index"] + 1):
        raise ValueError("Trajectory indexing")
    if row["batch_size"] != (24 if row["batch_index"] == 93 else 32):
        raise ValueError("Trajectory batch shape")
    if len(row["ordered_ID_sha256"]) != 64 or not all(
            math.isfinite(float(x)) for x in row["lr_by_group"] +
            [row["loss"], row["preclip_grad_norm"]]):
        raise ValueError("Trajectory finite/digest")
    for key in ("rng_before_forward", "rng_after_forward"):
        if set(row[key]) != {"python_random", "numpy_legacy_random",
                             "torch_cpu", "torch_cuda_all_logical_devices"}:
            raise ValueError("Trajectory RNG schema")
    return True
