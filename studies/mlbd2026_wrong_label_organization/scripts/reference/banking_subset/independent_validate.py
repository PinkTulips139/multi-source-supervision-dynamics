from __future__ import annotations

import csv, hashlib, json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
SRC = ROOT / "reports/research/submission_mlbd2026/mlbd2026_banking77_source_execution_v1_20260921T031659Z/formal_source_outputs"

def digest(rows):
    payload = "".join(json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for x in rows)
    return hashlib.sha256(payload.encode()).hexdigest()

def main():
    arrays = []
    for name in ("SOURCE_BERT", "SOURCE_ROBERTA", "SOURCE_DEBERTA"):
        z = np.load(SRC / name / "OFFICIAL_TEST_PREDICTIONS.npz", allow_pickle=False)
        arrays.append((z["canonical_sample_ids"].astype(str), z["truth_ids"].astype(np.int64), z["predicted_ids"].astype(np.int64)))
    ids, y, b = arrays[0]
    r, d = arrays[1][2], arrays[2][2]
    pair_br = (b == r) & (b != y)
    pair_bd = (b == d) & (b != y)
    pair_rd = (r == d) & (r != y)
    include = pair_br | pair_bd | pair_rd
    shared = np.where(pair_br, b, np.where(pair_bd, b, np.where(pair_rd, r, -1)))
    rows = []
    comp = []
    source_names = ("bert", "roberta", "deberta")
    matrix = np.column_stack((b, r, d))
    for i in range(len(ids)):
        base = {"canonical_sample_id": str(ids[i]), "truth_id": int(y[i])}
        if include[i]:
            w = int(shared[i])
            agreeing = "|".join(source_names[j] for j in range(3) if int(matrix[i, j]) == w and w != int(y[i]))
            rows.append({**base, "shared_wrong_id": w, "agreeing_sources": agreeing,
                         "bert_prediction": int(b[i]), "roberta_prediction": int(r[i]), "deberta_prediction": int(d[i])})
        else:
            comp.append(base)
    frozen = json.loads((OUT / "04_LOCAL_SUBSET_AND_GATE.json").read_text(encoding="utf-8"))
    with (OUT / "02_LOCAL_SHARED_FAILURE_MEMBERSHIP.csv").open(newline="", encoding="utf-8") as f:
        formal_rows = [{k: (int(v) if k not in {"canonical_sample_id", "agreeing_sources"} else v) for k, v in row.items()} for row in csv.DictReader(f)]
    checks = {
        "three_way_ids_equal": all(np.array_equal(ids, x[0]) for x in arrays[1:]),
        "three_way_truth_equal": all(np.array_equal(y, x[1]) for x in arrays[1:]),
        "local_rows_exact": rows == formal_rows,
        "local_size_exact": len(rows) == frozen["size"] == 304,
        "local_hash_exact": digest(rows) == frozen["membership_sha256"],
        "complement_size_exact": len(comp) == frozen["complement_size"] == 2776,
        "complement_hash_exact": digest(comp) == frozen["complement_sha256"],
        "partition_exact": len(rows) + len(comp) == 3080 and not ({x["canonical_sample_id"] for x in rows} & {x["canonical_sample_id"] for x in comp}),
        "support_gate": len(rows) >= 20 and len(comp) > 0,
    }
    result = {"status": "PASS" if all(checks.values()) else "FAIL", "implementation": "independent vectorized pair-equality construction", "checks": checks,
              "local_size": len(rows), "local_hash": digest(rows), "complement_size": len(comp), "complement_hash": digest(comp)}
    (OUT / "06_INDEPENDENT_LOCAL_SUBSET_RECOMPUTATION.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if result["status"] != "PASS": raise SystemExit(1)
    print(json.dumps(result, indent=2))

if __name__ == "__main__": main()
