# SVG to PNG Conversion - Windows Setup Guide

Complete instructions for converting EPC diagram SVGs to PNG on Windows.

## Prerequisites

### 1. Python 3.8+
- Download from: https://www.python.org/downloads/
- During installation, check "Add Python to PATH"

### 2. GTK3 Runtime (for Cairo library)
- Download from: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
- Download the latest `.exe` installer (e.g., `gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe`)
- Run the installer with default settings
- It will install to: `C:\Program Files\GTK3-Runtime Win64`

## Setup Instructions

### Step 1: Copy Files
Copy the following folder to your target machine:
```
wpimport/
├── LSFAL11A4PA157987/          (all HTML files)
├── scripts/
│   ├── convert_svg_to_png.py
│   └── convert_svg_cairosvg.py
├── images/
│   └── converted/               (will contain output)
└── requirements.txt
```

### Step 2: Install Python Dependencies
Open PowerShell in the `wpimport` folder and run:

```powershell
# Create virtual environment
python -m venv env

# Activate virtual environment
.\env\Scripts\Activate.ps1

# Install dependencies
pip install beautifulsoup4 lxml cairosvg tqdm
```

### Step 3: Add GTK3 to PATH
In the same PowerShell session:

```powershell
$env:PATH = "C:\Program Files\GTK3-Runtime Win64\bin;" + $env:PATH
```

**Note:** This adds GTK3 only for the current session. To make it permanent:
- Right-click "This PC" → Properties → Advanced System Settings
- Click "Environment Variables"
- Under "System variables", find "Path", click Edit
- Add new entry: `C:\Program Files\GTK3-Runtime Win64\bin`

## Run Conversion

### Option 1: Extract SVGs and Convert to PNG (All-in-One)
This extracts SVGs from all 155 HTML files and converts them to PNG:

```powershell
# Add GTK3 to PATH (if not permanent)
$env:PATH = "C:\Program Files\GTK3-Runtime Win64\bin;" + $env:PATH

# Run extraction (creates SVG files)
python scripts/convert_svg_to_png.py

# Run conversion (SVG → PNG)
python scripts/convert_svg_cairosvg.py
```

### Option 2: Quick Batch Script
Create a file called `convert_all.bat` with this content:

```batch
@echo off
echo Adding GTK3 to PATH...
set PATH=C:\Program Files\GTK3-Runtime Win64\bin;%PATH%

echo Activating Python environment...
call env\Scripts\activate.bat

echo Extracting SVGs from HTML files...
python scripts\convert_svg_to_png.py

echo Converting SVGs to PNG...
python scripts\convert_svg_cairosvg.py

echo.
echo Conversion complete! Check images\converted\ folder
pause
```

Then just double-click `convert_all.bat` to run everything.

## Output

All converted PNG files will be in:
```
images/converted/
```

Files are named: `LSFAL11A4PA157987_DiagramName.png`

Example:
- `LSFAL11A4PA157987_Air_filter.png`
- `LSFAL11A4PA157987_Front_Brakes.png`
- `LSFAL11A4PA157987_Steering_Wheel_and_AirBag.png`

## Performance

- **155 HTML files** (all diagrams for one vehicle serial)
- Extraction: ~1-2 minutes
- Conversion: ~50 seconds
- **Total time: ~3 minutes**

## Troubleshooting

### "cannot load library 'libcairo-2.dll'"
- GTK3 Runtime is not installed or not in PATH
- Solution: Install GTK3 and add to PATH as shown in Step 3

### "No module named 'cairosvg'"
- Dependencies not installed
- Solution: Run `pip install cairosvg` in activated environment

### "Unable to find a suitable font for 'ArialMT'"
- This is just a warning, PNG files are still created successfully
- Can be ignored (fonts will fall back to defaults)

### SVG files created but no PNG files
- Cairo library not found
- Solution: Verify GTK3 is in PATH: `where.exe libcairo-2.dll`

## Transfer Back to Main Machine

After conversion completes, copy the PNG files back:
```
images/converted/*.png  → Copy to main machine
```

Then upload these PNG files to WordPress and link to products.
