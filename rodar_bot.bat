@echo off
cd /d "C:\Users\lucas\OneDrive\Documentos\promo_bot\promo_bot1"

chcp 65001 > nul
set PYTHONUTF8=1

"C:\Users\lucas\OneDrive\Documentos\promo_bot\promo_bot1\.venv311\Scripts\python.exe" -m scraper.ml_scraper >> logs\execucao.log 2>&1

exit

