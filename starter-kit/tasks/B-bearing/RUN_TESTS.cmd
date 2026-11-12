@echo off
setlocal
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" run_core_tests.py
) else (
  python run_core_tests.py
)
exit /b %ERRORLEVEL%
