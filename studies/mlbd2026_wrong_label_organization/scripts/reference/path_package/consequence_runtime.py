"""Identity/routing layer for the frozen XLNet consequence experiment.

This module performs no model construction or inference. Numerical model/loss code is
loaded only by the formal worker from the hash-bound CLEAN-v5 support package.
"""
from pathlib import Path
import csv, gzip, hashlib, json
import numpy as np

CONDITIONS = ("REAL", "CONTROL")
ORDERS = ("PI0", "PI1")
SEEDS = (167174636, 1852328752, 1231418446, 1461753708)

def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def resolve_project_file(project_root, row):
    root = Path(project_root).resolve()
    candidates = row.get("project_relative_paths", [row.get("project_relative_path")])
    present = []
    for candidate in candidates:
        if not candidate: continue
        path = (root / candidate).resolve()
        if not path.is_relative_to(root): raise ValueError("Out-of-root asset: " + row["role"])
        if path.is_file():
            if sha(path) != row["sha256"]: raise ValueError("Asset hash: " + row["role"])
            present.append(path)
    if not present: raise ValueError("Missing asset at every frozen path: " + row["role"])
    return present[0]

def package_contract(package_root):
    package_root = Path(package_root)
    return read_json(package_root / "PATH_CONTRACT.json")

def validate_package_manifest(package_root):
    package_root = Path(package_root)
    manifest = read_json(package_root / "PACKAGE_MANIFEST.json")
    for row in manifest["files"]:
        path = package_root / row["path"]
        if not path.is_file() or sha(path) != row["sha256"]:
            raise ValueError("Package hash: " + row["path"])
    return manifest

def validate_support(package_root, project_root):
    contract = package_contract(package_root)
    support = resolve_project_file(project_root, contract["support_package_manifest"])
    if sha(support) != contract["support_package_manifest"]["sha256"]:
        raise ValueError("Support manifest authority")
    base = support.parent
    manifest = read_json(support)
    for row in manifest["files"]:
        path = base / row["path"]
        if not path.is_file() or sha(path) != row["sha256"]:
            raise ValueError("Support package hash: " + row["path"])
    return base

def load_label_map(path):
    obj = read_json(path)
    labels = obj["labels"]
    if len(labels) != 150 or [x["id"] for x in labels] != list(range(150)):
        raise ValueError("Class mapping")
    return {x["label"]: x["id"] for x in labels}

def load_bindings(package_root, project_root):
    contract = package_contract(package_root)
    paths = {row["role"]: resolve_project_file(project_root, row) for row in contract["assets"]}
    mapping = load_label_map(paths["LABEL_MAP"])
    dataset = read_json(paths["DATASET"])
    if len(dataset["val"]) != 3000 or len(dataset["test"]) != 4500:
        raise ValueError("Dataset split identity")
    dev_ids = [f"clinc150:dev:{i:06d}" for i in range(3000)]
    dev_truth = np.asarray([mapping[x[1]] for x in dataset["val"]], dtype=np.int64)
    conditions = {}
    for condition in CONDITIONS:
        with np.load(paths[condition], allow_pickle=False) as a:
            required = {"example_ids", "truth_ids", "source_predictions", "targets", "source_weights"}
            if not required.issubset(a.files):
                raise ValueError("Supervision schema: " + condition)
            ids = a["example_ids"].tolist(); truth = a["truth_ids"].astype(np.int64, copy=True)
            targets = a["targets"].astype(np.float32, copy=True)
            if ids != dev_ids or not np.array_equal(truth, dev_truth):
                raise ValueError("Supervision identity: " + condition)
            if targets.shape != (3000, 150) or not np.isfinite(targets).all() or (targets < 0).any() or not np.allclose(targets.sum(1), 1, atol=1e-6, rtol=0):
                raise ValueError("Supervision simplex: " + condition)
            source_mean = np.eye(150, dtype=np.float32)[a["source_predictions"]].mean(1)
            if not np.allclose(targets, source_mean, atol=1e-7, rtol=0):
                raise ValueError("Raw target semantics: " + condition)
            conditions[condition] = dict(example_ids=ids, truth_ids=truth, targets=targets)
    test_ids = [f"clinc150:test:{i:06d}" for i in range(4500)]
    test_truth = np.asarray([mapping[x[1]] for x in dataset["test"]], dtype=np.int64)
    with gzip.open(paths["FROZEN129"], "rt", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 129 or len({x["example_id"] for x in rows}) != 129:
        raise ValueError("Frozen129 membership")
    index = {x: i for i, x in enumerate(test_ids)}
    mask = np.zeros(4500, dtype=bool); shared_by_index = {}
    for row in rows:
        i = index.get(row["example_id"])
        if i is None or int(row["truth_id"]) != int(test_truth[i]) or int(row["source_shared_wrong_label_id"]) == int(test_truth[i]):
            raise ValueError("Frozen129 identity")
        if mapping[row["source_shared_wrong_label"]] != int(row["source_shared_wrong_label_id"]):
            raise ValueError("Shared-wrong mapping")
        mask[i] = True; shared_by_index[i] = int(row["source_shared_wrong_label_id"])
    if int(mask.sum()) != 129 or int((~mask).sum()) != 4371:
        raise ValueError("Subset/complement counts")
    return dict(paths=paths, dataset=dataset, mapping=mapping, conditions=conditions,
                test_ids=test_ids, test_truth=test_truth, frozen129_mask=mask,
                shared_wrong=np.asarray([shared_by_index[i] for i in np.flatnonzero(mask)], dtype=np.int64))

def validate_seed_assets(package_root, project_root, order_id):
    if order_id not in ORDERS: raise ValueError("Unfrozen order")
    support = validate_support(package_root, project_root)
    initial = read_json(support / "10_PER_SEED_INITIAL_STATE_INDEX.json")
    order = read_json(support / "11_PER_SEED_ORDER_INDEX.json")
    out = {}
    for seed in SEEDS:
        i = initial["seeds"][str(seed)]; o = order["seeds"][str(seed)]
        if sha(support / i["canonical_head_path"]) != i["canonical_head_file_sha256"] or sha(support / o["path"]) != o["sha256"]:
            raise ValueError("Seed asset hash")
        if order_id == "PI0":
            schedule = read_json(support / o["path"])["epoch_orders"][:20]
        else:
            schedule = read_json(Path(package_root) / "orders" / f"PI1_ORDER_SEED_{seed}.json")["epoch_orders"]
        if len(schedule) != 20 or any(len(x["example_ids"]) != 3000 or len(set(x["example_ids"])) != 3000 for x in schedule):
            raise ValueError("Order asset")
        out[str(seed)] = dict(initial=i, order=o, schedule=schedule)
    return support, out

def fit_matrix():
    return [dict(seed=s, order_id=o, condition=c, epochs=20, optimizer_steps=1880)
            for s in SEEDS for o in ORDERS for c in CONDITIONS]
