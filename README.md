# WooCommerce EPC Import Project

Automated import of Electronic Parts Catalog (EPC) data into WordPress/WooCommerce.

## 📁 Project Structure

```
wpimport/
├── LSFAL11A4PA157987/          # Source HTML data (vehicle serial)
├── scripts/                     # Python scripts
│   ├── create_placeholders.py  # Generate placeholder images
│   ├── extract_data.py         # Extract data from HTML files
│   └── import_to_woocommerce.py # Import to WooCommerce
├── data/
│   ├── extracted/              # Extracted JSON data
│   └── checkpoints/            # Import checkpoints
├── images/
│   ├── placeholders/           # Placeholder images
│   └── converted/              # SVG→PNG converted images (Phase 5)
├── logs/                       # Log files
├── config.py                   # Configuration file
├── keys.txt                    # WooCommerce API keys
└── requirements.txt            # Python dependencies
```

## 🚀 Quick Start Guide

### Step 1: Configuration

1. **Update WordPress URL** in `config.py`:
   ```python
   WORDPRESS_URL = "http://localhost/wordpress"  # Change this!
   ```

2. **Verify API Keys** in `keys.txt` (already set up)

### Step 2: Install Dependencies

Already installed, but if needed:
```powershell
pip install -r requirements.txt
```

### Step 3: Run the Import (TEST MODE - 20 Products)

#### 3a. Extract Data from HTML
```powershell
C:/pythonstuff/wpimport/env/Scripts/python.exe scripts/extract_data.py
```
- Parses HTML files
- Excludes hidden parts (class="dn")
- Detects Left/Right variations
- Creates `data/extracted/extracted_data_test.json`

#### 3b. Import to WooCommerce
```powershell
C:/pythonstuff/wpimport/env/Scripts/python.exe scripts/import_to_woocommerce.py
```
- Tests API connection
- Uploads placeholder images
- Creates categories hierarchy
- Imports 20 test products
- Sets £0.00 GBP pricing
- Sets 50 units in stock

### Step 4: Verify in WordPress

1. Go to WordPress Admin → Products
2. Check that products were created
3. Verify categories: Maxus → LSFAL11A4PA157987 → [category] → [diagram]
4. Check product details:
   - Placeholder images assigned
   - Price: £0.00
   - Stock: 50 units (in stock)
   - Custom attributes (callout number, remark, etc.)

## 📊 Import Features

### Data Extraction
- ✅ Excludes hidden parts (class="dn")
- ✅ Extracts SKU from `data-part-id`
- ✅ Detects Left/Right variations
- ✅ Captures remarks and callout numbers
- ✅ Deduplicates by SKU

### Product Creation
- ✅ Simple products (no orientation)
- ✅ Variable products (Left/Right variations)
- ✅ Placeholder images (General, Left, Right)
- ✅ Category hierarchy (4 levels)
- ✅ Custom attributes:
  - Callout Number
  - Orientation
  - Remark
  - Diagram File
  - Quantity per Vehicle

### Pricing & Stock
- ✅ Default price: £0.00 GBP (placeholder)
- ✅ Default stock: 50 units
- ✅ Status: In Stock
- ✅ Stock management enabled

## 🔄 Full Import (All Products)

Once you've tested with 20 products and verified everything works:

### 1. Extract All Data
Edit `scripts/extract_data.py` line 341:
```python
# Change this:
data = extractor.extract_category_data(data_dir, test_limit=20)

# To this (remove test_limit):
data = extractor.extract_category_data(data_dir)
```

Run extraction:
```powershell
C:/pythonstuff/wpimport/env/Scripts/python.exe scripts/extract_data.py
```

### 2. Import All Products
Update `scripts/import_to_woocommerce.py` to use the full data file:
```python
# Change:
data_file = base_dir / 'data' / 'extracted' / 'extracted_data_test.json'

# To:
data_file = base_dir / 'data' / 'extracted' / 'extracted_data.json'
```

Run import:
```powershell
C:/pythonstuff/wpimport/env/Scripts/python.exe scripts/import_to_woocommerce.py
```

## 📝 Current Status

### ✅ Completed (Phase 1-3)
- [x] Project structure created
- [x] Placeholder images generated
- [x] Data extraction script (with variation detection)
- [x] WooCommerce import script
- [x] Test mode (20 products)
- [x] Checkpoint system (resumable)
- [x] Progress bars and logging
- [x] GBP currency support

### ⏳ To Do (Phase 4-5)
- [ ] Full import (all products)
- [ ] Pricing update script (from Excel)
- [ ] SVG→PNG conversion script
- [ ] Image replacement script

## 📈 Expected Results

### Test Import (20 products)
- **Products**: ~20 simple products
- **Categories**: 2-3 categories created
- **Images**: 3 placeholder images uploaded
- **Time**: ~2-3 minutes

### Full Import (estimated)
- **Products**: ~3,000-5,000 products
- **Categories**: ~50-60 categories
- **Time**: ~2-3 hours (with API rate limiting)

## 🐛 Troubleshooting

### API Connection Failed
- Check WordPress URL in `config.py`
- Verify WooCommerce is installed
- Regenerate API keys if needed

### No Placeholder Images
- Run `scripts/create_placeholders.py` first
- Check `images/placeholders/` folder

### Duplicate SKU Errors
- Normal if re-running import
- Check `data/checkpoints/` for progress
- Products are skipped if SKU exists

### Import Stops/Crashes
- Check `logs/` folder for errors
- Import is resumable via checkpoints
- Re-run import script to continue

## 📞 Support Files

- **Extracted Data**: `data/extracted/extracted_data_test.json`
- **Checkpoints**: `data/checkpoints/import_checkpoint.json`
- **Logs**: `logs/` (future feature)
- **Test Results**: See terminal output

## 🔧 Configuration Options

Edit `config.py` to customize:
- WordPress URL
- Currency (GBP)
- Default stock quantity (50)
- API rate limiting (0.5s delay)
- Test product limit (20)

---

**Ready to import?** Update `config.py` and run the scripts! 🚀
