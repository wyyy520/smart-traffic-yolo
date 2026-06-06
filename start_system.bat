@echo off
cd /d %~dp0
echo Starting Smart Traffic System...
echo.
echo 1. Starting Go Backend...
start "" "C:\Users\13069\go\pkg\mod\golang.org\toolchain@v0.0.1-go1.26.3.windows-amd64\bin\go.exe" run go_backend\main.go
timeout /t 3 /nobreak >nul
echo 2. Opening Main Interface...
start web\html\index.html
echo 3. Opening Dashboard...
start cmd /k streamlit run dashboard.py
echo.
echo System Started!
echo - Main Interface: index.html
echo - Dashboard: http://localhost:8501
pause