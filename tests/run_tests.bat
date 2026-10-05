@echo off
cd /d "%~dp0.."

if exist ".coverage" del /q ".coverage"
if exist "htmlcov" rmdir /s /q "htmlcov"

coverage run --branch --source=. -m pytest test_mbt.py
if errorlevel 1 exit /b 1

coverage report -m
if errorlevel 1 exit /b 1

coverage html
if errorlevel 1 exit /b 1

start "" "htmlcov\index.html"
pause