@echo off
REM KAIRI-SIO-SATELITAL — Monitor Precipitacion Horario
REM Task Scheduler: cada 1 hora, todos los dias
REM

cd /d C:\kairi-sio-satelital
call .venv\Scripts\activate.bat
python precip_monitor.py >> logs\precip_monitor.log 2>&1