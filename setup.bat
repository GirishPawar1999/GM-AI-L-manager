@echo off
setlocal EnableDelayedExpansion

:: Gmail AI Manager - Setup Script for Windows
echo ==========================================
echo   Gmail AI Manager - Setup Script
echo ==========================================
echo.

:: Check Node.js
echo Checking Node.js installation...
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo [OK] Node.js is installed: %NODE_VERSION%

:: Check npm
echo Checking npm installation...
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] npm is not installed
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
echo [OK] npm is installed: %NPM_VERSION%

:: Check Python
echo Checking Python installation...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Python is not installed
    echo AI features require Python. Install from https://python.org/
    set /p CONTINUE="Continue without Python? (y/n): "
    if /i "!CONTINUE!" neq "y" exit /b 1
) else (
    for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo [OK] Python is installed: !PYTHON_VERSION!
    set PYTHON_INSTALLED=1
)

:: Install Node.js dependencies
echo.
echo Installing Node.js dependencies...
call npm install
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Node.js dependencies
    pause
    exit /b 1
)
echo [OK] Node.js dependencies installed

:: Install Python dependencies
if defined PYTHON_INSTALLED (
    echo.
    echo Installing Python dependencies...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [WARNING] Some Python dependencies failed to install
    ) else (
        echo [OK] Python dependencies installed
    )
)

:: Create directories
echo.
echo Creating necessary directories...
if not exist assets mkdir assets
echo [OK] Directories created

:: Check for credentials
echo.
echo Checking for Gmail API credentials...
if exist credentials.json (
    echo [OK] credentials.json found
) else (
    echo [WARNING] credentials.json not found
    echo.
    echo You need to set up Gmail API credentials:
    echo 1. Visit: https://console.cloud.google.com/
    echo 2. Create a project and enable Gmail API
    echo 3. Create OAuth 2.0 credentials
    echo 4. Download and save as credentials.json
    echo.
    echo You can also set this up from the Home page after starting the app.
)

:: Create default config files
echo.
echo Creating default configuration files...

if not exist AI_settings.json (
    (
        echo {
        echo   "emailSummarization": true,
        echo   "aiAutoCategorization": true,
        echo   "smartReplyGeneration": true
        echo }
    ) > AI_settings.json
    echo [OK] Created AI_settings.json
)

if not exist template.json (
    (
        echo {
        echo   "rules": [
        echo     {
        echo       "category": "Work",
        echo       "keywords": ["meeting", "project", "deadline"]
        echo     },
        echo     {
        echo       "category": "Bills",
        echo       "keywords": ["invoice", "payment", "bill"]
        echo     },
        echo     {
        echo       "category": "Shopping",
        echo       "keywords": ["order", "shipped", "delivery"]
        echo     }
        echo   ]
        echo }
    ) > template.json
    echo [OK] Created template.json
)

if not exist .gitignore (
    (
        echo # Sensitive Files
        echo credentials.json
        echo token.json
        echo database.json
        echo.
        echo # Dependencies
        echo node_modules/
        echo package-lock.json
        echo.
        echo # Build
        echo dist/
        echo build/
    ) > .gitignore
    echo [OK] Created .gitignore
)

:: Complete
echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Ensure you have credentials.json in the root directory
echo 2. Run 'npm start' to launch the application
echo 3. Complete the setup in the Home page
echo 4. Authorize Gmail API access
echo.
echo Commands:
echo   npm start       - Start the Electron app
echo   npm run dev     - Start in development mode
echo   npm run server  - Start server only
echo   npm run build   - Build desktop application
echo.
echo For more information, see README.md or QUICKSTART.md
echo.
pause