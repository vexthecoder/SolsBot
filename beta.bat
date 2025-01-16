@echo off
setlocal enabledelayedexpansion

set "config_path=config.json"

if not exist "%config_path%" (
    echo Config file not found: %config_path%
    exit /b 1
)

for /f "tokens=2 delims=:," %%i in ('findstr /i /c:"\"developer\"" "%config_path%"') do (
    set "developer=%%i"
)

set "developer=!developer: =!"
set "developer=!developer:"=!"

if /i "!developer!"=="true" (
    echo WARNING: Testing features are unstable and might crash the app multiple times. Proceed with caution.
    echo.
    set /p "enable_testing=Developer mode is enabled. Do you want to disable testing features? (y/n): "
    if /i "!enable_testing!"=="y" (
        echo Disabled testing features.
        powershell -Command "(Get-Content %config_path%) -replace '\"developer\": true', '\"developer\": false' | Set-Content %config_path%"
    ) else (
        echo Testing features will remain enabled.
    )
) else (
    echo WARNING: Testing features are unstable and might crash the app multiple times. Proceed with caution.
    echo.
    set /p "disable_testing=Developer mode is disabled. Do you want to enable testing features? (y/n): "
    if /i "!disable_testing!"=="y" (
        echo Enabled testing features.
        powershell -Command "(Get-Content %config_path%) -replace '\"developer\": false', '\"developer\": true' | Set-Content %config_path%"
    ) else (
        echo Testing features will remain disabled.
    )
)

echo Press any key to exit.
pause >nul
exit /b 0