@echo off
TITLE Screenshot Gemini Solver - Launcher
echo ===========================================
echo   SCREENSHOT GEMINI SOLVER LAUNCHER
echo ===========================================
echo.

:: 1. Cek Node.js Dependencies
if not exist "node_modules\" (
    echo [INFO] Menginstall Node.js dependencies...
    call npm install
)

:: 2. Cek Python Dependencies
echo [INFO] Menginstall Python dependencies...
pip install -r requirements.txt

echo.
echo [OK] Dependencies siap.
echo [INFO] Membuka Dashboard GUI...
echo.

:: 3. Jalankan GUI (GUI akan handle wa_bot.js & solver_bot.py)
python gui_app.py

pause
