@echo off
setlocal
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m baselines.train --profile A --train public\train.jsonl --validation public\validation.jsonl --from-baseline checkpoint.npz --epochs 2 --output runs\A-round-01 --stage-id A-round-01
) else (
  python -m baselines.train --profile A --train public\train.jsonl --validation public\validation.jsonl --from-baseline checkpoint.npz --epochs 2 --output runs\A-round-01 --stage-id A-round-01
)
exit /b %ERRORLEVEL%
