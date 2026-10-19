@echo off
REM Importa la musica nueva de punta a punta: Descargas -> Rekordbox -> cues.
REM Doble click, o con una lista de Muzpa: importar.cmd data\batch_x.txt
cd /d C:\Users\gonza\Documents\plomo
if "%~1"=="" (
  .venv\Scripts\python.exe scripts\importar.py
) else (
  .venv\Scripts\python.exe scripts\importar.py --batch "%~1"
)
pause
