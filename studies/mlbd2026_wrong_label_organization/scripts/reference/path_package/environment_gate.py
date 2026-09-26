"""Installed runtime receipt; read-only, no model construction or forward."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys


PACKAGES = ("torch", "transformers", "tokenizers", "numpy", "sentencepiece", "safetensors")


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def collect(required_nvidia_packages=None):
    import torch
    distributions = {}
    for name in PACKAGES + tuple(sorted(required_nvidia_packages or {})):
        dist = importlib.metadata.distribution(name)
        record = dist.read_text("RECORD")
        distributions[name] = dict(version=dist.version,
                                   record_sha256=None if record is None else hashlib.sha256(record.encode()).hexdigest(),
                                   root=str(dist.locate_file("")))
    binaries = {"torch_C": str(Path(torch._C.__file__).resolve())}
    for key, value in list(binaries.items()):
        binaries[key] = dict(path=value, sha256=sha(value))
    cuda = dict(torch_build=torch.version.cuda, cudnn_build=torch.backends.cudnn.version(),
                available=torch.cuda.is_available(), device_count=torch.cuda.device_count())
    if cuda["available"]:
        cuda["devices"] = [dict(name=torch.cuda.get_device_name(i), capability=list(torch.cuda.get_device_capability(i)))
                           for i in range(cuda["device_count"])]
        result = subprocess.run(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                                capture_output=True, text=True, check=True)
        cuda["driver_versions"] = result.stdout.strip().splitlines()
    return dict(python=sys.version, executable=str(Path(sys.executable).resolve()),
                executable_sha256=sha(sys.executable), system=platform.system(),
                distributions=distributions, binaries=binaries, cuda=cuda)


def validate(receipt, environment_contract):
    required = environment_contract["required"]
    actual = collect(required["required_nvidia_packages"])
    if actual != receipt: raise ValueError("Installed runtime drift")
    if actual["system"] != "Linux" or not actual["python"].startswith("3.11.13"):
        raise ValueError("Python/Linux runtime contract")
    for name, version in required["required_versions"].items():
        if actual["distributions"][name]["version"] != version:
            raise ValueError("Package version: " + name)
    for name, version in required["required_nvidia_packages"].items():
        if actual["distributions"][name]["version"] != version:
            raise ValueError("NVIDIA package version: " + name)
    if actual["cuda"]["torch_build"] != required["required_cuda_build"] or not actual["cuda"]["available"]:
        raise ValueError("CUDA build/visibility")
    if any(x["record_sha256"] is None for x in actual["distributions"].values()):
        raise ValueError("Missing installed RECORD")
    return actual
