@echo off
setlocal
cd /d "%~dp0"
where conda >nul 2>nul
if errorlevel 1 (
  echo conda bulunamadi. Anaconda Prompt acip bu klasore gidin ve bu dosyayi oradan calistirin.
  pause
  exit /b 1
)
conda env list | findstr /C:"rayli-agi" >nul
if errorlevel 1 (
  echo rayli-agi ortami yok; yeni ortam olusturuluyor...
  conda env create -f environment.yml
  if errorlevel 1 (
    echo Ortam olusturma basarisiz oldu. Yukaridaki hata metnini saklayin.
    pause
    exit /b 1
  )
) else (
  echo rayli-agi ortami var; environment.yml ile guncelleniyor...
  conda env update -f environment.yml --prune
  if errorlevel 1 (
    echo Ortam guncelleme basarisiz oldu. Yukaridaki hata metnini saklayin.
    pause
    exit /b 1
  )
)
echo Hazir. Simdi: conda activate rayli-agi
echo Ardindan: python run_project.py
pause
