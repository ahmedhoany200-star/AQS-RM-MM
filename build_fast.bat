@echo off
REM Fast test build: MASTER -> test folder\deploy
cd /d "%~dp0"
python build_fast.py || (echo *** FAILED *** & pause & exit /b 1)
echo.
echo DONE. Upload the whole "test folder\deploy" folder.
pause
