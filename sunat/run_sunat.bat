@echo off
REM Se ubica en la misma carpeta que sunat_scraper.py (usa %~dp0, asi que
REM funciona sin importar en que ruta este el repo en cada computadora).
cd /d "%~dp0"

if not exist logs mkdir logs

echo ==== Ejecucion: %date% %time% ==== >> logs\run_log.txt
python sunat_scraper.py >> logs\run_log.txt 2>&1
echo. >> logs\run_log.txt

exit
