import os
from pathlib import Path


_configured_root = os.environ.get("RSI_TASKS_ROOT")
_tasks_root = (
    Path(_configured_root)
    if _configured_root
    else Path(__file__).resolve().parents[3] / "tasks"
)
_task_root = _tasks_root / "A-gas"
if not (_task_root / "baselines" / "__init__.py").is_file():
    raise ImportError(f"A baseline package is unavailable: {_task_root}")
__path__ = [str(_task_root)]
