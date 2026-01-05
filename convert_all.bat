@echo off
REM SVG to PNG Conversion Batch Script
REM Converts all EPC diagrams to PNG format

echo ============================================================
echo EPC Diagram Converter - SVG to PNG
echo ============================================================
echo.

REM Add GTK3 to PATH
echo [1/4] Adding GTK3 Runtime to PATH...
set PATH=C:\Program Files\GTK3-Runtime Win64\bin;%PATH%

REM Check if GTK3 is available
where libcairo-2.dll >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: GTK3 Runtime not found!
    echo Please install GTK3 from: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
    pause
    exit /b 1
)
echo    GTK3 found!

REM Activate virtual environment
echo.
echo [2/4] Activating Python environment...
if not exist "env\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv env
    pause
    exit /b 1
)
call env\Scripts\activate.bat
echo    Environment activated!

REM Extract SVGs from HTML
echo.
echo [3/4] Extracting SVGs from HTML files...
echo    Processing 155 diagram files...
python scripts\convert_svg_to_png.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: SVG extraction failed!
    pause
    exit /b 1
)

REM Convert SVGs to PNG
echo.
echo [4/4] Converting SVGs to PNG...
python scripts\convert_svg_cairosvg.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PNG conversion failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Conversion Complete!
echo ============================================================
echo.
echo Output location: images\converted\
echo.
dir /b images\converted\*.png | find /c ".png" > temp.txt
set /p COUNT=<temp.txt
del temp.txt
echo Total PNG files created: %COUNT%
echo.
echo Files are named: LSFAL11A4PA157987_DiagramName.png
echo.
pause
