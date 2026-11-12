@echo off
setlocal
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m unittest discover -s baselines\tests -v
) else (
  python -m unittest discover -s baselines\tests -v
)
exit /b %ERRORLEVEL%
