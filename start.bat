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
echo [INFO] Menjalankan WA Bot dan Solver...
echo.

:: 3. Jalankan WA Bot di window baru
start "WA BOT SERVICE" cmd /k "node wa_bot.js"

:: 4. Tunggu sebentar agar WA Bot siap
timeout /t 5 /nobreak > nul

:: 5. Jalankan Solver di window ini
echo [INFO] Menjalankan Solver Bot...
python solver_bot.py

pause
