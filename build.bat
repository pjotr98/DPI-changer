@echo off
setlocal
cd /d "%~dp0"

rem Each release build increments 2.0.BUILD automatically.
py -3 build_version.py --bump
if errorlevel 1 goto :fail

py -3 -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name "DPI Changer" --icon "icon.ico" ^
  --version-file "version_info.txt" "dpi_tray_app.py"
if errorlevel 1 goto :fail

echo.
echo PyInstaller finished. Looking for Inno Setup...
set "ISCC="
where ISCC.exe >nul 2>&1
if not errorlevel 1 set "ISCC=ISCC.exe"
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC (
  echo Inno Setup compiler not found. EXE is ready in dist\.
  echo Open installer.iss in Inno Setup to finish the release.
  exit /b 0
)
"%ISCC%" "installer.iss"
if errorlevel 1 goto :fail
echo.
echo Setup complete. See output\.
exit /b 0

:fail
echo Build failed.
exit /b 1
