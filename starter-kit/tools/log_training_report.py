import argparse
import json
import math
import os
import sys
from pathlib import Path


def force_utf8_console():
    """Keep SwanLab's emoji output from breaking a GBK Windows console."""
    if os.name == "nt":
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as stream:
        return json.load(stream)


def load_history(path):
    records = []
    with Path(path).open("r", encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{number}: expected a JSON object")
            records.append(record)
    return records


def numeric_metrics(prefix, values):
    result = {}
    for name, value in values.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        if math.isfinite(value):
            result[f"{prefix}/{name}"] = float(value)
    return result


def main():
    force_utf8_console()
    parser = argparse.ArgumentParser(
        description="Log a completed public-data training report and history to SwanLab."
    )
    parser.add_argument("--report", required=True, help="training.json from one completed round")
    parser.add_argument("--history", help="history.jsonl; defaults next to training.json")
    parser.add_argument("--project", required=True, help="Shared SwanLab project name")
    parser.add_argument("--workspace", required=True, help="Project owner's or organization's SwanLab username")
    parser.add_argument("--hypothesis", required=True, help="What this round intended to test")
    parser.add_argument("--code-change", required=True, help="Code or parameter change; write 'none' if unchanged")
    parser.add_argument("--decision", required=True, choices=("accepted", "rejected", "skipped"))
    parser.add_argument("--decision-reason", required=True, help="Why this candidate was accepted, rejected, or skipped")
    parser.add_argument("--tokens-used", type=int, default=0)
    parser.add_argument("--labels-used", type=int, default=0)
    parser.add_argument("--platform-trial-used", action="store_true")
    args = parser.parse_args()

    report_path = Path(args.report)
    report = load_json(report_path)
    history_path = Path(args.history) if args.history else report_path.with_name("history.jsonl")
    history = load_history(history_path) if history_path.is_file() else []

    if args.tokens_used < 0 or args.labels_used < 0:
        parser.error("--tokens-used and --labels-used must be nonnegative")
    task = str(report.get("profile", "")).upper()
    if task not in {"A", "B", "C"}:
        parser.error("training.json must identify profile A, B, or C")

    config = {
        "task": task,
        "stage_id": report.get("stage_id"),
        "hypothesis": args.hypothesis,
        "code_change": args.code_change,
        "decision": args.decision,
        "decision_reason": args.decision_reason,
        "parent_checkpoint_sha256": report.get("parent_checkpoint_sha256"),
        "checkpoint_sha256": report.get("checkpoint_sha256"),
        "train_sha256": report.get("train_sha256"),
        "validation_sha256": report.get("validation_sha256"),
        "source_sha256": report.get("source_sha256"),
        "configuration": report.get("configuration"),
        "seed": report.get("seed"),
        "initial_epochs": report.get("initial_epochs"),
        "final_epochs": report.get("final_epochs"),
        "initial_steps": report.get("initial_steps"),
        "final_steps": report.get("final_steps"),
        "train_rows": report.get("train_rows"),
        "validation_rows": report.get("validation_rows"),
        "training_seconds": report.get("training_seconds"),
        "pytrio_tokens_used": args.tokens_used,
        "labels_used": args.labels_used,
        "platform_trial_used": args.platform_trial_used,
        "purpose": report.get("purpose"),
        "official_scoring_ready": report.get("official_scoring_ready"),
    }

    description = (
        f"Task {task}; {args.decision}. "
        f"Hypothesis: {args.hypothesis}. "
        f"Decision: {args.decision_reason}"
    )

    import swanlab

    swanlab.init(
        project=args.project,
        workspace=args.workspace,
        name=str(report.get("stage_id") or f"{task}-unnamed"),
        group=task,
        tags=[f"task-{task}", "public-validation"],
        description=description,
        config=config,
        public=False,
    )

    last_step = 0
    for index, record in enumerate(history, 1):
        metrics = {}
        if isinstance(record.get("loss"), (int, float)) and not isinstance(record["loss"], bool):
            if math.isfinite(record["loss"]):
                metrics["train/loss"] = float(record["loss"])
        validation = record.get("validation")
        if isinstance(validation, dict):
            metrics.update(numeric_metrics("val", validation))
        step = record.get("epoch")
        if not isinstance(step, int) or step < 0:
            step = index
        if metrics:
            swanlab.log(metrics, step=step)
        last_step = max(last_step, step)

    summary = {}
    summary.update(numeric_metrics("val_before", report.get("validation_before", {})))
    summary.update(numeric_metrics("val_after", report.get("validation_after", {})))
    training_seconds = report.get("training_seconds")
    if isinstance(training_seconds, (int, float)) and not isinstance(training_seconds, bool):
        if math.isfinite(training_seconds):
            summary["resource/training_seconds"] = float(training_seconds)
    summary["resource/pytrio_tokens"] = args.tokens_used
    summary["resource/labels"] = args.labels_used
    summary["resource/platform_trial_used"] = int(args.platform_trial_used)
    if summary:
        swanlab.log(summary, step=last_step + 1)

    swanlab.finish()
    print(f"Logged {report.get('stage_id')} to SwanLab project {args.project}.")
    print("Copy the run URL from the SwanLab page and give it to the experiment-records owner.")


if __name__ == "__main__":
    main()
