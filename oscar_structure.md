# Oscar Database Structure
*Documentation of the Oscar PostgreSQL database schema and relationships*

---

## Table of Contents
1. [Connection Information](#connection-information)
2. [Database Overview](#database-overview)
3. [Core Tables](#core-tables)
4. [Table Relationships](#table-relationships)
5. [Common Query Patterns](#common-query-patterns)
6. [Field Mappings to WordPress](#field-mappings-to-wordpress)

---

## Connection Information

### Database Credentials
```python
DB_CONFIG = {
    'dbname': 'parts_store',
    'user': 'postgres',
    'password': 'N0rwich!',
    'host': '80.95.207.42',
    'port': '5432'
}
```

### Connection Method
```python
import psycopg2
from psycopg2.extras import RealDictCursor

# Basic connection
conn = psycopg2.connect(**DB_CONFIG)

# Connection with dictionary cursor (recommended)
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor(cursor_factory=RealDictCursor)
```

---

## Database Overview

### Database Type
- **Engine**: PostgreSQL
- **Name**: `parts_store`
- **Schema**: `public`
- **Purpose**: Store vehicle parts catalog with hierarchical categorization

### Key Tables (5 main tables)
1. `motorpartsdata_serialnumber` - Vehicle identification (VIN/Serial numbers)
2. `motorpartsdata_parenttitle` - Main category/system level
3. `motorpartsdata_childtitle` - Sub-category/diagram level (contains SVG diagrams)
4. `motorpartsdata_part` - Individual parts/products
5. `motorpartsdata_pricingdata` - Pricing information

---

## Core Tables

### 1. motorpartsdata_serialnumber
**Purpose**: Stores vehicle identification information (VIN/Serial numbers)

| Column Name | Data Type | Description | Example |
|------------|-----------|-------------|---------|
| `id` | integer | Primary key | `1` |
| `serial` | varchar | Vehicle VIN/Serial number | `LSFAL11A4PA157987` |
| `vehicle_brand` | varchar | Manufacturer/Brand name | `Maxus` |

**Relationships**:
- One-to-many with `motorpartsdata_parenttitle` (one serial has many parent categories)

**Sample Query**:
```sql
SELECT * FROM motorpartsdata_serialnumber 
WHERE serial = 'LSFAL11A4PA157987';
```

---

### 2. motorpartsdata_parenttitle
**Purpose**: Main category level (e.g., "Engine", "Transmission", "Body")

| Column Name | Data Type | Description | Example |
|------------|-----------|-------------|---------|
| `id` | integer | Primary key | `45` |
| `title` | varchar | Category name | `Entertainment` |
| `serial_number_id` | integer | Foreign key to serialnumber | `1` |

**Relationships**:
- Many-to-one with `motorpartsdata_serialnumber` (via `serial_number_id`)
- One-to-many with `motorpartsdata_childtitle` (one parent has many children)

**Sample Query**:
```sql
SELECT pt.*, sn.serial, sn.vehicle_brand
FROM motorpartsdata_parenttitle pt
JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
WHERE sn.serial = 'LSFAL11A4PA157987';
```

---

### 3. motorpartsdata_childtitle
**Purpose**: Sub-category/diagram level with SVG diagram data

| Column Name | Data Type | Description | Example |
|------------|-----------|-------------|---------|
| `id` | integer | Primary key | `123` |
| `title` | varchar | Sub-category name | `Speaker` |
| `parent_id` | integer | Foreign key to parenttitle | `45` |
| `svg_code` | text | SVG diagram XML/HTML content | `<svg>...</svg>` |

**Relationships**:
- Many-to-one with `motorpartsdata_parenttitle` (via `parent_id`)
- One-to-many with `motorpartsdata_part` (one diagram has many parts)

**Sample Query**:
```sql
SELECT ct.*, pt.title as parent_title
FROM motorpartsdata_childtitle ct
JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id
WHERE pt.id = 45;
```

**Note**: The `svg_code` field contains HTML/SVG diagram content that can be:
- Extracted to standalone files
- Converted to PNG images
- Used for visual part identification

---

### 4. motorpartsdata_part
**Purpose**: Individual part/product records with detailed specifications

| Column Name | Data Type | Description | Example |
|------------|-----------|-------------|---------|
| `id` | integer | Primary key (unique part instance) | `37139` |
| `part_number` | varchar | Original manufacturer SKU | `B00004111` |
| `usage_name` | varchar | Part description/name | `RING-DIFFERENTIAL BEARING INNER` |
| `child_title_id` | integer | Foreign key to childtitle (diagram) | `123` |
| `call_out_order` | varchar | Callout number on diagram | `4` |
| `unit_qty` | decimal | Quantity in assembly | `8.0` |
| `lr` | varchar | Left/Right indicator | `L`, `R`, or empty |
| `remark` | text | Additional notes/remarks | Various |
| `nn_note` | text | Special notes | Various |

**Relationships**:
- Many-to-one with `motorpartsdata_childtitle` (via `child_title_id`)
- One-to-one with `motorpartsdata_pricingdata` (via part number lookup)

**Key Fields Explained**:
- **part_number**: Original SKU from manufacturer (can have duplicates across contexts)
- **usage_name**: Human-readable part description
- **call_out_order**: Reference number on the diagram (links part to visual representation)
- **unit_qty**: How many of this part are needed (e.g., 8 bolts)
- **lr**: Left or Right side indicator (useful for symmetrical parts)

**Sample Query**:
```sql
SELECT p.*, ct.title as diagram_title
FROM motorpartsdata_part p
JOIN motorpartsdata_childtitle ct ON p.child_title_id = ct.id
WHERE p.part_number = 'B00004111';
```

---

### 5. motorpartsdata_pricingdata
**Purpose**: Pricing and stock information for parts

| Column Name | Data Type | Description | Example |
|------------|-----------|-------------|---------|
| `id` | integer | Primary key | `1` |
| `part_number_id` | integer | Foreign key to part | `37139` |
| `list_price` | decimal | Retail price | `1.33` |
| `stock_available` | integer | Quantity in stock | `50` |

**Relationships**:
- Many-to-one with `motorpartsdata_part` (via `part_number_id`)

**Sample Query**:
```sql
SELECT pd.*, p.part_number, p.usage_name
FROM motorpartsdata_pricingdata pd
JOIN motorpartsdata_part p ON pd.part_number_id = p.id
WHERE pd.list_price IS NOT NULL
LIMIT 10;
```

---

## Table Relationships

### Entity Relationship Diagram
```
┌──────────────────────────┐
│  serialnumber            │
│  ──────────────          │
│  id (PK)                 │
│  serial                  │
│  vehicle_brand           │
└────────┬─────────────────┘
         │ 1:N
         ▼
┌──────────────────────────┐
│  parenttitle             │
│  ──────────────          │
│  id (PK)                 │
│  title                   │
│  serial_number_id (FK)   │
└────────┬─────────────────┘
         │ 1:N
         ▼
┌──────────────────────────┐
│  childtitle              │
│  ──────────────          │
│  id (PK)                 │
│  title                   │
│  parent_id (FK)          │
│  svg_code                │
└────────┬─────────────────┘
         │ 1:N
         ▼
┌──────────────────────────┐        ┌──────────────────────────┐
│  part                    │        │  pricingdata             │
│  ──────────────          │ 1:1    │  ──────────────          │
│  id (PK)                 │◄───────┤  id (PK)                 │
│  part_number             │        │  part_number_id (FK)     │
│  usage_name              │        │  list_price              │
│  child_title_id (FK)     │        │  stock_available         │
│  call_out_order          │        └──────────────────────────┘
│  unit_qty                │
│  lr                      │
│  remark                  │
│  nn_note                 │
└──────────────────────────┘
```

### Hierarchy Flow
```
Vehicle (Serial Number)
    └── System Category (Parent Title)
        └── Diagram/Component (Child Title) [Contains SVG]
            └── Parts (Part) [Multiple instances]
                └── Pricing (PricingData) [Optional]
```

### Example: Complete Product Hierarchy
```
Maxus                                    [serialnumber.vehicle_brand]
└── LSFAL11A4PA157987                   [serialnumber.serial]
    └── Entertainment                    [parenttitle.title]
        └── Speaker                      [childtitle.title]
            └── RING-BEARING INNER       [part.usage_name]
                • SKU: B00004111         [part.part_number]
                • Callout: 4             [part.call_out_order]
                • Qty: 8.0               [part.unit_qty]
                • Price: £1.33           [pricingdata.list_price]
```

---

## Common Query Patterns

### 1. Get All Parts for a Specific Serial
```sql
SELECT 
    sn.vehicle_brand,
    sn.serial,
    pt.title as parent_category,
    ct.title as child_category,
    p.id as part_id,
    p.part_number,
    p.usage_name,
    p.call_out_order,
    p.unit_qty,
    p.lr,
    p.remark,
    p.nn_note
FROM motorpartsdata_part p
JOIN motorpartsdata_childtitle ct ON p.child_title_id = ct.id
JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id
JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
WHERE sn.serial = 'LSFAL11A4PA157987'
ORDER BY pt.title, ct.title, p.call_out_order;
```

### 2. Get Category Hierarchy for a Serial
```sql
SELECT DISTINCT
    sn.vehicle_brand as brand,
    sn.serial,
    pt.title as parent_category,
    ct.title as child_category
FROM motorpartsdata_serialnumber sn
LEFT JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
LEFT JOIN motorpartsdata_childtitle ct ON ct.parent_id = pt.id
WHERE sn.serial = 'LSFAL11A4PA157987'
ORDER BY pt.title, ct.title;
```

### 3. Get Parts with Pricing
```sql
SELECT 
    p.part_number,
    p.usage_name,
    pd.list_price,
    pd.stock_available
FROM motorpartsdata_part p
LEFT JOIN motorpartsdata_pricingdata pd ON pd.part_number_id = p.id
WHERE p.part_number = 'B00004111';
```

### 4. Count Statistics for a Serial
```sql
SELECT 
    COUNT(DISTINCT pt.id) as parent_categories,
    COUNT(DISTINCT ct.id) as child_diagrams,
    COUNT(DISTINCT p.id) as total_parts,
    COUNT(DISTINCT p.part_number) as unique_skus
FROM motorpartsdata_serialnumber sn
JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
JOIN motorpartsdata_childtitle ct ON ct.parent_id = pt.id
JOIN motorpartsdata_part p ON p.child_title_id = ct.id
WHERE sn.serial = 'LSFAL11A4PA157987';
```

### 5. Find Duplicate Part Numbers (Same SKU in Different Contexts)
```sql
SELECT 
    p.part_number,
    COUNT(*) as occurrence_count,
    STRING_AGG(DISTINCT ct.title, ', ') as used_in_diagrams
FROM motorpartsdata_part p
JOIN motorpartsdata_childtitle ct ON p.child_title_id = ct.id
GROUP BY p.part_number
HAVING COUNT(*) > 1
ORDER BY occurrence_count DESC;
```

### 6. List All Tables in Database
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;
```

### 7. Get Table Schema (Column Information)
```sql
SELECT 
    column_name, 
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'motorpartsdata_part'
ORDER BY ordinal_position;
```

### 8. Extract SVG Diagrams
```sql
SELECT 
    ct.id,
    ct.title,
    pt.title as parent_title,
    sn.serial,
    ct.svg_code
FROM motorpartsdata_childtitle ct
JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id
JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
WHERE sn.serial = 'LSFAL11A4PA157987'
  AND ct.svg_code IS NOT NULL
  AND LENGTH(ct.svg_code) > 100;
```

---

## Field Mappings to WordPress

### Oscar to WooCommerce Mapping Table

| Oscar Table | Oscar Field | WP Product Field | WP Location | Notes |
|-------------|-------------|------------------|-------------|-------|
| `motorpartsdata_part` | `id` | - | `meta_data.oscar_part_id` | Unique part instance ID |
| `motorpartsdata_part` | `part_number` | - | `meta_data.original_sku` | Original manufacturer SKU |
| `motorpartsdata_part` | `usage_name` | `name` | `product.name` | Part description |
| `motorpartsdata_part` | `call_out_order` | - | `meta_data.callout_number` | Diagram reference |
| `motorpartsdata_part` | `unit_qty` | - | `meta_data.unit_qty` | Quantity needed |
| `motorpartsdata_part` | `lr` | - | `meta_data.lr` | Left/Right indicator |
| `motorpartsdata_part` | `remark` | - | `meta_data.remark` | Additional notes |
| `motorpartsdata_part` | `nn_note` | - | `meta_data.nn_note` | Special notes |
| `motorpartsdata_childtitle` | `title` | - | `categories[3]` | Sub-category |
| `motorpartsdata_childtitle` | `svg_code` | - | (Converted to PNG) | Product image source |
| `motorpartsdata_parenttitle` | `title` | - | `categories[2]` | Main category |
| `motorpartsdata_serialnumber` | `serial` | - | `categories[1]` | Serial/VIN category |
| `motorpartsdata_serialnumber` | `serial` | - | `meta_data.vehicle_serial` | Vehicle identifier |
| `motorpartsdata_serialnumber` | `vehicle_brand` | - | `categories[0]` | Brand category |
| `motorpartsdata_pricingdata` | `list_price` | `regular_price` | `product.regular_price` | Product price |

### WooCommerce SKU Generation
Note that WordPress products get a **generated SKU** different from the original:

```
WordPress SKU = {original_sku}-{hash_suffix}

Example:
  Oscar:     B00004111
  WordPress: B00004111-BF9845
```

This ensures uniqueness since the same part number can appear in multiple contexts (different vehicles, diagrams, positions).

---

## Data Statistics

### Typical Database Scale
- **Serial Numbers**: 10-100 vehicles
- **Parent Categories**: 5-20 per serial
- **Child Diagrams**: 20-200 per serial  
- **Parts per Diagram**: 10-50 parts
- **Total Parts**: 10,000-100,000+ records
- **Unique SKUs**: 5,000-20,000

### Duplication Patterns
- Same `part_number` appears multiple times (different vehicles, positions, diagrams)
- Each occurrence is a unique record with unique `id`
- Requires SKU hashing in WordPress to maintain uniqueness

---

## Best Practices

### Querying
1. **Always use JOINs** to get hierarchical context
2. **Use RealDictCursor** for named column access
3. **Filter by serial** for performance on large datasets
4. **Use DISTINCT** when counting categories to avoid duplicates

### Indexes (Assumed)
- Primary keys on all `id` columns
- Foreign key indexes on `serial_number_id`, `parent_id`, `child_title_id`, `part_number_id`
- Consider index on `part_number` for lookup queries

### Connection Management
```python
# Always close connections
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    # ... perform queries ...
finally:
    cursor.close()
    conn.close()
```

### Error Handling
```python
try:
    conn = psycopg2.connect(**DB_CONFIG)
    print("✅ Connected to Oscar database")
except psycopg2.OperationalError as e:
    print(f"❌ Connection failed: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
```

---

## Sample Connection Script

See `oscar_db_connection_sample.py` for a complete working example that demonstrates:
- Direct connection with credentials
- Loading credentials from file
- Sample queries
- Table inspection
- Error handling

---

## Related Documentation
- [dbstruct.md](dbstruct.md) - WordPress/WooCommerce database structure and mappings
- [PRODUCT_IMPORT_GUIDE.md](PRODUCT_IMPORT_GUIDE.md) - Import workflow documentation
- [oscar_db_connection_sample.py](oscar_db_connection_sample.py) - Working connection examples

---

*Last Updated: March 8, 2026*
