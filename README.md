# WooCommerce Import System

A comprehensive system for importing vehicle parts data from Oscar database to WooCommerce, with optimized async processing and smart category management.

## Table of Contents

- [Overview](#overview)
- [Category Management](#category-management)
- [Category Verification](#category-verification)
- [Product Import](#product-import)
- [Troubleshooting](#troubleshooting)
- [Database Issues](#database-issues)
- [Logging and Monitoring](#logging-and-monitoring)

---

## Overview

This system imports automotive parts data from PostgreSQL Oscar database into WooCommerce. The process involves:

1. **Category Creation**: Build hierarchical category structure (Brand → Serial → Parent → Child)
2. **Product Import**: Import products with proper category assignments and SKU conflict resolution
3. **Resume/Checkpoint**: Automatic checkpoint saving for large imports

---

## Category Management

### Fast Category Creator (Recommended)

**Script**: `scripts/fast_create_categories.py`

High-performance async category creation with 10x speed improvement over sequential processing.

#### Usage

```bash
# Create categories for specific serial
python scripts/fast_create_categories.py --serial LSFAL11A4PA157987

# Create categories for specific serial with custom concurrency
python scripts/fast_create_categories.py --serial LSFAL11A4PA157987 --concurrent 15

# Create all categories (no serial filter)
python scripts/fast_create_categories.py
```

#### Features

- **Async Processing**: Creates categories concurrently with configurable request limits
- **Duplicate Detection**: Automatically detects existing categories to avoid duplicates
- **Smart Hierarchy**: Creates proper 4-level structure (Brand → Serial → Parent → Child)
- **Error Handling**: Comprehensive error logging with retry logic
- **Performance**: ~10x faster than sequential creation

#### Example Output

```
🚀 Fast Async Oscar Category Creator
🔗 Concurrent requests: 10
🚗 Serial filter: LSFAL11A4PA157987

📂 Preloading existing WordPress categories...
✅ Cached 205 existing categories

🔍 Extracting category hierarchy...
   📋 Filtering by serial: LSFAL11A4PA157987
📊 Found:
   🏢 Brands: 1
   🚗 Serials: 1
   📂 Parent categories: 47
   📄 Child categories: 310

🚀 Creating Category Hierarchy in WooCommerce (Async)
📁 Level 1: Brand categories...
🚗 Level 2: Serial categories...
📂 Level 3: Parent categories...
📄 Level 4: Child categories...

🎉 ASYNC CATEGORY CREATION COMPLETED
⏱️  Total time: 45.2s
✅ Categories created: 204
🔍 Categories found existing: 1
❌ Errors: 0
📈 Processing rate: 4.5 categories/second
```

### Standard Category Creator

**Script**: `scripts/create_categories.py`

Original sequential category creator (slower but more conservative).

```bash
python scripts/create_categories.py --serial LSFAL11A4PA157987
```

---

## Category Verification

### WordPress Category Count Verification

**Script**: `verify_wp_count.py`

Verifies that WordPress has the correct number of categories after creation by breaking down the hierarchy and comparing against expected counts.

#### Usage

```bash
python verify_wp_count.py
```

#### Expected Results

For a typical serial (e.g., LSFAL11A4PA157987):
- **1 Brand** (Maxus)
- **1 Serial** (LSFAL11A4PA157987)  
- **47 Parent categories** (main category groups)
- **150 Child categories** (specific part categories)
- **1 Uncategorized** (WordPress default)
- **Total: 200 categories**

#### Troubleshooting Category Counts

**Problem**: Getting fewer child categories than expected (e.g., 150 instead of 155)

**Root Cause**: Self-referencing categories in Oscar database where category appears as both parent and child with the same sanitized name.

**Examples of problematic categories**:
- `'JE650A001 - Front Lamp'` (child) → parent: `'Front Lamp'` 
- After sanitization both become: `'Front Lamp'`

**Solution**: These are filtered out as invalid data. The category exists as a parent, so products will still map correctly.

### Missing Categories Diagnosis

**Script**: `check_missing_children.py`

Compares Oscar database categories against WordPress to find discrepancies.

```bash
python check_missing_children.py
```

If categories are missing, they're likely self-referencing entries that should be filtered out.

---

## Product Import

### Bulk Import Optimizer (Main Import Script)

**Script**: `scripts/bulk_import_optimizer.py`

High-performance bulk product importer with async processing, SKU conflict resolution, and smart category matching.

#### Usage

```bash
# Import products for specific serial with limits
python scripts/bulk_import_optimizer.py --serial LSFAL11A4PA157987 --limit-per-serial 50 --batch-size 10

# Import all products for a serial
python scripts/bulk_import_optimizer.py --serial LSFAL11A4PA157987

# Import all serials (production run)
python scripts/bulk_import_optimizer.py
```

#### Key Features

##### 1. SKU Conflict Resolution

**Important**: The system **patches existing products** instead of creating duplicates.

- **Existing SKU Detection**: Checks WordPress for existing SKUs before import
- **Category Merging**: Adds new categories to existing products without replacing
- **Price Updates**: Updates pricing on existing products
- **No Duplicates**: Never creates duplicate SKUs

```
Example:
- SKU "B00003507" already exists with categories: [Brakes]
- New import wants to add: [Power Generation, Engine Management]
- Result: SKU now has categories: [Brakes, Power Generation, Engine Management]
```

##### 2. Multi-Application Product Names

**Important**: Products with concatenated names (separated by " | ") are **correct and intentional**.

**Example**: `SKU B00004955`
```
Product Name: "BOLT-INSTRUMENT PANEL CROSS MEMBER BRACKET | BOLT-INSTRUMENT PANEL CROSS MEMBER TO CROSS MEMBER BRACKET | BOLT/SCREW-COMPRESSOR INLET TUBE | BOLT/SCREW-COMPRESSOR OUTLET TUBE"

Oscar Database: Same SKU has 4 different usage names
- Usage 1: "BOLT-INSTRUMENT PANEL CROSS MEMBER BRACKET" 
- Usage 2: "BOLT-INSTRUMENT PANEL CROSS MEMBER TO CROSS MEMBER BRACKET"
- Usage 3: "BOLT/SCREW-COMPRESSOR INLET TUBE"  
- Usage 4: "BOLT/SCREW-COMPRESSOR OUTLET TUBE"

WordPress Result: 1 product with multiple applications shown in name
```

**Why This Is Correct**:
- ✅ **1 SKU = 1 Physical Part** = **1 WordPress Product**  
- ✅ **Multiple Usage Names** = **Different Applications** = **Shown in concatenated name**
- ✅ **Multiple Categories** = **All application areas** where part is used
- ✅ **Customer Value**: Shows all possible uses for the same part

**SQL Logic**: `STRING_AGG(DISTINCT p.usage_name, ' | ' ORDER BY p.usage_name)`

##### 3. Smart Category Search

The system uses intelligent category matching with multiple fallback strategies:

1. **Exact Match**: Direct category name lookup
2. **Normalized Search**: Strips special characters, converts to lowercase
3. **Partial Match**: Finds categories containing the search term
4. **Fuzzy Match**: Uses similarity scoring for close matches
5. **Skip Logic**: Products with missing categories are logged but skipped

##### 3. Async Batch Processing

- **Concurrent Requests**: Configurable concurrent request limits (default: 10)
- **Batch Operations**: Groups products into batches for efficient processing
- **Progress Tracking**: Real-time progress bars with detailed statistics

#### Cache Management

**Important**: The script uses persistent category caching for performance.

##### Cache Issue and Solution

**Problem**: Category cache can become stale and show "Multiple matches" warnings.

**Symptoms**:
```
📂 Preloading category mappings...
✅ Cached 356 unique categories  # ← Should match WordPress count
⚠️ Multiple matches for 'Maxus', using ID 1227
```

**Solution - Clear Cache**:

```bash
# Delete the checkpoint file to clear cache
del data\checkpoints\bulk_import_checkpoint.json

# Next run will rebuild cache from current WordPress state
python scripts/bulk_import_optimizer.py --serial LSFAL11A4PA157987 --limit-per-serial 1
```

**Verification**: After clearing, cache count should match WordPress category count.

##### 4. Resume/Checkpoint System

**Automatic Checkpointing**:
- **SKU Tracking**: Remembers processed SKUs to avoid reprocessing
- **Progress Persistence**: Saves progress every batch
- **Resume Capability**: Automatically resumes from last checkpoint

**Checkpoint Location**: `data/checkpoints/bulk_import_checkpoint.json`

**Manual Reset**:
```bash
# Clear checkpoint to restart import
del data\checkpoints\bulk_import_checkpoint.json
```

#### Example Output

```
🎯 SERIAL-BY-SERIAL BULK IMPORT STARTED
📋 Processing single serial: LSFAL11A4PA157987
📂 Preloading category mappings...
✅ Cached 205 categories

🚗 Processing Serial 1/1: LSFAL11A4PA157987
🔍 Extracting unique SKUs from serial: LSFAL11A4PA157987
✅ Found 1479 unique SKUs for serial LSFAL11A4PA157987
   ⏭️ Skipping 13 already processed SKUs
   📦 Importing 1466 products from LSFAL11A4PA157987

🚀 Starting ASYNC import of 1466 products
   Batch size: 10, Concurrent batches: 10
   Created 147 batches

Processing async batches: 100%|████████████| 147/147 [05:23<00:00, 0.45it/s]

✅ Async import completed
   Products created: 1200
   Products updated: 266
   Products failed: 0

🎉 SERIAL-BY-SERIAL IMPORT COMPLETED
   Total time: 324.7s
   Serials processed: 1
   Products created: 1466
   Processing rate: 4.5 products/second
```

---

## Troubleshooting

### Common Issues

#### 1. "Multiple matches for category" Warnings

**Cause**: Stale category cache
**Solution**: Clear checkpoint file (see [Cache Management](#cache-management))

#### 2. "Missing categories" Errors

**Cause**: Categories haven't been created in WordPress
**Solution**: Run category creator first:
```bash
python scripts/fast_create_categories.py --serial LSFAL11A4PA157987
```

#### 3. Import Stuck/Slow

**Cause**: Network issues or large batch sizes
**Solutions**:
- Reduce batch size: `--batch-size 5`
- Reduce concurrent requests: `--concurrent 5`
- Check network connection

#### 4. SKU Conflicts

**Expected Behavior**: System patches existing products instead of creating duplicates
**Verification**: Check logs for "Product updated" vs "Product created" messages

### Cache Debugging

```bash
# Check current WordPress category count
python check_categories.py

# Compare with cache count in import log
python scripts/bulk_import_optimizer.py --serial LSFAL11A4PA157987 --limit-per-serial 1
# Look for: "✅ Cached X unique categories"
# Should match WordPress count
```

---

## Logging and Monitoring

### Log Files

All scripts generate comprehensive logs in the `logs/` directory:

#### Bulk Import Logs

**Location**: `logs/bulk_import_YYYYMMDD_HHMMSS.log`

**Contents**:
- Detailed import progress
- SKU conflict resolutions
- Category mapping results
- Error details with context

**Example**:
```
[2026-01-13 20:43:27] INFO: 📍 Matched 'Body Interior & Exterior Electronics' -> 'Body Interior and Exterior Electronics'
[2026-01-13 20:43:27] INFO: Creating 5 new products, updated 2 existing
[2026-01-13 20:43:28] SUCCESS: Batch 1 SUCCESS: Created 5, Updated 2 products
```

#### Progress Tracking

**Location**: `logs/bulk_progress_YYYYMMDD_HHMMSS.json`

**Contents**: Real-time progress data for monitoring large imports

#### Error Logs

**Location**: `logs/bulk_errors_YYYYMMDD_HHMMSS.log`

**Contents**: Detailed error information for debugging

### Checkpoint Files

**Location**: `data/checkpoints/`

- `bulk_import_checkpoint.json`: Main import progress and cache
- `import_checkpoint.json`: Legacy checkpoint file

### Monitoring Scripts

#### Category Analysis
```bash
# Check WordPress category structure
python scripts/analyze_wp_categories.py

# Check specific serial categories
python scripts/analyze_wp_categories.py | grep LSFAL11A4PA157987
```

#### Oscar Database Reports
```bash
# Generate comprehensive Oscar database report
python scripts/oscar_reporting.py

# Filter by specific serial
python scripts/oscar_reporting.py --serial LSFAL11A4PA157987

# Output to custom file
python scripts/oscar_reporting.py --output my_report.txt
```

---

## Best Practices

### 1. Always Create Categories First

```bash
# Step 1: Create categories
python scripts/fast_create_categories.py --serial LSFAL11A4PA157987

# Step 2: Import products
python scripts/bulk_import_optimizer.py --serial LSFAL11A4PA157987
```

### 2. Start Small for Testing

```bash
# Test with limited products first
python scripts/bulk_import_optimizer.py --serial LSFAL11A4PA157987 --limit-per-serial 10 --batch-size 3
```

### 3. Monitor Performance

- Check log files for errors
- Monitor processing rates (target: 3-5 products/second)
- Adjust batch sizes based on network performance

### 4. Clear Cache When Needed

- After deleting/recreating categories
- When seeing "Multiple matches" warnings
- After WordPress structure changes

---

## Database Issues

### Self-Referencing Categories Problem

**Issue**: Oscar database contains invalid category relationships where a category appears as both parent and child after sanitization.

**Example**:
```
Parent: 'Front Lamp' 
Child: 'JE650A001 - Front Lamp'
After sanitization: 'Front Lamp' → 'Front Lamp' (self-reference)
```

**Affected Categories** (LSFAL11A4PA157987):
- Antenna
- Body Interior and Exterior Electronics  
- Front Lamp
- Rear Lamp
- Rear View Mirror

#### Resolution

**WordPress Script**: `scripts/fast_create_categories.py` now filters out self-referencing children:
```python
# Only add to children if it's not a self-reference
if child != parent:
    children[child] = parent
```

**Oscar Reporting**: `scripts/oscar_reporting.py` filters out invalid relationships:
```sql
WHERE REGEXP_REPLACE(pt.title, '^[A-Z]{2}[0-9]+[A-Z]?[0-9]+\s*-\s*', '') 
   != REGEXP_REPLACE(ct.title, '^[A-Z]{2}[0-9]+[A-Z]?[0-9]+\s*-\s*', '')
```

#### Impact

- **WordPress**: Creates 47 parents + 150 children (filters out 5 invalid children)
- **Oscar Report**: Shows 42 parents + 150 children (filters out entire relationships)
- **Products**: No impact - all categories products need exist in WordPress

### Database Duplicates

**Issue**: All child categories have duplicate entries in Oscar database (original + migrated data).

**Evidence**: 
- 155 unique categories × 2 = 310 total records
- Low IDs (≤200): Original data
- High IDs (>200): Duplicate migration data

**Impact**: Minimal - scripts handle duplicates correctly by using the first match found.

---

## Script Reference

| Script | Purpose | Key Options |
|--------|---------|-------------|
| `fast_create_categories.py` | Create category hierarchy (async) | `--serial`, `--concurrent` |
| `bulk_import_optimizer.py` | Import products (main script) | `--serial`, `--limit-per-serial`, `--batch-size` |
| `create_categories.py` | Create categories (sequential) | `--serial` |
| `oscar_reporting.py` | Generate Oscar database reports | `--serial`, `--output` |
| `verify_wp_count.py` | Verify WordPress category counts | No options |
| `check_missing_children.py` | Find missing categories | No options |
| `debug_hierarchy.py` | Debug category hierarchy issues | No options |
| `analyze_wp_categories.py` | Analyze WordPress categories | None |
| `check_categories.py` | Quick category count check | None |