@echo off
echo ========================================
echo   CRYPTO MONITOR - Lancement
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Verification de Python...
python --version
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe ou pas dans le PATH
    pause
    exit /b 1
)

echo.
echo [2/3] Verification des dependances...
pip show Django >nul 2>&1
if errorlevel 1 (
    echo Installation des dependances...
    pip install -r requirements.txt
)

echo.
echo [3/3] Lancement du serveur Django...
echo.
echo ========================================
echo   Serveur demarre !
echo   Ouvrez votre navigateur a l'adresse:
echo   http://localhost:8000
echo ========================================
echo.
echo Appuyez sur Ctrl+C pour arreter le serveur
echo.

python manage.py runserver

pause

