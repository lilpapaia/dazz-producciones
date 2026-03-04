@echo off
echo ========================================
echo DAZZ CREATIVE - Sistema Gestion Gastos
echo ========================================
echo.

:: Check if virtual environment exists
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
    echo Entorno virtual creado
)

:: Activate virtual environment
echo Activando entorno virtual...
call venv\Scripts\activate.bat

:: Install dependencies
echo Instalando dependencias...
pip install -r requirements.txt --quiet

:: Check if .env exists
if not exist ".env" (
    echo.
    echo Archivo .env no encontrado
    echo Copiando .env.example a .env...
    copy .env.example .env
    echo.
    echo IMPORTANTE: Edita el archivo .env y anade tu ANTHROPIC_API_KEY
    echo    Obten tu API key en: https://console.anthropic.com
    echo.
    pause
)

:: Create uploads directory
if not exist "uploads" mkdir uploads

echo.
echo Todo listo!
echo.
echo Iniciando servidor en http://localhost:8000
echo Documentacion: http://localhost:8000/docs
echo.
echo -------------------------------------------
echo Presiona Ctrl+C para detener el servidor
echo -------------------------------------------
echo.

:: Start server
python main.py
