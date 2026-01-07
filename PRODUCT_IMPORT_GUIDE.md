# Product Import Guide - Complete Workflow

## Overview
This guide covers the complete process for importing EPC diagram products into WooCommerce with PNG images and SVG fallback capability.

---

## Prerequisites

### 1. System Requirements (Windows)
- **Python 3.12** with virtual environment at `C:\pythonstuff\wpimport\env`
- **GTK3-Runtime Win64** installed at `C:\Program Files\GTK3-Runtime Win64\bin`
  - Required for Cairo graphics library used by cairosvg
  - Download: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer

### 2. Python Libraries
Install via: `pip install -r requirements.txt`
```
beautifulsoup4
lxml
cairosvg
woocommerce
requests
tqdm
```

### 3. WordPress Setup
- **Site URL**: https://maxusvanparts.co.uk
- **WordPress Credentials**:
  - Username: `developer`
  - Password: `nIbM 6KlW sft3 hQyj OG4P ZYeI`
- **WooCommerce API Keys** (in `config.py`):
  - Consumer Key: `ck_1be77215f05ca7f848ac0ec16a6b68e76ced9302`
  - Consumer Secret: `cs_b2c2be6911c85fe9abc62b4ec5170b9ab746392e`

### 4. Required WordPress Plugin
- **Safe SVG Plugin** - Allows SVG uploads to WordPress media library
  - Used for fallback when PNG conversion fails
  - Plugin sanitizes SVG files for security

---

## Data Structure

### Source Files
```
LSFAL11A4PA157987/
├── air intake system/
├── airbag/
├── antenna/
├── body interior & exterior electronics/
└── [45+ category folders...]
    └── *.html (diagram files with embedded SVGs)
```

### Generated Files
```
images/
├── converted/
│   ├── *.png (converted diagrams - 155 files)
│   └── *.svg (extracted vectors - 155 files)
└── placeholders/
    └── [placeholder images]

data/
├── extracted/
│   └── extracted_data_test.json (product data)
└── checkpoints/
    └── import_checkpoint.json (resume tracking)

logs/
└── [import logs]

conversion_errors.txt (PNG conversion failures - auto-generated)
```

---

## Complete Workflow

### Step 1: Extract Product Data
```powershell
python scripts\extract_data.py
```
**What it does:**
- Parses HTML files from `LSFAL11A4PA157987/` folders
- Extracts product information (SKU, title, category, price)
- Extracts SVG diagrams from HTML
- Saves to `data/extracted/extracted_data_test.json`

### Step 2: Extract SVG Files
```powershell
python extract_all_svgs.py
```
**What it does:**
- Reads all HTML files
- Extracts embedded SVG graphics
- Saves to `images/converted/` with naming format: `LSFAL11A4PA157987_DiagramName.svg`
- Creates 155 SVG files

### Step 3: Convert SVG to PNG (with GTK3)
**CRITICAL: Must set GTK3 path for Cairo library**
```powershell
$env:PATH = "C:\Program Files\GTK3-Runtime Win64\bin;" + $env:PATH; python scripts\convert_svg_cairosvg.py
```

**What it does:**
- Converts all SVG files to PNG format
- Output width: 2000px (maintains aspect ratio)
- Handles SVGs with undefined dimensions by:
  - Extracting viewBox attributes
  - Calculating proper aspect ratios
  - Using explicit output dimensions
- Creates 155 PNG files in `images/converted/`
- Logs failures to `conversion_errors.txt`

**Why GTK3 is needed:**
- `cairosvg` uses Cairo graphics library for rendering
- Cairo on Windows requires GTK3 runtime binaries
- Without GTK3 in PATH, conversions will fail silently or crash

**Script Details:**
- Location: `scripts/convert_svg_cairosvg.py`
- Retry logic for undefined SVG sizes
- Progress bar with tqdm
- Error handling and logging

### Step 4: Import Products to WooCommerce
```powershell
python scripts\import_to_woocommerce.py
```

**What it does:**
- Reads `data/extracted/extracted_data_test.json`
- For each product:
  1. **Find Image** (automatic fallback chain):
     - First checks: `images/converted/LSFAL11A4PA157987_DiagramName.png`
     - If not found: `images/converted/LSFAL11A4PA157987_DiagramName.svg`
     - If not found: Uses placeholder image
  2. **Upload Image** to WordPress media library
  3. **Create WooCommerce Product** with:
     - SKU, title, description
     - Price, category
     - Featured image (PNG/SVG/placeholder)
     - Stock status
- Creates checkpoint file for resume capability
- Logs all operations to `logs/` folder

**Image Fallback Logic** (lines 218-260):
```python
def get_diagram_image_path(diagram_name):
    """Get diagram image with PNG->SVG->placeholder fallback"""
    base_name = f"LSFAL11A4PA157987_{diagram_name}"
    
    # Try PNG first
    png_path = images_dir / 'converted' / f"{base_name}.png"
    if png_path.exists():
        return png_path
    
    # Try SVG fallback
    svg_path = images_dir / 'converted' / f"{base_name}.svg"
    if svg_path.exists():
        return svg_path
    
    # Use placeholder as last resort
    return get_placeholder_image()
```

---

## Configuration Files

### config.py
Contains WordPress and WooCommerce credentials:
```python
WORDPRESS_URL = "https://maxusvanparts.co.uk"
WORDPRESS_USERNAME = "developer"
WORDPRESS_PASSWORD = "nIbM 6KlW sft3 hQyj OG4P ZYeI"

WOOCOMMERCE_URL = "https://maxusvanparts.co.uk"
CONSUMER_KEY = "ck_1be77215f05ca7f848ac0ec16a6b68e76ced9302"
CONSUMER_SECRET = "cs_b2c2be6911c85fe9abc62b4ec5170b9ab746392e"
```

---

## Troubleshooting

### PNG Conversion Issues

**Problem**: Only 3 PNGs created instead of 155
**Solution**: GTK3 not in PATH
```powershell
# Always run with GTK3 in PATH:
$env:PATH = "C:\Program Files\GTK3-Runtime Win64\bin;" + $env:PATH; python scripts\convert_svg_cairosvg.py
```

**Problem**: "SVG size is undefined" errors
**Solution**: Script now handles this automatically by:
- Extracting viewBox dimensions
- Setting explicit output dimensions
- Using square dimensions as fallback

**Problem**: Font warnings during conversion
**Solution**: Already suppressed in script with `redirect_stderr()`

### SVG Upload Issues

**Problem**: SVG files rejected by WordPress
**Solution**: Install Safe SVG plugin
```
WordPress Admin → Plugins → Add New → Search "Safe SVG" → Install & Activate
```

**Problem**: SVG doesn't display in product
**Solution**: Check file was uploaded successfully, verify media ID

### Import Issues

**Problem**: Import stops midway
**Solution**: Uses checkpoint system - just re-run script, it will resume

**Problem**: Images not attaching to products
**Solution**: Verify images exist in `images/converted/` and check naming format

---

## Quick Start (Complete Process)

```powershell
# 1. Activate virtual environment
.\env\Scripts\activate

# 2. Extract data
python scripts\extract_data.py

# 3. Extract SVGs
python extract_all_svgs.py

# 4. Convert to PNG (with GTK3 in PATH)
$env:PATH = "C:\Program Files\GTK3-Runtime Win64\bin;" + $env:PATH; python scripts\convert_svg_cairosvg.py

# 5. Import products
python scripts\import_to_woocommerce.py
```

---

## File Counts Reference

After successful workflow:
- **HTML files**: 155 (source data in `LSFAL11A4PA157987/`)
- **SVG files**: 155 (extracted to `images/converted/`)
- **PNG files**: 155 (converted to `images/converted/`)
- **Products**: 155 (imported to WooCommerce)

---

## Image Priority

The import script uses **PNG-first approach**:
1. **PNG** - Primary format, better WooCommerce compatibility and performance
2. **SVG** - Fallback for conversion failures, scalable vectors
3. **Placeholder** - Last resort if no image found

Current setup: **All 155 products will use PNG images**

---

## Resume Capability

Import creates checkpoint file: `data/checkpoints/import_checkpoint.json`

If import interrupted:
- Re-run script
- Automatically skips already imported products
- Continues from last checkpoint
- Safe to run multiple times

---

## Production Credentials Summary

| Service | URL/Location | Username | Password/Key |
|---------|-------------|----------|--------------|
| WordPress | https://maxusvanparts.co.uk | developer | nIbM 6KlW sft3 hQyj OG4P ZYeI |
| WooCommerce API | https://maxusvanparts.co.uk | Consumer Key | ck_1be77215f05ca7f848ac0ec16a6b68e76ced9302 |
| WooCommerce API | (Secret) | Consumer Secret | cs_b2c2be6911c85fe9abc62b4ec5170b9ab746392e |
| GTK3 Runtime | Local Path | N/A | C:\Program Files\GTK3-Runtime Win64\bin |

---

## Key Scripts Reference

| Script | Purpose | Dependencies |
|--------|---------|--------------|
| `scripts/extract_data.py` | Extract product data from HTML | beautifulsoup4, lxml |
| `extract_all_svgs.py` | Extract SVG graphics from HTML | beautifulsoup4 |
| `scripts/convert_svg_cairosvg.py` | Convert SVG to PNG | cairosvg, GTK3 runtime |
| `scripts/import_to_woocommerce.py` | Import products with images | woocommerce, requests |
| `scripts/upload_placeholders.py` | Upload placeholder images | requests |
| `scripts/cleanup_products.py` | Delete test products | woocommerce |

---

## Notes

- **GTK3 PATH is critical**: Without it, cairosvg cannot render SVGs to PNG
- **Safe SVG plugin required**: For SVG fallback capability
- **Checkpoint system**: Makes import resumable and safe
- **Automatic fallback**: PNG → SVG → Placeholder ensures all products get images
- **Naming convention**: `LSFAL11A4PA157987_DiagramName.ext` for all images
- **Current status**: All 155 PNGs successfully generated, ready for import

---

## Support Commands

```powershell
# Check PNG count
Get-ChildItem "images\converted" -Filter "*.png" | Measure-Object

# Check SVG count
Get-ChildItem "images\converted" -Filter "*.svg" | Measure-Object

# View file counts by type
Get-ChildItem "images\converted" | Group-Object Extension | Select-Object Name, Count

# Check conversion errors
Get-Content conversion_errors.txt

# View import logs
Get-ChildItem logs\ | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content

# Test WordPress connection
python test_wp_auth.py

# Test WooCommerce API
python test_api_connection.py
```

---

**Last Updated**: January 7, 2026  
**Status**: ✅ All 155 PNGs converted successfully, ready for import
