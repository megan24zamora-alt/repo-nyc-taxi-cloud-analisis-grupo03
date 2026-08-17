@echo off
echo ========================================
echo EJECUCION DEL PIPELINE NYC TAXI
echo ========================================

cd /d "%~dp0\.."

set GCS_BUCKET=nyc-taxi-g03-2025

echo Ejecutando pipeline de integracion...
python .\scripts\pipeline_integration.py

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: El pipeline fallo. Revisar mensajes anteriores.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================
echo PIPELINE FINALIZADO CORRECTAMENTE
echo ========================================
echo Datos disponibles en Cloud Storage y BigQuery.
echo Listo para analisis y visualizacion en Power BI.
echo ========================================

pause