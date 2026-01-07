# Setup on New Machine

## Prerequisites
1. **Python 3.12** installed
2. **GTK3-Runtime Win64** installed at `C:\Program Files\GTK3-Runtime Win64\bin`
   - Download: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
3. **Git** installed

## Initial Setup

### 1. Clone Repository
```powershell
git clone <your-repo-url>
cd wpimport
```

### 2. Create Virtual Environment
```powershell
python -m venv env
.\env\Scripts\activate
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Copy Credentials (NOT in git)
Create these files with your credentials:

**keys.txt:**
```
Consumer key
ck_1be77215f05ca7f848ac0ec16a6b68e76ced9302

Consumer secret
cs_b2c2be6911c85fe9abc62b4ec5170b9ab746392e
```

**productioncreds.txt:**
```
https://maxusvanparts.co.uk/
Consumer key ck_1be77215f05ca7f848ac0ec16a6b68e76ced9302
Consumer secret cs_b2c2be6911c85fe9abc62b4ec5170b9ab746392e	

developer
productintegration
nIbM 6KlW sft3 hQyj OG4P ZYeI
```

**config.py:**
```python
WORDPRESS_URL = "https://maxusvanparts.co.uk"
CURRENCY = "GBP"
DEFAULT_STOCK_QUANTITY = 50
DEFAULT_STOCK_STATUS = "instock"
API_DELAY = 0.5
TEST_PRODUCT_LIMIT = 20
```

### 5. Copy Source HTML Files
Transfer the `LSFAL11A4PA157987/` folder with all HTML diagram files to the project root.

### 6. Run Full Workflow

```powershell
# Activate environment
.\env\Scripts\activate

# Step 1: Extract data
python scripts\extract_data.py

# Step 2: Extract SVGs
python extract_all_svgs.py

# Step 3: Convert SVGs to PNG (requires GTK3 in PATH)
$env:PATH = "C:\Program Files\GTK3-Runtime Win64\bin;" + $env:PATH
python scripts\convert_svg_cairosvg.py

# Step 4: Import to WooCommerce
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
python scripts\import_to_woocommerce.py
```

## Notes

- **GTK3 PATH is critical** for PNG conversion
- The import can be **resumed** if interrupted (uses checkpoint system)
- If you get SKU lookup errors after cleanup, **empty WordPress trash** and run:
  ```powershell
  python fix_lookup_table.py
  ```

## What's in Git vs What's Not

### Included in Git:
- Scripts (`.py` files)
- Documentation (`.md` files)
- Requirements files
- Directory structure

### NOT in Git (generate/copy manually):
- `env/` - Virtual environment (regenerate with `python -m venv env`)
- `keys.txt` - API credentials
- `productioncreds.txt` - WordPress credentials
- `config.py` - Configuration
- `LSFAL11A4PA157987/` - Source HTML files
- `images/converted/` - Generated PNG/SVG files
- `data/extracted/` - Extracted JSON data
- `logs/` - Log files

## Quick Start Summary
```powershell
git clone <repo>
cd wpimport
python -m venv env
.\env\Scripts\activate
pip install -r requirements.txt
# Copy credentials files manually
# Copy LSFAL11A4PA157987 folder manually
# Run workflow steps above
```
