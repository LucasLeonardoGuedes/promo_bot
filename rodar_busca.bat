@echo off
cd /d "%~dp0"

chcp 65001 > nul
set PYTHONUTF8=1

".\.venv311\Scripts\python.exe" -m scraper.busca_produtos >> logs\busca.log 2>&1

exit
