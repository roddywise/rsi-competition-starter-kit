"""Input-only distribution diagnostics for public train/validation projections."""

import bisect
import json
import math
from pathlib import Path
import statistics


_MAX_JSONL_BYTES = 128 * 1024 * 1024
_EPSILON = 1e-6


def _flatten(value, path=()):
    if isinstance(value, dict):
        result = []
        for key in sorted(value):
            result.extend(_flatten(value[key], path + (("key", str(key)),)))
        return result
    if isinstance(value, list):
        result = []
        for index, child in enumerate(value):
            result.extend(_flatten(child, path + (("index", index),)))
        return result
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"non-numeric public input at {path!r}")
    if not math.isfinite(value):
        raise ValueError(f"non-finite public input at {path!r}")
    encoded_path = json.dumps(
        [{"key": key} if kind == "key" else {"index": key} for kind, key in path],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return [(encoded_path, float(value))]


def _read_input_columns(path, flatten):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"public data file is missing or unsafe: {path}")
    if path.stat().st_size > _MAX_JSONL_BYTES:
        raise ValueError(f"public data file exceeds {_MAX_JSONL_BYTES} bytes")
    columns = None
    schema = None
    rows = 0
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"invalid JSONL row at {path}:{line_number}") from error
            if not isinstance(row, dict) or "inputs" not in row:
                raise ValueError(f"row has no inputs at {path}:{line_number}")
            flattened = flatten(row["inputs"])
            if (
                isinstance(flattened, tuple)
                and len(flattened) == 2
                and isinstance(flattened[0], (list, tuple))
                and isinstance(flattened[1], (list, tuple))
            ):
                flattened = list(zip(flattened[0], flattened[1]))
            if not flattened:
                raise ValueError(f"row has no numeric inputs at {path}:{line_number}")
            row_schema = tuple(item[0] for item in flattened)
            if schema is None:
                schema = row_schema
                columns = [[] for _ in schema]
            elif row_schema != schema:
                raise ValueError(f"feature schema changed at {path}:{line_number}")
            for column, (_, value) in zip(columns, flattened):
                column.append(value)
            rows += 1
    if not rows or columns is None or schema is None:
        raise ValueError(f"public data file contains no rows: {path}")
    return rows, schema, columns


def _quantile(sorted_values, proportion):
    index = round((len(sorted_values) - 1) * proportion)
    return sorted_values[index]


def _histogram(values, edges):
    counts = [0] * (len(edges) + 1)
    for value in values:
        counts[bisect.bisect_left(edges, value)] += 1
    return counts


def _population_stability_index(train_values, validation_values):
    sorted_train = sorted(train_values)
    edges = sorted(
        {
            _quantile(sorted_train, decile / 10)
            for decile in range(1, 10)
        }
    )
    train_counts = _histogram(train_values, edges)
    validation_counts = _histogram(validation_values, edges)
    bins = len(train_counts)
    train_total = len(train_values)
    validation_total = len(validation_values)
    psi = 0.0
    for train_count, validation_count in zip(train_counts, validation_counts):
        train_share = (train_count + _EPSILON) / (
            train_total + _EPSILON * bins
        )
        validation_share = (validation_count + _EPSILON) / (
            validation_total + _EPSILON * bins
        )
        psi += (validation_share - train_share) * math.log(
            validation_share / train_share
        )
    return psi


def diagnose_public_drift(train_path, validation_path, *, flatten=None, top_k=8):
    """Compare public input distributions without reading answers, IDs, or metadata."""
    flatten = _flatten if flatten is None else flatten
    train_rows, train_schema, train_columns = _read_input_columns(
        train_path, flatten
    )
    validation_rows, validation_schema, validation_columns = _read_input_columns(
        validation_path, flatten
    )
    if train_schema != validation_schema:
        raise ValueError("train and validation feature schemas differ")

    features = []
    for index, (feature_path, train_values, validation_values) in enumerate(
        zip(train_schema, train_columns, validation_columns)
    ):
        train_mean = statistics.fmean(train_values)
        validation_mean = statistics.fmean(validation_values)
        train_variance = statistics.pvariance(train_values)
        validation_variance = statistics.pvariance(validation_values)
        pooled_scale = math.sqrt((train_variance + validation_variance) / 2)
        mean_delta = abs(validation_mean - train_mean)
        standardized_mean_difference = (
            mean_delta / pooled_scale
            if pooled_scale > 1e-12
            else (0.0 if mean_delta <= 1e-12 else 999.0)
        )
        psi = _population_stability_index(train_values, validation_values)
        if psi >= 0.25 or standardized_mean_difference >= 1.0:
            severity = "high"
        elif psi >= 0.1 or standardized_mean_difference >= 0.5:
            severity = "moderate"
        else:
            severity = "low"
        features.append(
            {
                "feature_index": index,
                "feature_path": feature_path,
                "psi": psi,
                "standardized_mean_difference": standardized_mean_difference,
                "severity": severity,
            }
        )

    sorted_features = sorted(
        features,
        key=lambda item: max(
            item["psi"] / 0.25,
            item["standardized_mean_difference"],
        ),
        reverse=True,
    )
    high_count = sum(item["severity"] == "high" for item in features)
    moderate_count = sum(
        item["severity"] == "moderate" for item in features
    )
    psi_values = sorted(item["psi"] for item in features)
    median_psi = _quantile(psi_values, 0.5)
    return {
        "method": "train-quantile PSI plus standardized mean difference",
        "scope": "public inputs only; labels, IDs, and metadata are excluded",
        "train_rows": train_rows,
        "validation_rows": validation_rows,
        "summary": {
            "feature_count": len(features),
            "high_drift_features": high_count,
            "moderate_drift_features": moderate_count,
            "low_drift_features": (
                len(features) - high_count - moderate_count
            ),
            "median_psi": median_psi,
            "max_psi": sorted_features[0]["psi"] if sorted_features else 0.0,
        },
        "top_features": sorted_features[: max(0, int(top_k))],
    }
