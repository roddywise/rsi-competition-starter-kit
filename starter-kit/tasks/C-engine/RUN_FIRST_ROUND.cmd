@echo off
setlocal
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m baselines.train --profile C --train public\train.jsonl --validation public\validation.jsonl --from-baseline checkpoint.npz --epochs 2 --output runs\C-round-01 --stage-id C-round-01
) else (
  python -m baselines.train --profile C --train public\train.jsonl --validation public\validation.jsonl --from-baseline checkpoint.npz --epochs 2 --output runs\C-round-01 --stage-id C-round-01
)
exit /b %ERRORLEVEL%
