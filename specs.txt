# WooCommerce Migration Plan

## Project Goal
Import EPC (Electronic Parts Catalog) data from HTML files directly into WordPress/WooCommerce as products, bypassing Oscar entirely.

---

## Data Source Structure

### EPC Data Folder Organization

The source data is organized in a hierarchical folder structure:

```
epcdata/
  └── LSFAL11A5MA087816/                    # Vehicle Serial Number (VIN)
      ├── air intake system/
      │   └── Air filter.html               # Diagram HTML file
      ├── brakes/
      │   ├── Brake Apply.html
      │   ├── Front Brakes.html
      │   └── Rear Brakes.html
      ├── body upper structure/
      │   ├── inner framing(left side).html  # Note: paired diagrams
      │   ├── inner framing(right side).html
      │   ├── Outer Framing(left side).html
      │   └── Outer Framing(right side).html
      ├── front lamp/
      │   └── Front Lamp.html
      └── ... (50+ category folders)
```

**Key Observations**:
1. **Top Level**: Vehicle serial number (VIN) - one folder per vehicle
2. **Second Level**: Part category folders (lowercase, spaces allowed)
3. **Third Level**: HTML files with part diagrams and data
4. **Naming Convention**: Mixed case, spaces in folder/file names
5. **Paired Diagrams**: Some categories have "left side" and "right side" diagrams

### HTML File Structure

Each HTML file contains:

**1. SVG Diagram Section**
- Embedded `<svg>` element with technical drawing
- Callout numbers pointing to parts
- Will be converted to PNG for WooCommerce

**2. Parts Data Table**
```html
<div class="parts-item" data-id="233583" data-part-id="C00185421" data-callout="1">
    <span class="column" style="width:70px;">Left</span>         <!-- L/R field -->
    <span class="column text-column text-column-note">
        <span title="LED headlight">LED headlight</span>    <!-- Remark -->
    </span>
</div>

<!-- Full part details section -->
<span class="column describe text-column" title="HEADLAMP">HEADLAMP</span>  <!-- Part name -->
<span class="column quantity">1.0</span>                                    <!-- Quantity -->
<div class="part-number">
    <a href="/part/C00185421">C00185421</a>                            <!-- SKU -->
</div>
```

**3. Critical Data Fields**
- **SKU**: Unique part number from `data-part-id` attribute (e.g., `C00185421`, `C00087470`)
  ```html
  <div class="parts-item" data-part-id="C00185421" data-callout="1">
  <!-- data-part-id IS the SKU -->
  ```
- **Part Name**: Generic name from description column (e.g., `HEADLAMP`)
- **L/R Field**: Orientation - `Left`, `Right`, or empty
- **Callout Number**: Reference to diagram from `data-callout` attribute (e.g., `1`, `2`, `3`)
- **Quantity**: Units required from quantity column (e.g., `1.0`, `2.0`)
- **Remark**: Additional notes (e.g., `LED headlight`, `Right rudder`)
- **Data ID**: Internal reference from `data-id` attribute

**Parsing Strategy**:
```python
def extract_part_from_html(parts_item_div):
    """
    Extract part data from HTML div element
    """
    sku = parts_item_div.get('data-part-id')          # This is the SKU!
    callout = parts_item_div.get('data-callout')
    data_id = parts_item_div.get('data-id')
    
    # Extract other fields from child spans
    lr = parts_item_div.find('span', class_='column').text.strip()
    name = parts_item_div.find('span', class_='describe').text.strip()
    quantity = parts_item_div.find('span', class_='quantity').text.strip()
    
    return {
        'sku': sku,
        'name': name,
        'lr': lr,
        'callout': callout,
        'quantity': quantity
    }
```

### Part Variations in Data

**Many parts have Left/Right variations** within the same HTML file:

```html
<!-- Example from Front Lamp.html -->

<!-- Left variant -->
<div class="parts-item" data-part-id="C00185421" data-callout="1">
    <span class="column" style="width:70px;">Left</span>
    <span class="column describe">HEADLAMP</span>
    <!-- SKU: C00185421 -->
</div>

<!-- Right variant -->
<div class="parts-item" data-part-id="C00185422" data-callout="1">
    <span class="column" style="width:70px;">Right</span>
    <span class="column describe">HEADLAMP</span>
    <!-- SKU: C00185422 -->
</div>
```

**Pattern Detection**:
- Same part name: `HEADLAMP`
- Same callout number: `1`
- Different SKUs: `C00185421` vs `C00185422`
- Different L/R values: `Left` vs `Right`

→ **These should become ONE WooCommerce Variable Product**

### Why This SKU Structure is Perfect for Variations

The `data-part-id` approach **perfectly supports** WooCommerce Variable Products:

✅ **Unique SKU per variation**: Each orientation (Left/Right) has its own `data-part-id`
- Left headlamp: `C00185421`
- Right headlamp: `C00185422`

✅ **Independent inventory tracking**: Each variation can have different stock levels
- Left: 10 units in stock
- Right: 5 units in stock

✅ **Independent pricing**: Each variation can have its own price
- Left: $125.50
- Right: $130.00 (maybe more expensive due to sensor)

✅ **WooCommerce best practice**: Variable products should have unique SKUs per variation

**How it maps to WooCommerce**:
```
Parent Product: "HEADLAMP" (no SKU)
├── Variation: Left
│   ├── SKU: C00185421 (from data-part-id)
│   ├── Price: $125.50
│   └── Stock: 10 units
└── Variation: Right
    ├── SKU: C00185422 (from data-part-id)
    ├── Price: $130.00
    └── Stock: 5 units
```

This structure allows each physical part to be tracked independently while presenting a unified product to customers.

---



 Fast Start with Placeholders (RECOMMENDED)
1. Extract data from HTML files
2. Import products with **placeholder images** and **$0.00 pricing**
3. Convert SVGs → PNGs in background (will be done seperately at a later stage)
4. Update pricing from Excel separately
5. Run image update script to replace placeholders







**Note**: Products imported with `regular_price: "0.00"` as placeholder. Update pricing separately using Phase 4 scripts before going live.

### Quick Reference: Placeholder Workflow


          
Key Points:
- data-part-id attribute IS the SKU (e.g., C00087470)
- Pricing updated separately in Phase 4
- Images updated separately in Phase 5
- Each phase is independent and resumable
```

---

## Phase 1A: Create Placeholder Images

### Objective
Create generic placeholder images for initial product import.

### Placeholder Strategy

**Create 3 placeholder images**:

1. **General Placeholder** (`placeholder_diagram.png`)
   - Size: 2000x1500px
   - Text: "Diagram Image Coming Soon"
   - Use for most products

2. **Left Orientation Placeholder** (`placeholder_left.png`)
   - Size: 2000x1500px
   - Text: "Left Side - Diagram Coming Soon"
   - Badge/icon indicating "LEFT"

3. **Right Orientation Placeholder** (`placeholder_right.png`)
   - Size: 2000x1500px
   - Text: "Right Side - Diagram Coming Soon"
   - Badge/icon indicating "RIGHT"

### Quick Placeholder Generator

```python
from PIL import Image, ImageDraw, ImageFont

def create_placeholder(text, output_path, width=2000, height=1500):
    """
    Create a placeholder image with text
    """
    # Create white background
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add border
    border_color = '#cccccc'
    draw.rectangle([(10, 10), (width-10, height-10)], outline=border_color, width=5)
    
    # Add text
    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()
    
    # Center text
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    position = ((width - text_width) // 2, (height - text_height) // 2)
    
    draw.text(position, text, fill='#666666', font=font)
    
    # Save
    img.save(output_path, 'PNG')
    print(f"Created placeholder: {output_path}")

# Generate the 3 placeholders
create_placeholder("Diagram Image Coming Soon", "placeholder_diagram.png")
create_placeholder("LEFT - Diagram Coming Soon", "placeholder_left.png")
create_placeholder("RIGHT - Diagram Coming Soon", "placeholder_right.png")
```

### Upload Placeholders to WordPress

```python
def upload_placeholder_images():
    """
    Upload placeholder images to WordPress media library
    Returns dict mapping placeholder type to media ID
    """
    placeholders = {
        'general': 'placeholder_diagram.png',
        'left': 'placeholder_left.png',
        'right': 'placeholder_right.png'
    }
    
    placeholder_ids = {}
    
    for key, filepath in placeholders.items():
        # Upload to WordPress
        with open(filepath, 'rb') as f:
            files = {'file': (filepath, f, 'image/png')}
            response = requests.post(
                f"{wp_url}/wp-json/wp/v2/media",
                files=files,
                auth=(username, app_password)
            )
        
        media_id = response.json()['id']
        placeholder_ids[key] = media_id
        print(f"Uploaded {key} placeholder, ID: {media_id}")
    
    return placeholder_ids

# Store IDs for import script
# {'general': 123, 'left': 124, 'right': 125}
```

---

## Phase 1B: SVG to PNG Conversion (Background Task)

### Objective
Convert all SVG diagrams to PNG images for WooCommerce product galleries.

### Technical Approach

**Tool**: Python with `cairosvg` library

**Script Requirements**:
1. Parse HTML files from data directory structure
2. Extract SVG elements from each HTML file
3. Convert SVG → PNG (high resolution)
4. Generate thumbnail PNG (medium resolution)
5. Maintain directory structure in output
6. Log all conversions and errors
7. Skip already converted files (idempotent)

### Output Structure
```
converted_images/
  ├── LSFAL11A4PA157987/
  │   ├── air_intake_system/
  │   │   ├── air_filter.png (2000px width)
  │   │   └── air_filter_thumb.png (600px width)
  │   ├── brakes/
  │   │   ├── front_brakes.png
  │   │   ├── front_brakes_thumb.png
  │   │   └── ...
  │   └── ...
  └── metadata.json (tracks conversions)
```

### PNG Specifications
- **Full Size**: 2000px width, maintain aspect ratio
- **Thumbnail**: 600px width, maintain aspect ratio
- **Format**: PNG (lossless)
- **Quality**: Maximum (no compression artifacts)
- **Background**: White fill (in case of transparent SVGs)

### Conversion Script Features
```python
# Pseudocode structure
def convert_svg_to_png(svg_string, output_path, width):
    """
    Convert SVG string to PNG file
    Args:
        svg_string: Raw SVG markup
        output_path: Where to save PNG
        width: Output width in pixels
    """
    # Use cairosvg.svg2png()
    # Handle errors gracefully
    # Log success/failure
    
def process_html_file(html_path, output_dir):
    """
    Extract SVG from HTML and convert
    """
    # Parse HTML with BeautifulSoup
    # Find SVG element
    # Get file stem for naming
    # Convert to full size PNG
    # Convert to thumbnail PNG
    # Store metadata
    
def batch_convert_directory(root_dir, output_dir):
    """
    Recursively process all HTML files
    """
    # Walk directory tree
    # For each .html file
    # Call process_html_file()
    # Track progress (X of Y files)
    # Generate summary report
```

### Error Handling
- Malformed SVG: Log error, continue processing
- Missing SVG: Log warning, skip file
- File write errors: Log error, continue
- Create error_log.txt with all issues

### Output Metadata
```json
{
  "conversion_date": "2025-12-27T10:30:00Z",
  "total_files": 150,
  "successful": 148,
  "failed": 2,
  "files": [
    {
      "source": "air intake system/Air filter.html",
      "full_image": "air_intake_system/air_filter.png",
      "thumbnail": "air_intake_system/air_filter_thumb.png",
      "width": 2000,
      "height": 1500,
      "status": "success"
    }
  ],
  "errors": [
    {
      "source": "some/broken.html",
      "error": "Invalid SVG markup"
    }
  ]
}
```

---

## Phase 2: Data Extraction & Preparation

### Objective
Parse HTML files and extract structured data for WooCommerce import.

### Data Extraction Script

**Input**: HTML files from data directory
**Output**: JSON file with all product data

```json
{
  "serial_number": "LSFAL11A4PA157987",
  "vehicle_brand": "Maxus",
  "categories": [
    {
      "name": "Air Intake System",
      "slug": "air-intake-system",
      "parent": "LSFAL11A4PA157987",
      "diagrams": [
        {
          "name": "Air Filter",
          "slug": "air-filter",
          "image": "converted_images/.../air_filter.png",
          "thumbnail": "converted_images/.../air_filter_thumb.png",
          "parts": [
            {
              "sku": "52365-T7001-00",
              "name": "Air Filter Element",
              "description": "Standard air filter for intake system",
              "callout_number": "1",
              "quantity": "1",
              "orientation": "N/A",
              "remarks": "Replace every 12 months",
              "categories": ["Air Intake System", "Air Filter"]
            }
          ]
        }
      ]
    }
  ]
}
```

### Data Mapping Strategy

**Unique Part per Product**:
- Each unique SKU becomes ONE WooCommerce product
- Same part appears in multiple diagrams = one product with multiple categories
- Categories represent the hierarchy: Serial → Parent → Child

**Example**:
```
Part SKU: ABC123
Product Name: "Brake Pad Set - Front Left"
Categories: 
  - Maxus LSFAL11A4PA157987
    - Brakes
      - Front Brakes
  - Maxus LSFAL11A4PA157987
    - Body Structure
      - Front Assembly
```

### Variation Product Detection & Handling

#### Why Use Variable Products?

Many parts come in Left/Right, Front/Rear variations:
- **Headlamp Left** (C00185421) + **Headlamp Right** (C00185422)
- **Inner Framing Left** (C00076737) + **Inner Framing Right** (C00076793)
- **Front Brake** + **Rear Brake**

Instead of creating separate products, use **WooCommerce Variable Products**:

✅ **ONE parent product**: "Headlamp"  
   └─ **Variation 1**: Left (SKU: C00185421)  
   └─ **Variation 2**: Right (SKU: C00185422)

**Benefits**:
1. Cleaner catalog (one product instead of 2-4)
2. Better UX (dropdown selector on product page)
3. Proper inventory tracking per variation
4. Standard WooCommerce functionality

#### Early Detection Strategy (RECOMMENDED)

**Detect variations during HTML parsing** for cleaner implementation:

```python
def detect_variations(parts_from_html):
    """
    Group parts by (name + callout) to detect variations
    Returns: dict of variation groups
    """
    groups = {}
    
    for part in parts_from_html:
        # Create grouping key
        key = (part['name'], part['callout'])
        
        if key not in groups:
            groups[key] = []
        
        groups[key].append(part)
    
    # Identify variation groups
    variation_groups = {}
    simple_products = []
    
    for key, parts in groups.items():
        # Check if parts have different L/R values
        lr_values = [p['lr'] for p in parts if p['lr']]
        
        if len(lr_values) > 1 and len(set(lr_values)) > 1:
            # This is a variation group!
            variation_groups[key] = {
                'base_name': parts[0]['name'],
                'variations': parts
            }
        else:
            # Regular simple products
            simple_products.extend(parts)
    
    return variation_groups, simple_products

# Example output:
# variation_groups = {
#     ('HEADLAMP', '1'): {
#         'base_name': 'HEADLAMP',
#         'variations': [
#             {'sku': 'C00185421', 'lr': 'Left', 'name': 'HEADLAMP', ...},
#             {'sku': 'C00185422', 'lr': 'Right', 'name': 'HEADLAMP', ...}
#         ]
#     }
# }
```

#### Creating Variable Products in WooCommerce

```python
def create_variable_product(base_name, variations, category_ids, image_ids):
    """
    Create WooCommerce variable product with variations
    """
    # Step 1: Create parent product
    parent_data = {
        "name": base_name,
        "type": "variable",  # Key difference!
        "categories": category_ids,
        "images": [{"id": img_id} for img_id in image_ids],
        "attributes": [
            {
                "name": "Orientation",
                "visible": True,
                "variation": True,  # Makes it a variation attribute
                "options": [v['lr'] for v in variations]
            }
        ]
    }
    
    parent = wcapi.post("products", parent_data).json()
    parent_id = parent['id']
    
    # Step 2: Create variations under parent
    for variation in variations:
        variation_data = {
            "sku": variation['sku'],
            "regular_price": variation.get('price', '0.00'),
            "description": variation['description'],
            "image": {"id": variation.get('image_id')},
            "attributes": [
                {
                    "name": "Orientation",
                    "option": variation['lr']  # Left, Right, Front, Rear
                }
            ],
            "meta_data": [
                {"key": "callout_number", "value": variation['callout']},
                {"key": "quantity", "value": variation['quantity']},
                {"key": "remarks", "value": variation.get('remarks', '')}
            ]
        }
        
        wcapi.post(f"products/{parent_id}/variations", variation_data)
    
    return parent_id
```

#### Orientation Detection Patterns

```python
def extract_orientation(part):
    """
    Extract orientation from L/R field and remarks
    """
    lr_field = part.get('lr', '').strip()
    
    # Primary source: L/R column
    if lr_field:
        return lr_field  # 'Left', 'Right', 'Front', 'Rear'
    
    # Fallback: Check part name or remarks
    text = f"{part['name']} {part.get('remarks', '')}".lower()
    
    if re.search(r'\b(left|lh|l\.h\.)\b', text):
        return 'Left'
    elif re.search(r'\b(right|rh|r\.h\.)\b', text):
        return 'Right'
    elif re.search(r'\b(front|fr)\b', text):
        return 'Front'
    elif re.search(r'\b(rear|rr)\b', text):
        return 'Rear'
    
    return None  # No orientation (simple product)
```

#### Late Conversion (If Needed)

If you initially create simple products and later discover they should be variations:

```python
def convert_simple_to_variable(simple_product_ids, base_name):
    """
    Convert existing simple products to variable product
    Use with caution - may affect URLs and SEO
    """
    # 1. Fetch existing products
    products = [wcapi.get(f"products/{pid}").json() for pid in simple_product_ids]
    
    # 2. Create new variable parent
    orientations = [p['meta_data'].get('orientation') for p in products]
    parent = wcapi.post("products", {
        "name": base_name,
        "type": "variable",
        "attributes": [{
            "name": "Orientation",
            "visible": True,
            "variation": True,
            "options": orientations
        }]
    }).json()
    
    # 3. Create variations from old products
    for product in products:
        wcapi.post(f"products/{parent['id']}/variations", {
            "sku": product['sku'],
            "regular_price": product['regular_price'],
            "attributes": [{
                "name": "Orientation",
                "option": product['meta_data']['orientation']
            }]
        })
    
    # 4. Delete old simple products
    for pid in simple_product_ids:
        wcapi.delete(f"products/{pid}", {"force": True})
    
    return parent['id']
```

**⚠️ Important**: Late conversion can break:
- Product URLs (SEO impact)
- Existing shopping cart items
- Customer bookmarks

**→ Recommendation**: Detect variations early during data extraction phase.

#### When to Use Variable vs Simple Products

**Use Variable Product When**:
- Parts have Left/Right variations
- Parts have Front/Rear variations  
- Parts have Size variations (Small, Medium, Large)
- Same `(name + callout)` but different L/R values in HTML

**Use Simple Product When**:
- Unique part with no variations
- L/R field is empty or N/A
- Single occurrence of `(name + callout)` in HTML

#### Data Extraction Output for Variations

```json
{
  "products": [
    {
      "type": "variable",
      "name": "HEADLAMP",
      "base_sku": "HEADLAMP_GROUP_1",
      "variations": [
        {
          "sku": "C00185421",
          "orientation": "Left",
          "price": "0.00",
          "callout": "1",
          "quantity": "1.0"
        },
        {
          "sku": "C00185422",
          "orientation": "Right",
          "price": "0.00",
          "callout": "1",
          "quantity": "1.0"
        }
      ],
      "categories": ["Front Lamp"],
      "images": ["front_lamp.png"]
    },
    {
      "type": "simple",
      "name": "HEADLAMP BULB",
      "sku": "C00045073",
      "orientation": null,
      "price": "0.00",
      "callout": "3",
      "quantity": "2.0",
      "categories": ["Front Lamp"],
      "images": ["front_lamp.png"]
    }
  ]
}
```

### Category Structure
```
└── Maxus (Top-level brand)
    └── LSFAL11A4PA157987 (Vehicle model)
        ├── Air Intake System
        │   ├── Air Filter
        │   └── Intake Manifold
        ├── Brakes
        │   ├── Front Brakes
        │   ├── Rear Brakes
        │   └── Brake Lines
        └── ...
```

**WooCommerce Implementation**:
- Create top-level category per brand: "Maxus", "Peugeot", etc.
- Second level: Vehicle serial
- Third level: Parent categories
- Fourth level: Child categories (diagrams)

---

## Phase 3: WooCommerce Import

### Objective
Create WooCommerce products via REST API from extracted data.

### API Authentication
```python
# WordPress site URL
wp_url = "https://yoursite.com"

# WooCommerce REST API credentials (generate in WP admin)
consumer_key = "ck_xxxxxxxxxxxxxxxxxxxxx"
consumer_secret = "cs_xxxxxxxxxxxxxxxxxxxxx"

# Use WooCommerce Python library or requests
from woocommerce import API

wcapi = API(
    url=wp_url,
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    version="wc/v3"
)
```

### Import Script Flow

#### Step 1: Create Category Hierarchy
```python
def create_categories(data):
    """
    Create all categories before products
    Returns dict mapping category names to IDs
    """
    # Create top-level brand category
    # Create vehicle serial category
    # Create parent categories
    # Create child categories
    # Store category_name → category_id mapping
```

#### Step 2: Use Placeholder Images (Initial Import)
```python
def assign_placeholder_image(part_data, placeholder_ids):
    """
    Assign appropriate placeholder based on orientation
    Returns image ID to use for product
    """
    orientation = part_data.get('orientation', '').lower()
    
    if 'left' in orientation:
        return placeholder_ids['left']
    elif 'right' in orientation:
        return placeholder_ids['right']
    else:
        return placeholder_ids['general']
```

#### Step 3: Create Products (with Placeholders)
```python
def create_product(part_data, category_ids, image_ids):
    """
    Create WooCommerce product
    """
    product_data = {
        "name": part_data["name"],
        "type": "simple",
        "sku": part_data["sku"],
        "regular_price": "0.00",  # Placeholder, update later
        "description": part_data["description"],
        "short_description": f"Callout #{part_data['callout_number']}",
        "categories": category_ids,
        "images": [{"id": img_id} for img_id in image_ids],  # Placeholder IDs initially
        "attributes": [
            {
                "name": "Callout Number",
                "visible": True,
                "options": [part_data["callout_number"]]
            },
            {
                "name": "Quantity",
                "visible": True,
                "options": [part_data["quantity"]]
            },
            {
                "name": "Orientation",
                "visible": True,
                "options": [part_data["orientation"]]
            }
        ],
        "meta_data": [
            {"key": "diagram_name", "value": part_data["diagram_name"]},
            {"key": "diagram_html_path", "value": part_data["diagram_html_path"]},  # Store for later image update
            {"key": "vehicle_serial", "value": part_data["vehicle_serial"]},
            {"key": "remarks", "value": part_data["remarks"]},
            {"key": "needs_real_image", "value": "true"}  # Flag for image update script
        ]
    }
    
    response = wcapi.post("products", product_data)
    return response.json()
```

#### Step 4: Handle Duplicate Parts
```python
def get_or_create_product(sku):
    """
    Check if product with SKU exists
    If yes: update categories (add new ones)
    If no: create new product
    """
    # Search by SKU
    existing = wcapi.get("products", params={"sku": sku})
    
    if existing.json():
        # Product exists, merge categories
        return existing.json()[0]["id"]
    else:
        # Create new product
        return create_product(...)
```

### Progress Tracking
```python
# Create import log
{
  "import_date": "2025-12-27T11:00:00Z",
  "total_parts": 5432,
  "unique_skus": 3210,
  "categories_created": 165,
  "products_created": 3210,
  "products_updated": 0,
  "images_uploaded": 150,
  "errors": 12,
  "duration_seconds": 3600,
  "status": "completed"
}
```

### Rate Limiting
WooCommerce API has rate limits (typically 60 requests/minute):
```python
import time
from requests.exceptions import HTTPError

def api_call_with_retry(func, *args, max_retries=3):
    """
    Wrapper for API calls with rate limit handling
    """
    for attempt in range(max_retries):
        try:
            response = func(*args)
            if response.status_code == 429:  # Too Many Requests
                wait_time = int(response.headers.get('Retry-After', 60))
                time.sleep(wait_time)
                continue
            return response
        except HTTPError as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(5 * (attempt + 1))
```

---

## Phase 4: Update Pricing (Independent Task)

### Objective
Update product prices from Excel/CSV files. This can happen **before or after** going live.

### Why Separate Pricing Updates?
✅ **Fast initial import** - Don't wait for pricing data to be ready  
✅ **Easy repricing** - Update prices anytime without touching products  
✅ **Independent workflow** - Pricing team can work separately  
✅ **Bulk updates** - Change thousands of prices in minutes  

### Price Update Script

```python
import pandas as pd
from woocommerce import API

def update_prices_from_excel(excel_file):
    """
    Read pricing Excel, update WooCommerce products by SKU
    """
    # Load pricing data
    df = pd.read_excel(excel_file)
    # Expected columns: SKU, Price, Stock_Quantity, Stock_Status
    
    total = len(df)
    updated = 0
    errors = []
    
    for index, row in df.iterrows():
        sku = str(row['SKU']).strip()
        price = str(row['Price'])
        stock_qty = int(row.get('Stock_Quantity', 0))
        stock_status = row.get('Stock_Status', 'instock')  # instock, outofstock, onbackorder
        
        try:
            # Find product by SKU
            products = wcapi.get("products", params={"sku": sku}).json()
            
            if not products:
                errors.append(f"SKU not found: {sku}")
                continue
            
            product_id = products[0]['id']
            
            # Update price and stock
            update_data = {
                "regular_price": price,
                "stock_quantity": stock_qty,
                "stock_status": stock_status,
                "manage_stock": True
            }
            
            response = wcapi.put(f"products/{product_id}", update_data)
            
            if response.status_code == 200:
                updated += 1
                print(f"✅ Updated {sku}: ${price}")
            else:
                errors.append(f"Failed to update {sku}: {response.text}")
                
        except Exception as e:
            errors.append(f"Error processing {sku}: {str(e)}")
    
    # Summary report
    print(f"\n{'='*60}")
    print(f"Price Update Summary")
    print(f"{'='*60}")
    print(f"Total rows in Excel: {total}")
    print(f"Successfully updated: {updated}")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print(f"\nErrors:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        
        # Save full error log
        with open('pricing_errors.txt', 'w') as f:
            f.write('\n'.join(errors))
        print(f"\nFull error log saved to: pricing_errors.txt")

# Example usage
update_prices_from_excel('parts_pricing.xlsx')
```

### Expected Excel Format

| SKU | Price | Stock_Quantity | Stock_Status |
|-----|-------|----------------|-------------|
| C00185421 | 125.50 | 10 | instock |
| C00185422 | 125.50 | 5 | instock |
| C00076959 | 89.99 | 0 | outofstock |
| C00087470 | 45.00 | 100 | instock |

### Variable Product Pricing

For variable products (Left/Right variations), update each variation separately:

```python
def update_variation_prices(excel_file):
    """
    Update prices for product variations
    """
    df = pd.read_excel(excel_file)
    
    for index, row in df.iterrows():
        sku = str(row['SKU']).strip()
        price = str(row['Price'])
        
        # Find variation by SKU
        # WooCommerce API: /products/<parent_id>/variations?sku=<sku>
        # Or search all products and filter by type=variation
        
        products = wcapi.get("products", params={"sku": sku, "type": "variation"}).json()
        
        if products:
            parent_id = products[0]['parent_id']
            variation_id = products[0]['id']
            
            # Update variation price
            wcapi.put(
                f"products/{parent_id}/variations/{variation_id}",
                {"regular_price": price}
            )
            print(f"✅ Updated variation {sku}: ${price}")
```

### Batch Pricing Updates

```python
def batch_update_prices(updates, batch_size=100):
    """
    Update prices in batches using WooCommerce batch endpoint
    Faster for large updates (1000+ products)
    """
    batch_data = {
        "update": [
            {
                "id": product_id,
                "regular_price": price
            }
            for product_id, price in updates
        ]
    }
    
    response = wcapi.post("products/batch", batch_data)
    return response.json()
```

### When to Update Pricing

**Option 1: Before Going Live**
- Import products with $0.00 prices
- Update all prices from Excel
- Test checkout flow
- Make site public

**Option 2: Soft Launch**
- Import products with $0.00 or placeholder prices
- Make site visible (catalog mode, no checkout)
- Update prices gradually
- Enable checkout once pricing complete

**Option 3: Ongoing Updates**
- Site already live
- Regular price updates from supplier
- Run pricing script weekly/monthly
- Prices update automatically

---

## Phase 4A: Product Enhancement (Optional)

### After Initial Import & Pricing

#### 1. Product Descriptions
Enhance product descriptions beyond basic data:
```python
def enhance_product_description(product_id, part_data):
    """
    Generate rich product description
    """
    description = f\"\"\"
    <h3>{part_data['name']}</h3>
    <p><strong>Part Number:</strong> {part_data['sku']}</p>
    <p><strong>Fits Vehicle:</strong> {part_data['vehicle_serial']}</p>
    <p><strong>Diagram:</strong> {part_data['diagram_name']}</p>
    <p><strong>Callout Number:</strong> {part_data['callout']}</p>
    
    {f"<p><strong>Notes:</strong> {part_data['remarks']}</p>" if part_data['remarks'] else ""}
    
    <p>Genuine OEM part for Maxus vehicles.</p>
    \"\"\"
    
    wcapi.put(f"products/{product_id}", {"description": description})
```

#### 2. Product Attributes
Create global attributes in WooCommerce:
- Callout Number (1-999)
- Orientation (Left, Right, N/A)
- Quantity (1-10)
- Vehicle Serial (dropdown of all serials)
- Diagram Name (reference to diagram)

#### 3. Related Products
Link parts from same diagram as related products:
```python
def link_related_parts(diagram_parts):
    """
    For each part in a diagram, set other parts as related
    """
    part_ids = [get_product_id(p["sku"]) for p in diagram_parts]
    
    for part_id in part_ids:
        other_parts = [pid for pid in part_ids if pid != part_id]
        update_product(part_id, {
            "related_ids": other_parts[:10]  # Max 10 related
        })
```

---

## Phase 5: Replace Placeholder Images with Real Diagrams

### Objective
Convert SVG diagrams to PNG and update WooCommerce products with real images.

### Why This is Phase 5 (Not Phase 1)
✅ Products are already live and testable  
✅ Categories and data structure validated  
✅ Can run image conversion in background  
✅ Update images in batches (e.g., 10 categories at a time)  
✅ Non-blocking - business can continue  

### Step 1: Convert SVGs to PNGs

```python
from bs4 import BeautifulSoup
import cairosvg
from pathlib import Path

def convert_svg_to_png(html_file_path, output_dir):
    """
    Extract SVG from HTML and convert to PNG
    Returns paths to full image and thumbnail
    """
    # Parse HTML
    with open(html_file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    # Find SVG element
    svg = soup.find('svg')
    if not svg:
        print(f"No SVG found in {html_file_path}")
        return None, None
    
    svg_string = str(svg)
    
    # Generate output filenames
    diagram_name = Path(html_file_path).stem
    category_name = Path(html_file_path).parent.name
    
    full_path = output_dir / f"{category_name}_{diagram_name}.png"
    thumb_path = output_dir / f"{category_name}_{diagram_name}_thumb.png"
    
    # Convert to full size PNG (2000px width)
    cairosvg.svg2png(
        bytestring=svg_string.encode('utf-8'),
        write_to=str(full_path),
        output_width=2000
    )
    
    # Convert to thumbnail (600px width)
    cairosvg.svg2png(
        bytestring=svg_string.encode('utf-8'),
        write_to=str(thumb_path),
        output_width=600
    )
    
    return full_path, thumb_path

def batch_convert_svgs(data_dir, output_dir, batch_size=10):
    """
    Convert SVGs in batches
    """
    html_files = list(Path(data_dir).rglob('*.html'))
    total = len(html_files)
    
    for i, html_file in enumerate(html_files):
        print(f"Converting {i+1}/{total}: {html_file.name}")
        
        try:
            full_img, thumb_img = convert_svg_to_png(html_file, output_dir)
            
            # Log conversion for tracking
            log_conversion(html_file, full_img, thumb_img, success=True)
            
        except Exception as e:
            print(f"Error converting {html_file}: {e}")
            log_conversion(html_file, None, None, success=False, error=str(e))
        
        # Pause between batches to avoid overload
        if (i + 1) % batch_size == 0:
            print(f"Batch complete. Processed {i+1}/{total}")
```

### Step 2: Upload PNGs to WordPress

```python
def upload_image_to_wordpress(image_path, diagram_name):
    """
    Upload PNG to WordPress media library
    Returns media ID
    """
    with open(image_path, 'rb') as f:
        files = {
            'file': (image_path.name, f, 'image/png')
        }
        
        response = requests.post(
            f"{wp_url}/wp-json/wp/v2/media",
            files=files,
            auth=(username, app_password),
            data={
                'title': diagram_name,
                'alt_text': f"{diagram_name} diagram"
            }
        )
    
    if response.status_code == 201:
        media_id = response.json()['id']
        print(f"Uploaded {image_path.name}, Media ID: {media_id}")
        return media_id
    else:
        print(f"Failed to upload {image_path.name}: {response.text}")
        return None
```

### Step 3: Update Products with Real Images

```python
def update_products_with_real_images(diagram_html_path, full_image_id, thumb_image_id):
    """
    Find all products from a specific diagram and update their images
    """
    # Search for products with this diagram
    products = wcapi.get("products", params={
        "meta_key": "diagram_html_path",
        "meta_value": diagram_html_path,
        "per_page": 100
    }).json()
    
    print(f"Found {len(products)} products for diagram: {diagram_html_path}")
    
    for product in products:
        product_id = product['id']
        
        # Update product images
        update_data = {
            "images": [
                {"id": full_image_id},      # Full size
                {"id": thumb_image_id}      # Thumbnail
            ],
            "meta_data": [
                {"key": "needs_real_image", "value": "false"}  # Clear flag
            ]
        }
        
        response = wcapi.put(f"products/{product_id}", update_data)
        
        if response.status_code == 200:
            print(f"✅ Updated product {product['sku']} with real images")
        else:
            print(f"❌ Failed to update product {product['sku']}: {response.text}")

def batch_update_all_products():
    """
    Complete workflow: Convert SVG → Upload → Update Products
    """
    # 1. Get all HTML files
    html_files = list(Path(data_dir).rglob('*.html'))
    
    # 2. Process each diagram
    for i, html_file in enumerate(html_files):
        print(f"\n{'='*60}")
        print(f"Processing {i+1}/{len(html_files)}: {html_file.name}")
        print(f"{'='*60}")
        
        try:
            # Convert SVG to PNG
            full_img_path, thumb_img_path = convert_svg_to_png(html_file, output_dir)
            
            if not full_img_path:
                continue
            
            # Upload to WordPress
            full_img_id = upload_image_to_wordpress(full_img_path, html_file.stem)
            thumb_img_id = upload_image_to_wordpress(thumb_img_path, f"{html_file.stem}_thumb")
            
            if not full_img_id or not thumb_img_id:
                continue
            
            # Update all products using this diagram
            relative_path = str(html_file.relative_to(data_dir))
            update_products_with_real_images(relative_path, full_img_id, thumb_img_id)
            
            print(f"✅ Complete for {html_file.name}")
            
        except Exception as e:
            print(f"❌ Error processing {html_file.name}: {e}")
            continue
```

### Step 4: Verification & Cleanup

```python
def verify_image_updates():
    """
    Check which products still have placeholder images
    """
    # Find products with needs_real_image = true
    products = wcapi.get("products", params={
        "meta_key": "needs_real_image",
        "meta_value": "true",
        "per_page": 100
    }).json()
    
    if products:
        print(f"⚠️  {len(products)} products still need real images:")
        for p in products:
            print(f"  - {p['sku']}: {p['name']} (ID: {p['id']})")
    else:
        print("✅ All products have real images!")
    
    return products

def delete_placeholder_images():
    """
    Remove placeholder images from media library (optional)
    """
    placeholders = [
        "placeholder_diagram.png",
        "placeholder_left.png", 
        "placeholder_right.png"
    ]
    
    for placeholder_name in placeholders:
        # Search media library
        response = requests.get(
            f"{wp_url}/wp-json/wp/v2/media",
            params={"search": placeholder_name},
            auth=(username, app_password)
        )
        
        media_items = response.json()
        
        for item in media_items:
            # Check if still used by any products
            products_using = wcapi.get("products", params={
                "image": item['id']
            }).json()
            
            if not products_using:
                # Safe to delete
                requests.delete(
                    f"{wp_url}/wp-json/wp/v2/media/{item['id']}",
                    params={"force": True},
                    auth=(username, app_password)
                )
                print(f"Deleted unused placeholder: {placeholder_name}")
```

### Image Update Progress Tracking

```json
{
  "update_date": "2025-12-28T15:30:00Z",
  "total_diagrams": 150,
  "converted": 148,
  "uploaded": 148,
  "products_updated": 3210,
  "still_pending": 45,
  "errors": 2,
  "failed_diagrams": [
    {
      "file": "air intake system/complex_diagram.html",
      "error": "Invalid SVG structure"
    }
  ]
}
```

### Advantages of This Approach

| Aspect | Placeholder First | Images First |
|--------|-------------------|--------------|
| **Time to first products** | 2-4 hours | 2-3 days |
| **Data testing** | Immediate | Delayed |
| **Image conversion** | Background task | Blocking |
| **Error recovery** | Re-run image update | Re-run full import |
| **Flexibility** | Update images anytime | Must convert all upfront |
| **User experience** | Products visible (temp images) | Wait for complete import |

---

## Phase 6: Frontend Customization (Optional)

### Custom Product Template
Create custom WooCommerce product template to show:
- Diagram image prominently
- Part callout number badge
- "Also appears in X other diagrams" section
- List of all parts from same diagram

### Custom Archive Page
Create vehicle-specific catalog pages:
- `/shop/maxus/LSFAL11A4PA157987/` shows all parts for that vehicle
- Interactive category navigation
- Diagram preview in category view

### Search Enhancement
Configure WooCommerce search to find by:
- Part number (SKU)
- Part name
- Callout number
- Vehicle serial
- Category name

---

## Technical Requirements

### Server Requirements
- **PHP**: 7.4+ (8.0+ recommended)
- **WordPress**: 6.0+
- **WooCommerce**: 7.0+
- **MySQL**: 5.7+ or MariaDB 10.3+
- **Memory**: 256MB minimum, 512MB recommended
- **Disk Space**: ~2GB for images + database

### Python Environment
```
Python 3.8+
Libraries:
  - beautifulsoup4==4.12.0
  - cairosvg==2.7.0
  - requests==2.31.0
  - pandas==2.0.0 (for Excel pricing)
  - woocommerce==3.0.0 (WC API wrapper)
  - Pillow==10.0.0 (image optimization)
```

### WordPress Plugins Required
- **WooCommerce** (core)
- **Safe SVG** (if keeping SVG files) - NOT NEEDED if converting to PNG
- **WooCommerce Product Table** (optional: better product lists)
- **YITH WooCommerce Zoom Magnifier** (optional: zoom on diagrams)

---

## Project Structure (New WooCommerce Project)

```
woocommerce_epc_import/
  ├── data/                          # Copy from Oscar project
  │   └── LSFAL11A5MA087816/         # Vehicle VIN folders with HTML files
  │       ├── air intake system/
  │       ├── brakes/
  │       └── ...
  ├── scripts/
  │   ├── 01_create_placeholders.py       # Phase 1A: Generate placeholder images
  │   ├── 02_extract_data.py              # Phase 2: Parse HTML files
  │   ├── 03_import_to_woocommerce.py     # Phase 3: Create products with placeholders
  │   ├── 04_update_prices.py             # Phase 4: Load pricing from Excel
  │   ├── 05_convert_and_update_images.py # Phase 5: SVG→PNG + update products
  │   └── utils/
  │       ├── svg_converter.py            # SVG to PNG conversion
  │       ├── html_parser.py              # Parse HTML and extract parts
  │       ├── wc_api_client.py            # WooCommerce API wrapper
  │       ├── variation_detector.py       # Detect Left/Right variations
  │       └── image_uploader.py           # WordPress media upload
  ├── output/
  │   ├── placeholders/                   # Generated placeholder images
  │   │   ├── placeholder_diagram.png
  │   │   ├── placeholder_left.png
  │   │   └── placeholder_right.png
  │   ├── converted_images/               # Real PNGs (generated in Phase 5)
  │   │   ├── LSFAL11A5MA087816/
  │   │   │   ├── front_lamp_Full.png
  │   │   │   ├── front_lamp_thumb.png
  │   │   │   └── ...
  │   ├── extracted_data.json             # Parsed product data
  │   ├── import_log.json                 # Phase 3 import results
  │   ├── image_update_log.json           # Phase 5 update results
  │   └── errors/                         # Error logs
  ├── config/
  │   ├── woocommerce_config.py           # API credentials
  │   ├── wordpress_auth.py               # WP media upload credentials
  │   └── conversion_settings.py          # Image sizes, batch settings
  ├── requirements.txt
  └── README.md
```

---

## Execution Timeline (REVISED for Placeholder Approach)

### Week 1: Fast Start (Data & Structure)
- **Day 1**: Set up WordPress/WooCommerce site
- **Day 2**: Generate WooCommerce API keys, test connection
- **Day 3**: Create placeholder images, upload to WordPress
- **Day 4**: Develop data extraction script
- **Day 5**: Extract data from HTML, detect variations
- **Day 6**: Develop category creation script
- **Day 7**: Import 100 test products with placeholders ($0.00 prices)

### Week 2: Full Import & Launch Prep
- **Day 1**: Validate test import, fix any issues
- **Day 2**: Full import (all 3000+ products with placeholders)
- **Day 3**: Verify all products, categories, variations
- **Day 4**: **Update pricing from Excel** (all products now priced)
- **Day 5**: Configure attributes, filters, test checkout
- **Day 6**: Frontend testing, SEO optimization
- **Day 7**: **🚀 SITE GOES LIVE** (with placeholder images but real prices)

### Week 3: Image Conversion (Background - Site Already Live)
- **Day 1-2**: Develop SVG → PNG conversion script
- **Day 3-4**: Run conversion for all HTML files (can run overnight)
- **Day 5-6**: Upload PNGs to WordPress, update products in batches
- **Day 7**: Verify all images updated, cleanup placeholders, **COMPLETE** ✅

**Total Time to Live Site: 2 weeks** (vs 3 weeks with images-first approach)  
**Note**: Site is fully functional after Week 2, Week 3 is just image enhancement

**Total Time to Live Products: 2 weeks (vs 3 weeks with images-first approach)**

---

## Risk Mitigation

### Backup Strategy
- **Before Import**: Full WordPress database backup
- **During Import**: Checkpoint after each major category
- **Rollback Plan**: SQL script to delete all imported products

### Testing Approach
1. **Test with 10 products**: One category, validate all fields
2. **Test with 100 products**: One parent category, check performance
3. **Test with 1000 products**: Multiple categories, stress test
4. **Full Import**: All 5000+ products

### Error Recovery
```python
def resumable_import(data_file, checkpoint_file):
    """
    Support resuming failed imports
    """
    # Load checkpoint (last successful SKU)
    checkpoint = load_checkpoint(checkpoint_file)
    
    # Skip already imported products
    remaining = [p for p in data if p["sku"] > checkpoint["last_sku"]]
    
    # Import with checkpointing every 100 products
    for i, product in enumerate(remaining):
        import_product(product)
        if i % 100 == 0:
            save_checkpoint(product["sku"])
```

---

## Success Metrics

### Phase 1 Success
- ✅ All SVGs converted to PNG without errors
- ✅ Images are clear and readable
- ✅ File sizes reasonable (<1MB per full image)

### Phase 2 Success
- ✅ All parts extracted with complete data
- ✅ No missing SKUs or names
- ✅ JSON validates against schema

### Phase 3 Success
- ✅ All products created in WooCommerce
- ✅ Categories correctly nested
- ✅ Images assigned to products
- ✅ No duplicate products
- ✅ Search works for SKU and name

### Phase 4 Success
- ✅ Prices updated from Excel
- ✅ Stock status accurate
- ✅ Related products linked
- ✅ Attributes filterable

---

## Next Steps

1. **Set up WordPress/WooCommerce** (local or staging)
2. **Generate WooCommerce API keys**
3. **Copy data folder** from Oscar project
4. **Start with Phase 1**: SVG → PNG conversion script

---

## Questions to Answer Before Starting

- [ ] WordPress site URL and hosting details?
- [ ] Do you have WooCommerce installed and configured?
- [ ] Do you have Excel pricing files ready?
- [ ] How many vehicle serials will you eventually have?
- [ ] Will you need multi-currency support?
- [ ] Do you need inventory management integration?
- [ ] Target launch date?

---

## Contact for Script Development

When ready to build the scripts, provide:
1. WordPress admin access (for API key generation)
2. Sample pricing Excel file format
3. Confirm if starting with just LSFAL11A4PA157987 or all serials
4. Any specific WooCommerce theme being used

---

**Document Version**: 1.0  
**Date**: December 27, 2025  
**Status**: Planning Phase
