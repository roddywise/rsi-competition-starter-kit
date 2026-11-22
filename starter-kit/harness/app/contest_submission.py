"""Restricted A/B/C callbacks for the RSI contest Harness SDK."""

import importlib
import json
import math
import os
from pathlib import Path

from drift import diagnose_public_drift


TASKS = ("classification", "regression")

_TASK_DIRECTORIES = {"A": "A-gas", "B": "B-bearing", "C": "C-engine"}
_TASK_TYPES = {
    "A": ("classification", "macro_f1", "higher"),
    "B": ("regression", "rmse", "lower"),
    "C": ("regression", "rmse", "lower"),
}
_ACTIONS = {
    "A": {
        "learning_rate": (0.001, 0.003, 0.005),
        "batch_size": (64, 128, 256),
        "epochs": (1, 2, 3),
    },
    "B": {
        "learning_rate": (0.001, 0.003, 0.005),
        "batch_size": (64, 128, 256),
        "epochs": (1, 2, 3),
    },
    "C": {
        "learning_rate": (0.001, 0.002, 0.003),
        "batch_size": (128, 256, 512),
        "epochs": (1, 2, 3),
    },
}
_MAX_CANDIDATE_BYTES = 64 * 1024 * 1024
_MAX_CANDIDATE_FILES = 64


def _load_task_module(dataset_key, module_name):
    if dataset_key not in _TASK_DIRECTORIES:
        raise ValueError(f"unsupported dataset key: {dataset_key!r}")
    if module_name not in {"train", "model", "data", "predict"}:
        raise ValueError("unsupported baseline module")
    return importlib.import_module(
        f"task_{dataset_key.lower()}.baselines.{module_name}"
    )


def _profile_config(dataset_key, train_module):
    config_path = Path(train_module.ROOT) / "configs" / f"{dataset_key}.json"
    with config_path.open("r", encoding="utf-8") as stream:
        config = json.load(stream)
    if config.get("profile") != dataset_key:
        raise ValueError("baseline profile does not match dataset")
    return config


def _fallback_action(dataset_key, config):
    return {
        "hypothesis": "模型响应无效，使用基线学习率和批大小执行 1 epoch 安全回退。",
        "learning_rate": config["learning_rate"],
        "batch_size": config["batch_size"],
        "epochs": 1,
        "model_action_fallback": True,
    }


def _parse_action(dataset_key, response_text, config):
    fallback = _fallback_action(dataset_key, config)
    if not isinstance(response_text, str):
        return fallback
    try:
        action = json.loads(response_text)
    except (json.JSONDecodeError, TypeError):
        return fallback
    if not isinstance(action, dict) or set(action) != {
        "hypothesis",
        "learning_rate",
        "batch_size",
        "epochs",
    }:
        return fallback
    hypothesis = action["hypothesis"]
    learning_rate = action["learning_rate"]
    batch_size = action["batch_size"]
    epochs = action["epochs"]
    allowlist = _ACTIONS[dataset_key]
    if (
        not isinstance(hypothesis, str)
        or not hypothesis.strip()
        or len(hypothesis.encode("utf-8")) > 4000
        or isinstance(learning_rate, bool)
        or not isinstance(learning_rate, (int, float))
        or not math.isfinite(learning_rate)
        or learning_rate not in allowlist["learning_rate"]
        or type(batch_size) is not int
        or batch_size not in allowlist["batch_size"]
        or type(epochs) is not int
        or epochs not in allowlist["epochs"]
    ):
        return fallback
    return {
        "hypothesis": hypothesis.strip(),
        "learning_rate": float(learning_rate),
        "batch_size": batch_size,
        "epochs": epochs,
        "model_action_fallback": False,
    }


def _metric_value(container, metric):
    if not isinstance(container, dict):
        return None
    candidate = container.get(metric)
    if (
        isinstance(candidate, bool)
        or not isinstance(candidate, (int, float))
        or not math.isfinite(candidate)
    ):
        return None
    return float(candidate)


def _metric_containers(record):
    if not isinstance(record, dict):
        return
    yield record
    for name in ("metrics", "validation", "validation_after"):
        value = record.get(name)
        if isinstance(value, dict):
            yield value
            nested = value.get("metrics")
            if isinstance(nested, dict):
                yield nested
    for name in ("summary", "result"):
        value = record.get(name)
        if isinstance(value, dict):
            yield value
            nested = value.get("metrics")
            if isinstance(nested, dict):
                yield nested
    nested_record = record.get("record")
    if isinstance(nested_record, dict):
        yield from _metric_containers(nested_record)


def _record_metric(record, metric):
    for container in _metric_containers(record):
        value = _metric_value(container, metric)
        if value is not None:
            return value
    return None


def _parent_metric(history, metric, parent_artifact_id, current_validation=None):
    value = _record_metric(current_validation, metric)
    if value is not None:
        return value
    matched = []
    for record in history:
        value = _record_metric(record, metric)
        if value is None:
            continue
        artifact_id = record.get("artifact_id") or record.get("selected_artifact_id")
        nested = record.get("record")
        if isinstance(nested, dict):
            artifact_id = artifact_id or nested.get("selected_artifact_id")
        if artifact_id == parent_artifact_id:
            matched.append(value)
    return matched[-1] if matched else None


def _history_configuration(record, dataset_key):
    if not isinstance(record, dict):
        return {}
    configuration = record.get("configuration")
    if not isinstance(configuration, dict):
        nested = record.get("record")
        configuration = (
            nested.get("configuration")
            if isinstance(nested, dict)
            else None
        )
    if not isinstance(configuration, dict):
        return {}
    allowed = _ACTIONS[dataset_key]
    result = {}
    learning_rate = configuration.get("learning_rate")
    if (
        not isinstance(learning_rate, bool)
        and isinstance(learning_rate, (int, float))
        and math.isfinite(learning_rate)
        and learning_rate in allowed["learning_rate"]
    ):
        result["learning_rate"] = float(learning_rate)
    batch_size = configuration.get("batch_size")
    if type(batch_size) is int and batch_size in allowed["batch_size"]:
        result["batch_size"] = batch_size
    epochs = configuration.get("epochs")
    if type(epochs) is int and epochs in allowed["epochs"]:
        result["epochs"] = epochs
    return result


def _history_for_model(history, metric, dataset_key):
    result = []
    for record in history[-10:]:
        if not isinstance(record, dict):
            continue
        value = _record_metric(record, metric)
        if value is None:
            continue
        round_index = record.get("round_index")
        if type(round_index) is not int:
            round_index = None
        item = {"round_index": round_index, metric: value}
        configuration = _history_configuration(record, dataset_key)
        if configuration:
            item["configuration"] = configuration
        result.append(item)
    return result


def _candidate_metric(submitted, metric):
    if not isinstance(submitted, dict):
        return None
    return _record_metric(submitted.get("summary"), metric)


def _candidate_size(candidate, limits):
    if candidate.is_symlink() or not candidate.is_dir():
        raise ValueError("candidate directory is invalid")
    limits = limits if isinstance(limits, dict) else {}
    max_bytes = _MAX_CANDIDATE_BYTES
    max_files = _MAX_CANDIDATE_FILES
    for key in ("artifact_bytes", "candidate_upload_bytes_per_round"):
        value = limits.get(key)
        if type(value) is int and value > 0:
            max_bytes = min(max_bytes, value)
    files = []
    total = 0
    for path in sorted(candidate.rglob("*")):
        if path.is_symlink():
            raise ValueError("candidate contains a symlink")
        if not path.is_file():
            continue
        files.append(path)
        total += path.stat().st_size
        if len(files) > max_files or total > max_bytes:
            raise ValueError("candidate exceeds the conservative artifact limit")
    if not files:
        raise ValueError("candidate is empty")


def _format_metric(value):
    return f"{value:.6g}"


def _select_candidate(
    submitted,
    history,
    metric,
    direction,
    parent_artifact_id,
    current_validation=None,
):
    candidate_id = submitted.get("artifact_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise ValueError("platform returned no candidate artifact ID")
    candidate_score = _candidate_metric(submitted, metric)
    if candidate_score is None:
        return (
            parent_artifact_id,
            f"平台候选摘要没有有效的 {metric}，保留父模型。",
        )
    parent_score = _parent_metric(
        history, metric, parent_artifact_id, current_validation
    )
    if parent_score is None:
        return (
            candidate_id,
            f"无可比父指标；选择首个有效测量候选，不与父模型比较。"
            f"平台 {metric}={_format_metric(candidate_score)}。",
        )
    improved = (
        candidate_score > parent_score
        if direction == "higher"
        else candidate_score < parent_score
    )
    if improved:
        return (
            candidate_id,
            f"平台 {metric} 从 {_format_metric(parent_score)} "
            f"变为 {_format_metric(candidate_score)}，严格改善，接受候选。",
        )
    comparison = "不高于" if direction == "higher" else "不低于"
    return (
        parent_artifact_id,
        f"候选 {metric}={_format_metric(candidate_score)} {comparison} "
        f"父模型 {_format_metric(parent_score)}，回滚到父模型。",
    )


def train(rnd):
    dataset_key = rnd.dataset_key
    if dataset_key not in _TASK_DIRECTORIES:
        raise ValueError(f"unsupported dataset key: {dataset_key!r}")
    expected_task, metric, direction = _TASK_TYPES[dataset_key]
    task_contract = rnd.task
    if (
        not isinstance(task_contract, dict)
        or task_contract.get("dataset_key", dataset_key) != dataset_key
        or task_contract.get("task") != expected_task
        or task_contract.get("metric") != metric
        or task_contract.get("metric_direction") != direction
    ):
        raise ValueError("platform task contract does not match dataset")
    train_path = getattr(rnd.data, "train_path", None)
    validation_path = getattr(rnd.data, "validation_path", None)
    if not train_path or not validation_path:
        raise ValueError("platform public data paths are missing")

    train_module = _load_task_module(dataset_key, "train")
    data_module = _load_task_module(dataset_key, "data")
    config = _profile_config(dataset_key, train_module)
    history = list(rnd.history())
    drift_report = diagnose_public_drift(
        train_path,
        validation_path,
        flatten=data_module.flatten,
    )
    drift_for_model = {
        "summary": drift_report["summary"],
        "top_features": [
            {
                "feature_index": item["feature_index"],
                "psi": item["psi"],
                "standardized_mean_difference": item[
                    "standardized_mean_difference"
                ],
                "severity": item["severity"],
            }
            for item in drift_report["top_features"]
        ],
    }
    prompt_payload = {
        "dataset_key": dataset_key,
        "task": expected_task,
        "primary_metric": metric,
        "metric_direction": direction,
        "recent_official_measurements": _history_for_model(
            history, metric, dataset_key
        ),
        "public_input_drift": drift_for_model,
        "allowed_values": _ACTIONS[dataset_key],
        "response_schema": {
            "hypothesis": "short non-empty text",
            "learning_rate": "one allowed number",
            "batch_size": "one allowed integer",
            "epochs": "one allowed integer",
        },
    }
    prompt = (
        "Choose one bounded hyperparameter experiment using only the allowed values. "
        "Do not propose code, commands, paths, or additional fields. "
        "Return exactly one JSON object matching response_schema.\n"
        + json.dumps(prompt_payload, ensure_ascii=False, allow_nan=False)
    )
    max_tokens = getattr(rnd, "max_output_tokens", 128)
    if type(max_tokens) is not int or max_tokens < 1:
        raise ValueError("invalid platform output token limit")
    receipt = rnd.model(
        [{"role": "user", "content": prompt}],
        max_tokens=min(256, max_tokens),
        temperature=0,
    )
    action = _parse_action(dataset_key, getattr(receipt, "text", ""), config)

    checkpoint_paths = getattr(rnd.parent, "descriptor", {}).get(
        "checkpoint_paths"
    )
    if not isinstance(checkpoint_paths, list) or len(checkpoint_paths) != 1:
        raise ValueError("parent must declare exactly one checkpoint")
    parent_checkpoint = Path(rnd.parent.path(checkpoint_paths[0]))
    if parent_checkpoint.is_symlink() or not parent_checkpoint.is_file():
        raise ValueError("verified parent checkpoint is not a regular file")

    workspace = Path(os.environ.get("CONTEST_WORK", "/workspace"))
    if workspace.is_symlink():
        raise ValueError("workspace must not be a symlink")
    workspace.mkdir(parents=True, exist_ok=True)
    round_index = getattr(rnd, "round_index", 0)
    if type(round_index) is not int or round_index < 1:
        raise ValueError("invalid platform round index")
    candidate = workspace / f"candidate-{dataset_key.lower()}-{round_index:03d}"
    if candidate.exists() or candidate.is_symlink():
        raise ValueError("candidate path already exists")

    stage_id = f"{dataset_key}-round-{round_index:02d}"
    report = train_module.train_run(
        dataset_key,
        train_path,
        validation_path,
        candidate,
        resume=parent_checkpoint,
        epochs=action["epochs"],
        learning_rate=action["learning_rate"],
        batch_size=action["batch_size"],
        stage_id=stage_id,
    )
    with (candidate / "drift_report.json").open(
        "x", encoding="utf-8"
    ) as stream:
        json.dump(drift_report, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write("\n")
    _candidate_size(candidate, getattr(rnd, "limits", {}))

    hypothesis = action["hypothesis"]
    change_summary = (
        "受限超参数试验："
        f"epochs={action['epochs']}, "
        f"learning_rate={action['learning_rate']}, "
        f"batch_size={action['batch_size']}"
    )
    configuration = {
        "dataset_key": dataset_key,
        "task": expected_task,
        "metric": metric,
        "learning_rate": action["learning_rate"],
        "batch_size": action["batch_size"],
        "epochs": action["epochs"],
        "model_action_fallback": action["model_action_fallback"],
        "parent_checkpoint_sha256": report.get("parent_checkpoint_sha256"),
        "public_input_drift": drift_report["summary"],
    }
    submitted = rnd.submit_candidate(
        candidate,
        hypothesis=hypothesis,
        change_summary=change_summary,
        configuration=configuration,
        seed=report["seed"],
        checkpoint_paths=["checkpoint.npz"],
        code_paths=[],
        predict_argv=["python3", "/app/harness.py", "predict"],
    )
    frame = getattr(rnd, "frame", {})
    current_validation = (
        frame.get("current_validation") if isinstance(frame, dict) else None
    )
    selected_id, reason = _select_candidate(
        submitted,
        history,
        metric,
        direction,
        rnd.parent.artifact_id,
        current_validation,
    )
    history_ids = [
        record["id"]
        for record in history
        if isinstance(record, dict)
        and isinstance(record.get("id"), str)
        and record["id"]
    ]
    return rnd.finish(
        selected_artifact_id=selected_id,
        hypothesis=hypothesis,
        change_summary=change_summary,
        reason=reason,
        configuration=configuration,
        seed=report["seed"],
        history_ids=history_ids,
        model_call_ids=list(rnd.call_ids),
    )


def _checkpoint_path(model_dir):
    configured = os.environ.get("CONTEST_ARTIFACT_PATH")
    path = Path(configured) if configured else Path(model_dir) / "checkpoint.npz"
    if path.is_symlink() or not path.is_file():
        raise ValueError("selected checkpoint is missing or unsafe")
    return path


def predict(sample, model_dir):
    checkpoint = _checkpoint_path(model_dir)
    requested_key = getattr(sample, "dataset_key", None)
    environment_key = os.environ.get("CONTEST_DATASET_KEY")
    if (
        requested_key is not None
        and environment_key is not None
        and requested_key != environment_key
    ):
        raise ValueError("prediction dataset context mismatch")
    requested_key = requested_key or environment_key
    probe = _load_task_module("A", "model").Model.load(checkpoint)
    dataset_key = probe.meta.get("profile")
    if dataset_key not in _TASK_DIRECTORIES:
        raise ValueError("checkpoint has no supported dataset profile")
    if requested_key is not None and requested_key != dataset_key:
        raise ValueError("prediction dataset does not match checkpoint")
    model = _load_task_module(dataset_key, "model").Model.load(checkpoint)
    if getattr(sample, "task", None) != model.meta.get("task"):
        raise ValueError("prediction task does not match checkpoint")
    if dataset_key == "B" and model.meta.get("target_unit") != "minutes":
        raise ValueError("bearing checkpoint target unit must be minutes")
    predict_module = _load_task_module(dataset_key, "predict")
    return predict_module.predict(model, sample.inputs)
