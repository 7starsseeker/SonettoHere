@echo off
REM 非 Windows 系统请直接运行: python setup.py ^&^& python main.py

cd /d "%~dp0"

echo ========================================
echo   SonettoHere Startup
echo ========================================
echo.

if not exist "main.py" (
    echo [ERR] 请确保在项目根目录运行此脚本。
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [ERR] 虚拟环境未找到。请先运行 setup.bat 完成初始化。
    echo       或直接执行: python setup.py
    pause
    exit /b 1
)

if not exist "web\node_modules" (
    echo [ERR] 前端依赖未安装。请先运行 setup.bat 完成初始化。
    echo       或直接执行: python setup.py
    pause
    exit /b 1
)

echo [1/3] Starting backend (FastAPI :8000) ...
start "SonettoHere Backend" /d "%~dp0" cmd /k ".venv\Scripts\python main.py web"

echo [2/3] Waiting for backend ...
set "READY=0"
for /L %%i in (1,1,30) do (
    curl -s http://localhost:8000/api/health >nul 2>&1
    if not errorlevel 1 (
        set "READY=1"
        goto :backend_ready
    )
    ping -n 2 127.0.0.1 >nul
)
:backend_ready

if "%READY%"=="0" (
    echo [WARN] Backend startup timed out, continuing ...
) else (
    echo        Backend ready.
)

echo [3/3] Starting frontend (Vite :5173) ...
start "SonettoHere Frontend" /d "%~dp0web" cmd /k "npm run dev"

echo        Waiting for frontend ...
set "READY=0"
for /L %%i in (1,1,20) do (
    curl -s http://localhost:5173 >nul 2>&1
    if not errorlevel 1 (
        set "READY=1"
        goto :frontend_ready
    )
    ping -n 2 127.0.0.1 >nul
)
:frontend_ready

start "" http://localhost:5173

echo.
echo ========================================
echo   All services started
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo ========================================
echo.
echo Close the two server windows to stop.
echo.
pause
