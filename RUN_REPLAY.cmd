@echo off
cd /d "%~dp0"
set "PYTHONPATH=%~dp0src"
echo Open http://127.0.0.1:4319 in your browser.
python -m edgegrasp_replay.cli serve
pause
