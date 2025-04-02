@echo off
cd /d "%~dp0BackEnd/TradeSim Emulator"
pip install -r requirements.txt
start cmd /k "python mt5_api.py"
start cmd /k "python serve_indicators.py"

timeout /t 5

cd /d "%~dp0FrontEnd/TradeSim/tradesim"
start cmd /k "npm run dev"

timeout /t 5


start chrome "http://localhost:5173/"