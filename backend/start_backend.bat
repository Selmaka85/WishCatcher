@echo off
REM Script de pornire backend pentru Windows
echo ========================================
echo Starting WishCatcher Backend Server
echo ========================================
echo.

REM Verifică dacă ești în directorul corect
if not exist "app\main.py" (
    echo ERROR: Nu esti in directorul backend!
    echo Navigheaza la: cd backend
    pause
    exit /b 1
)

REM Pornește serverul
echo Starting FastAPI server on http://localhost:8000
echo.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
