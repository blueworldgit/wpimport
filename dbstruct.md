# WordPress/WooCommerce Database Structure
*Documentation of product structure, hierarchy, and metadata for Oscar parts import system*

---

## Table of Contents
1. [Product Structure](#product-structure)
2. [SKU Generation](#sku-generation)
3. [Category Hierarchy](#category-hierarchy)
4. [Meta Data Fields](#meta-data-fields)
5. [Product Lifecycle Flags](#product-lifecycle-flags)
6. [Image Management](#image-management)
7. [Price Management](#price-management)
8. [Oscar Database Mapping](#oscar-database-mapping)

---

## Product Structure

### WooCommerce Product Schema

Each product in WooCommerce follows this structure:

```json
{
  "id": 80683,
  "sku": "C00343611-5BF312",
  "name": "RING-DIFFERENTIAL BEARING INNER",
  "type": "simple",
  "status": "publish",
  "categories": [
    {"id": 3590, "name": "Maxus"},
    {"id": 5874, "name": "LSFAM11C6RA144501"},
    {"id": 5876, "name": "Entertainment"},
    {"id": 5959, "name": "Speaker"}
  ],
  "images": [
    {"id": 12345, "src": "https://..."}
  ],
  "description": "Part for LSFAM11C6RA144501 - Entertainment. Usage: RING-DIFFERENTIAL BEARING INNER",
  "short_description": "Callout: 4 | Qty: 8.0",
  "meta_data": [
    {"key": "original_sku", "value": "C00343611"},
    {"key": "oscar_part_id", "value": "37139"},
    {"key": "callout_number", "value": "4"},
    {"key": "unit_qty", "value": "8.0"},
    {"key": "lr", "value": ""},
    {"key": "remark", "value": ""},
    {"key": "nn_note", "value": ""},
    {"key": "vehicle_serial", "value": "LSFAM11C6RA144501"},
    {"key": "oscar_imported", "value": "true"},
    {"key": "images_pending", "value": "true"},
    {"key": "images_updated", "value": "0"},
    {"key": "pricing_updated", "value": "0"}
  ]
}
```

### Field Definitions

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | Integer | WordPress product ID (auto-generated) | `80683` |
| `sku` | String | Unique product SKU (generated, see below) | `C00343611-5BF312` |
| `name` | String | Product name from Oscar `usage_name` | `RING-DIFFERENTIAL BEARING INNER` |
| `type` | String | Product type (always `"simple"`) | `simple` |
| `status` | String | Publication status (always `"publish"`) | `publish` |
| `categories` | Array | Hierarchical category assignment | See Category Hierarchy |
| `images` | Array | Product images (populated by upload script) | `[{"id": 12345, "src": "..."}]` |
| `description` | String | Full product description | `Part for {serial} - {category}. Usage: {name}` |
| `short_description` | String | Brief product summary | `Callout: {number} \| Qty: {quantity}` |
| `meta_data` | Array | Custom metadata (see below) | See Meta Data Fields |

---

## SKU Generation

### Format
```
{ORIGINAL_SKU}-{HASH_SUFFIX}
```

### Generation Algorithm
```python
import hashlib

# Input components
title_prefix = sanitized_product_name[:3].upper()  # First 3 alphanumeric chars
serial_prefix = sanitized_serial[:3].upper()        # First 3 alphanumeric chars
hash_input = f"{original_sku}-{title_prefix}-{serial_prefix}-{oscar_part_id}"

# Generate 6-character hex suffix
sku_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:6].upper()

# Final SKU
unique_sku = f"{original_sku}-{sku_suffix}"
```

### Examples
| Original SKU | Oscar Part ID | Generated SKU | Hash Suffix |
|--------------|---------------|---------------|-------------|
| B00004111 | 37139 | B00004111-BF9845 | BF9845 |
| C00343611 | 80683 | C00343611-5BF312 | 5BF312 |
| C00073046 | 12345 | C00073046-A1B2C3 | A1B2C3 |

### Purpose
- **Uniqueness**: Each part instance (same SKU in different contexts) gets unique identifier
- **Traceability**: Hash includes Oscar part_id for database linkage
- **Collision Resistance**: 6-character hex = 16^6 = 16.7M combinations
- **Context Awareness**: Includes title and serial prefixes for semantic differentiation

---

## Category Hierarchy

### Structure Overview
```
Level 1: Brand (Manufacturer)
├── Level 2: Serial (Vehicle VIN)
    ├── Level 3: Main Category (Parent Title/System)
        └── Level 4: Sub Category (Child Title/Component)
```

### Example Hierarchy
```
Maxus (Brand)
├── LSFAM11C6RA144501 (Serial/VIN)
    ├── Entertainment (Main Category)
    │   ├── Speaker (Sub Category)
    │   ├── Display (Sub Category)
    │   └── Amplifier (Sub Category)
    ├── Engine (Main Category)
    │   ├── Cylinder Head (Sub Category)
    │   ├── Crankshaft (Sub Category)
    │   └── Pistons (Sub Category)
    └── Transmission (Main Category)
        ├── Gearbox (Sub Category)
        └── Clutch (Sub Category)
```

### Category Creation Rules

1. **Serial Isolation**: Each serial gets its own category tree under its brand
2. **Name Sanitization**: 
   - Diagram codes removed (e.g., `JE830A001 - Body` → `Body`)
   - Special characters replaced: `&` → `and`, `/` → `-`
   - Parentheses, commas removed
3. **Parent-Child Relationships**:
   - Brand (parent: 0)
   - Serial (parent: Brand ID)
   - Main Category (parent: Serial ID)
   - Sub Category (parent: Main Category ID)

### Cache Key Format
```
{category_name}__parent_{parent_id}
```

Examples:
- `Maxus__parent_0`
- `LSFAM11C6RA144501__parent_3590`
- `Entertainment__parent_5874`
- `Speaker__parent_5876`

### Special Categories

| Category Name | ID | Purpose |
|---------------|-----|---------|
| `imageupdated` | 4020 | Marks products that have had images successfully uploaded |
| (More special categories may exist) | | |

---

## Meta Data Fields

### Core Oscar Fields

| Meta Key | Type | Source | Description | Example |
|----------|------|--------|-------------|---------|
| `original_sku` | String | `motorpartsdata_part.part_number` | Original Oscar SKU (before hashing) | `B00004111` |
| `oscar_part_id` | String | `motorpartsdata_part.id` | Primary key from Oscar database | `37139` |
| `vehicle_serial` | String | `motorpartsdata_serialnumber.serial` | Vehicle VIN/serial number | `LSFAM11C6RA144501` |

### Part Details

| Meta Key | Type | Source | Description | Example |
|----------|------|--------|-------------|---------|
| `callout_number` | String | `motorpartsdata_part.call_out_order` | Diagram callout/reference number | `4` |
| `unit_qty` | String | `motorpartsdata_part.unit_qty` | Quantity of this part in assembly | `8.0` |
| `lr` | String | `motorpartsdata_part.lr` | Left/Right indicator | `L`, `R`, or empty |
| `remark` | String | `motorpartsdata_part.remark` | Additional notes/remarks | Various |
| `nn_note` | String | `motorpartsdata_part.nn_note` | Special notes | Various |

---

## Product Lifecycle Flags

### Processing State Tracking

| Meta Key | Type | Values | Purpose |
|----------|------|--------|---------|
| `oscar_imported` | String | `"true"` / `"false"` | Indicates product was imported from Oscar |
| `images_pending` | String | `"true"` / `"false"` | Images need to be uploaded |
| `images_updated` | String | `"0"` / `"1"` / timestamp | Tracks image upload status |
| `pricing_updated` | String | `"0"` / `"1"` / timestamp | Tracks price update status |

### Workflow States

```
┌─────────────────┐
│ Product Created │
│ oscar_imported  │
│ = true          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Images Pending  │
│ images_pending  │
│ = true          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Images Uploaded │
│ images_updated  │
│ = 1             │
│ + imageupdated  │
│   category      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Pricing Updated │
│ pricing_updated │
│ = 1             │
└─────────────────┘
```

---

## Image Management

### Image Upload Process

1. **Source**: PNG files in `images/` directory
2. **Matching**: SKU-based filename matching
   - Pattern: `{original_sku}-{product_name}.png`
   - Example: `B00004111-BOLT_SCREW-FRONT_SPK.png`
3. **Deduplication**: Hash-based (SHA256) to avoid re-uploading identical images
4. **Upload**: WordPress REST API `/wp-json/wp/v2/media`
5. **Attachment**: Media ID linked to product via `images` array
6. **Marking**: Product added to `imageupdated` category (ID 4020)

### Filename Conventions

```python
# Sanitization rules
safe_name = product_name.replace(' ', '_')
                        .replace('&', 'and')
                        .replace('/', '-')
                        .replace('\\', '-')
# Remove special chars, keep alphanumeric, underscore, dash
safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '_-')

filename = f"{original_sku}-{safe_name}.png"
```

### Smart Matching

If exact match not found, fallback logic:
1. **Variations**: Try case variations, delimiter swaps
2. **Semantic Matching**: Score filenames based on search terms
3. **Closest Match**: Return best available file for SKU

---

## Price Management

### Pricing Workflow

1. **Source**: Excel file in `pricedata/` directory (one file per SKU)
2. **Lookup**: By `original_sku` meta field
3. **Update**: WooCommerce batch API (up to 100 products per call)
4. **Logging**: SKUs without pricing logged to `nopricefound.txt`

### Excel Format

```
File: pricedata/B00004124.json
{
  "SKU": "B00004124",
  "Price": 1.33
}
```

### Price Application

```python
# Update product
{
  "id": product_id,
  "regular_price": "1.33",
  "meta_data": [
    {"key": "pricing_updated", "value": "1"}
  ]
}
```

---

## Oscar Database Mapping

### Oscar → WordPress Field Mapping

| Oscar Table | Oscar Field | WP Field | WP Location |
|-------------|-------------|----------|-------------|
| `motorpartsdata_part` | `id` | `oscar_part_id` | meta_data |
| `motorpartsdata_part` | `part_number` | `original_sku` | meta_data |
| `motorpartsdata_part` | `usage_name` | `name` | product.name |
| `motorpartsdata_part` | `call_out_order` | `callout_number` | meta_data |
| `motorpartsdata_part` | `unit_qty` | `unit_qty` | meta_data |
| `motorpartsdata_part` | `lr` | `lr` | meta_data |
| `motorpartsdata_part` | `remark` | `remark` | meta_data |
| `motorpartsdata_part` | `nn_note` | `nn_note` | meta_data |
| `motorpartsdata_childtitle` | `title` | Sub Category | categories[3] |
| `motorpartsdata_parenttitle` | `title` | Main Category | categories[2] |
| `motorpartsdata_serialnumber` | `serial` | Serial Category | categories[1] |
| `motorpartsdata_serialnumber` | `serial` | `vehicle_serial` | meta_data |
| `motorpartsdata_serialnumber` | `vehicle_brand` | Brand Category | categories[0] |

### Oscar Database Query

```sql
SELECT 
    p.id as part_id,
    p.part_number as original_sku,
    p.usage_name as name,
    p.call_out_order as callout_number,
    p.unit_qty,
    p.lr,
    p.remark,
    p.nn_note,
    ct.title as sub_category,
    pt.title as main_category,
    sn.vehicle_brand as brand,
    sn.serial
FROM motorpartsdata_part p
JOIN motorpartsdata_childtitle ct ON p.child_title_id = ct.id
JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id
JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
WHERE sn.serial = 'LSFAM11C6RA144501'
ORDER BY p.part_number, p.call_out_order
```

---

## API Endpoints Used

### WooCommerce REST API
- **Products**: `/wp-json/wc/v3/products`
- **Batch Operations**: `/wp-json/wc/v3/products/batch`
- **Categories**: `/wp-json/wc/v3/products/categories`
- **System Status**: `/wp-json/wc/v3/system_status`

### WordPress REST API
- **Media Upload**: `/wp-json/wp/v2/media`
- **User Info**: `/wp-json/wp/v2/users/me`

### Custom Endpoints
- **Products Not in Category**: `/wp-json/custom/v1/products-not-in-category`

---

## Import Process Flow

### 1. Category Creation (`scripts/fast_create_categories.py`)
```
Oscar DB → Extract Category Hierarchy → Create in WooCommerce
   ↓
Brand → Serial → Main Category → Sub Category
```

### 2. Product Import (`scripts/bulk_import_optimizer.py`)
```
Oscar DB → Extract Products → Generate SKU → Map Categories → Batch Create
   ↓
Checkpoint: Track processed SKUs
   ↓
Result: Products with meta_data, pending images/pricing
```

### 3. Image Upload (`scripts/upload_missing_images_optimized.py`)
```
Find Products (NOT in imageupdated) → Match PNG Files → Upload → Attach → Mark Complete
   ↓
Deduplication: Hash-based image caching
   ↓
Result: Products with images, added to imageupdated category
```

### 4. Price Update (`scripts/update_prices_optimized.py`)
```
Load Excel Prices → Fetch Products → Match by original_sku → Batch Update
   ↓
Batch API: 100 products per call
   ↓
Result: Products with regular_price, pricing_updated flag set
```

---

## Performance Optimizations

### Batch Processing
- **Product Creation**: 50 products per batch, 6 concurrent batches
- **Image Upload**: 3 concurrent uploads (API safety)
- **Price Updates**: 100 products per batch API call
- **Category Caching**: Pre-load all categories to avoid repeated API calls

### Checkpointing
- **Location**: `data/checkpoints/bulk_import_checkpoint.json`
- **Data Stored**: 
  - Processed SKUs set
  - Statistics (created, updated, errors)
  - Category cache
  - Timestamp
- **Resume**: Automatic recovery from interruptions

### Connection Management
- **Timeouts**: 120s for uploads (increased from 30s for slow connections)
- **Retry Logic**: 3 retries with exponential backoff (2s, 4s, 8s)
- **Connection Pooling**: requests.Session() for category operations

---

## Troubleshooting Guide

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Duplicate SKU error | Hash collision | Extended to 6 characters (was 5) |
| Category not found | Missing category creation | Run `fast_create_categories.py` first |
| Upload timeout | Slow connection / large images | Increased timeout to 120s + retry logic |
| Price not applied | original_sku mismatch | Check Excel filename matches original_sku |
| Image not found | Filename mismatch | Check PNG filename sanitization rules |

### Verification Queries

```python
# Check product structure
GET /wp-json/wc/v3/products/{id}

# Find products by original SKU
GET /wp-json/wc/v3/products?meta_key=original_sku&meta_value=B00004111

# Check category hierarchy
GET /wp-json/wc/v3/products/categories?parent={parent_id}

# Products without images
GET /wp-json/custom/v1/products-not-in-category?exclude_category=4020
```

---

## Credentials Configuration

### Files
- **WooCommerce API**: `keys.txt` (Consumer Key/Secret)
- **WordPress REST**: `productioncreds.txt` (Username/App Password)
- **Site URL**: `config.py` (WORDPRESS_URL)

### Current Setup
```python
WORDPRESS_URL = "https://maxusvanparts.co.uk"
```

---

*Last Updated: 2026-03-07*
*System Version: 1.0*
