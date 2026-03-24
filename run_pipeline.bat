@echo off
REM KAIRI-SIO-SATELITAL — Pipeline Runner
REM Ejecutar via Windows Task Scheduler cada 6 dias
REM

cd /d C:\kairi-sio-satelital
call .venv\Scripts\activate.bat
python pipeline_runner.py --dias 7 >> logs\pipeline.log 2>&1
echo Pipeline ejecutado: %date% %time% >> logs\pipeline.log