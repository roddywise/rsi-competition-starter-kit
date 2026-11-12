import argparse
import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path


def flatten_numeric(value, path=()):
    if isinstance(value, dict):
        out = []
        for key in sorted(value):
            out.extend(flatten_numeric(value[key], path + (str(key),)))
        return out
    if isinstance(value, list):
        out = []
        for index, child in enumerate(value):
            out.extend(flatten_numeric(child, path + (str(index),)))
        return out
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"non-numeric or non-finite input at {path}")
    return [(path, float(value))]


def read_file(path, task):
    path = Path(path)
    raw = path.read_bytes()
    rows = []
    seen_ids = set()
    feature_schema = None
    label_counts = Counter()
    targets = []
    meta_keys = set()
    input_keys = set()

    for line_number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or not {"id", "inputs", "answer"}.issubset(row):
            raise ValueError(f"{path}:{line_number}: expected id, inputs and answer")
        identity = row["id"]
        if not isinstance(identity, str) or not identity or identity in seen_ids:
            raise ValueError(f"{path}:{line_number}: ID is empty or duplicated")
        seen_ids.add(identity)

        flattened = flatten_numeric(row["inputs"])
        schema = tuple(feature_path for feature_path, _ in flattened)
        if feature_schema is None:
            feature_schema = schema
        elif schema != feature_schema:
            raise ValueError(f"{path}:{line_number}: input feature schema changed")

        answer = row["answer"]
        if task == "A":
            if not isinstance(answer, str):
                raise ValueError(f"{path}:{line_number}: task A answer must be a label")
            label_counts[answer] += 1
        else:
            if isinstance(answer, bool) or not isinstance(answer, (int, float)) or not math.isfinite(answer):
                raise ValueError(f"{path}:{line_number}: answer must be a finite number")
            if answer < 0:
                raise ValueError(f"{path}:{line_number}: RUL answer must be nonnegative")
            targets.append(float(answer))

        if isinstance(row["inputs"], dict):
            input_keys.update(row["inputs"].keys())
        if isinstance(row.get("meta"), dict):
            meta_keys.update(row["meta"].keys())
        rows.append(identity)

    result = {
        "file": str(path),
        "rows": len(rows),
        "input_feature_count": len(feature_schema or ()),
        "input_schema_sha256": hashlib.sha256(
            json.dumps(feature_schema or (), ensure_ascii=False).encode("utf-8")
        ).hexdigest(),
        "input_top_level_keys": sorted(input_keys),
        "meta_key_names_only": sorted(meta_keys),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    if task == "A":
        result["label_counts"] = dict(sorted(label_counts.items()))
    else:
        ordered = sorted(targets)
        def quantile(p):
            return ordered[round((len(ordered) - 1) * p)]
        result["target_summary"] = {
            "min": ordered[0],
            "p25": quantile(0.25),
            "median": quantile(0.5),
            "p75": quantile(0.75),
            "max": ordered[-1],
            "mean": statistics.fmean(ordered),
        }
    return result, seen_ids, feature_schema


def main():
    parser = argparse.ArgumentParser(description="Summarize only the explicitly supplied public JSONL files.")
    parser.add_argument("--task", required=True, choices=("A", "B", "C"))
    parser.add_argument("--train", required=True)
    parser.add_argument("--validation", required=True)
    args = parser.parse_args()

    train, train_ids, train_schema = read_file(args.train, args.task)
    validation, validation_ids, validation_schema = read_file(args.validation, args.task)
    overlap = train_ids & validation_ids
    if overlap:
        raise SystemExit(f"ERROR: train/validation IDs overlap ({len(overlap)} rows)")
    if train_schema != validation_schema:
        raise SystemExit("ERROR: train/validation feature schemas differ")

    print(json.dumps({
        "task": args.task,
        "train_validation_ids_overlap": 0,
        "train": train,
        "validation": validation,
        "note": "ID values and meta values are not printed or treated as model features.",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
