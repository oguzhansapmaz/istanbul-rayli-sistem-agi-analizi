@echo off
setlocal
cd /d "%~dp0"
python run_project.py
if errorlevel 1 echo Proje calistirilirken hata olustu; terminal ciktisini saklayin.
pause
