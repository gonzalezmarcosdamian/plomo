@echo off
REM Sincroniza las listas que quedaron pendientes por la cuota de Spotify.
REM Lo programa scripts/programar_sync.py con schtasks; se puede correr a mano.
cd /d C:\Users\gonza\Documents\plomo
set LOG=data\sync_pendiente.log
echo ================================= >> %LOG%
echo %DATE% %TIME% >> %LOG%
.venv\Scripts\python.exe scripts\spotify_sync.py 148 901 >> %LOG% 2>&1
.venv\Scripts\python.exe scripts\spotify_validar.py 148 >> %LOG% 2>&1
echo. >> %LOG%
