# WooCommerce Product Import — Technical Handover

## Overview

Products are sourced from an **Oscar parts database** (PostgreSQL) and imported into a **WooCommerce** site. The pipeline runs in five sequential steps, each handled by a dedicated script. This document covers the data model, category structure, product structure, image handling, pricing, and how to re-run the process on another WP site.

---

## Source System — Oscar Database

**Connection:**
- Host: `80.95.207.42:5432`
- Database: `parts_store`
- User: `postgres`
- Password: `N0rwich!`

**Key tables:**

| Table | Purpose |
|---|---|
| `motorpartsdata_serialnumber` | Vehicle serials (e.g. `LSH14C4C5NA129710`) and brand |
| `motorpartsdata_parenttitle` | Top-level part categories per serial (e.g. `Brakes`) |
| `motorpartsdata_childtitle` | Sub-categories per parent (e.g. `JE241A001 - Front Brakes`) |
| `motorpartsdata_part` | Individual parts — one row per usage context |

**Important:** A single part number (e.g. `C00186732`) can have **multiple rows** in `motorpartsdata_part` if it appears in different callout positions or diagrams. Each row becomes a **separate WooCommerce product**.

---

## Category Structure in WooCommerce

Categories are a 4-level hierarchy mirroring the Oscar structure:

```
Brand  (e.g. "Maxus")
  └── Serial  (e.g. "LSH14C4C5NA129710")
        └── Parent Category  (e.g. "Brakes")
              └── Child Category  (e.g. "Front Brakes")
```

**Notes on naming:**
- Oscar diagram codes are stripped from child category names. `JE241A001 - Front Brakes` becomes `Front Brakes` in WooCommerce.
- Special characters are sanitised: `&` → `and`, `/` → `-`, parentheses and commas removed.
- Category names are **not unique globally** — "Brakes" exists under every serial. WooCommerce categories are identified by ID, not name.

---

## Product Structure in WooCommerce

Each Oscar `motorpartsdata_part` row becomes one WooCommerce **simple product**.

**SKU format:** `{part_number}-{4-char-hash}`

The hash is the first 4 hex chars of `MD5("{part_number}-{part_id}")` in uppercase. Example:
- Oscar part number: `C00186732`, part_id: `38809` → WP SKU: `C00186732-F211`
- Same part number, different part_id: `38811` → WP SKU: `C00186732-82C3`

This means **one Oscar part number can produce multiple WP products** if it appears in multiple rows.

**Product fields set on import:**

| WP Field | Source |
|---|---|
| `sku` | `{part_number}-{MD5 hash}` |
| `name` | `motorpartsdata_part.usage_name` |
| `type` | `simple` (always) |
| `status` | `publish` |
| `description` | `"Part for {serial} - {main_category}. Usage: {usage_name}"` |
| `short_description` | `"Callout: {call_out_order} | Qty: {unit_qty}"` |
| `categories` | 4 IDs: brand, serial, parent, child |
| `regular_price` | Set separately by price update script |
| `images` | Set separately by image upload script |

**Custom meta_data stored on every product:**

| Meta key | Value |
|---|---|
| `original_sku` | Oscar part number (without hash suffix) |
| `oscar_part_id` | Oscar `motorpartsdata_part.id` |
| `callout_number` | Position on diagram |
| `unit_qty` | Quantity per assembly |
| `lr` | Left/Right designation |
| `remark` | Oscar remark field |
| `nn_note` | Oscar nn_note field |
| `vehicle_serial` | Serial number (e.g. `LSH14C4C5NA129710`) |
| `oscar_imported` | `"true"` |
| `images_pending` | `"true"` (cleared after image upload) |

---

## The Five-Step Import Pipeline

### Step 1 — Convert SVG diagrams to PNG
```
python scripts\convert_svg_to_png.py --serial {SERIAL}
```
Converts Oscar SVG diagram files to PNG format ready for upload. Output goes to `images/converted/`.

PNG filename format: `{part_number}-{USAGE_NAME}.png`
where `USAGE_NAME` has spaces → underscores, `&` → `and`, `/` → `-`, special chars stripped.

---

### Step 2 — Create categories
```
python scripts\fast_create_categories.py --serial {SERIAL}
```
**Script:** `scripts/fast_create_categories.py`

- Connects to Oscar DB and extracts all distinct `(brand, serial, parent_category, child_category)` combinations for the serial.
- Preloads all existing WP categories into a name→ID cache to avoid duplicates.
- Creates categories in 4 passes (brand → serial → parent → child), each pass using async concurrent requests.
- On creation, WP returns the new category ID which is cached immediately for use by the next level.
- Uses WooCommerce REST API: `POST /wp-json/wc/v3/products/categories`

**Known issue:** The category name cache is keyed by name only (`{name: id}`). If the same category name (e.g. "Brakes") exists under multiple serials, only the last WP ID is retained in the cache. This only affects multi-serial runs — for single-serial runs it is correct.

---

### Step 3 — Clear checkpoint and import products
```
python clearloader.py
python scripts\bulk_import_optimizer.py --serial {SERIAL} --batch-size 50
```
**Script:** `scripts/bulk_import_optimizer.py`

`clearloader.py` deletes the checkpoint file so the importer starts fresh.

The importer:
1. Preloads all WP category IDs into `category_cache` (name → id).
2. Queries Oscar DB for all `motorpartsdata_part` rows matching the serial.
3. Generates unique WP SKU per row using MD5 hash of `{part_number}-{part_id}`.
4. Splits products into batches (default 50, max 100 for WC batch API).
5. For each batch, checks if each SKU already exists in WP — if yes, merges categories; if no, creates it.
6. Sends batch create via `POST /wp-json/wc/v3/products/batch`.
7. Saves a checkpoint after every 3 batches to `data/checkpoints/bulk_import_checkpoint.json`.

**Category matching during import:** The importer looks up each Oscar category name against `category_cache`. It tries exact match first, then normalised match (strips diagram codes, lowercases). If any of the 4 categories for a product cannot be found, the product is **skipped** (not created) and logged to the error log.

**Checkpoint file:** `data/checkpoints/bulk_import_checkpoint.json`  
Stores: processed SKUs, category cache, stats. Allows resuming interrupted imports.

**Log files:** Written to `logs/` — one import log, one progress JSON, one error log per run.

---

### Step 4 — Upload images
```
python scripts\upload_missing_images_optimized.py --serial {SERIAL} --force-overwrite
```
**Script:** `scripts/upload_missing_images_optimized.py`

- Fetches all WP products in the serial's category (by WC category ID — fast, indexed lookup).
- For each product, finds the matching PNG in `images/converted/` by matching `original_sku` meta and product name.
- PNG matching strategy (in priority order):
  1. Exact filename match: `{original_sku}-{safe_name}.png`
  2. Variations (upper/lower case, underscore/dash swap)
  3. Semantic fuzzy match (scores words from product name against filename)
  4. Fallback: first PNG for that SKU
- Deduplicates uploads: identical image content (SHA256 hash) is uploaded only once; all products sharing that image reuse the same WordPress media ID.
- Uploads via `POST /wp-json/wp/v2/media` (WordPress media API, requires app password).
- Updates products in batches of 100 via `POST /wp-json/wc/v3/products/batch` with `{"update": [{"id": ..., "images": [{"id": media_id}]}]}`.
- Skips files >2MB.

**Credentials for image upload:** Uses WordPress application password from `productioncreds.txt` (username `developer` + app password), not WooCommerce consumer keys.

**Images directory:** `images/converted/` (relative to workspace root).

---

### Step 5 — Update prices
```
python scripts\update_prices_optimized.py --serial {SERIAL}
```
**Script:** `scripts/update_prices_optimized.py`

- Reads pricing from `PRCJUL25.xlsx` (columns: `Part Number`, `Retail Price` in GBP).
- Fetches all WP products in the serial's category.
- For each product, looks up `original_sku` meta against the Excel `Part Number` column.
- Updates `regular_price` field in batches of 100 via `POST /wp-json/wc/v3/products/batch`.
- SKUs with no Excel entry are logged to `nopricefound.txt`.
- Products already having a price are skipped.

---

## Credentials & Config Files

| File | Contents |
|---|---|
| `config.py` | `WORDPRESS_URL` (e.g. `https://maxusvanparts.co.uk`) |
| `keys.txt` | WooCommerce REST API consumer key + secret (labelled `Consumer key` / `Consumer secret`) |
| `productioncreds.txt` | WordPress app password — line 1: username (`developer`), line 2: app password |
| `PRCJUL25.xlsx` | Pricing spreadsheet — columns `Part Number`, `Retail Price` |

---

## Migrating to a New WordPress Site

To run this on a different WP site or theme:

1. **Install WooCommerce** on the target site.
2. **Update `config.py`:** Change `WORDPRESS_URL` to the new site URL.
3. **Update `keys.txt`:** Generate new WooCommerce REST API keys (Consumer key + Consumer secret) from WP Admin → WooCommerce → Settings → Advanced → REST API.
4. **Update `productioncreds.txt`:** Create a WordPress application password for a user with `edit_posts` capability (WP Admin → Users → Profile → Application Passwords).
5. **Clear all checkpoints and cache:**
   ```
   python clearloader.py
   del data\wp_categories_export.json
   ```
6. **Run the pipeline in order** (Steps 1–5 above) for each serial.

The WC batch API endpoint (`/wp-json/wc/v3/products/batch`) and media upload endpoint (`/wp-json/wp/v2/media`) are standard WordPress/WooCommerce — no custom plugins required.

**WooCommerce batch API limit:** 100 items per request (enforced by WC, not configurable).

---

## Deleting and Re-importing a Serial

Use `delete_serial_complete.py` to wipe all products and categories for a serial before re-importing:

```
python delete_serial_complete.py --serial {SERIAL} --dry-run   # preview
python delete_serial_complete.py --serial {SERIAL}             # execute
```

If the serial category name in WP doesn't match exactly, use `--category-id {ID}` to bypass the name lookup:
```
python delete_serial_complete.py --serial {SERIAL} --category-id {WP_CATEGORY_ID}
```

After delete, clear the checkpoint, then re-run Steps 2–5.

---

## Key Known Issues

| Issue | Detail |
|---|---|
| Duplicate products per part number | Intentional — one WP product per Oscar row. Parts appearing in multiple diagram positions get multiple products with different hash suffixes. |
| Wrong category for a part | Comes from Oscar source data — the import mirrors whatever category Oscar assigns. Fix in Oscar, then delete + re-import. |
| Category name cache collision | When running multi-serial bulk imports, same-named categories (e.g. "Brakes") across serials overwrite each other in the name cache. Single-serial runs are unaffected. |
| Image not found | PNG filename must match `{original_sku}-{usage_name}.png` after sanitisation. Check `close_matches_report.json` after image upload for fuzzy matches. |
| Price not set | Part number not present in `PRCJUL25.xlsx`. Check `nopricefound.txt` for full list. |
