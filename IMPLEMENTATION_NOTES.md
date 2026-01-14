# Implementation Notes - SKU Management & Update Strategy

## SKU Uniqueness Solution

### The Challenge
- **Oscar Database**: Allows duplicate SKUs across different usage contexts (same part, different applications)
- **WordPress/WooCommerce**: Requires globally unique SKUs - no duplicates allowed
- **Example**: SKU "ABC123" might appear 5 times in Oscar for different vehicle applications

### The Solution
- **WordPress SKU**: Generated unique SKU using hash suffix: `ABC123-4F2A`
- **Metadata Storage**: Original Oscar SKU stored in product metadata as `original_sku`
- **Traceability**: Each WordPress product maintains link to original Oscar data

### Implementation Details
```php
// WordPress Product Structure
SKU: "ABC123-4F2A"              // Unique WordPress SKU
Meta: {
    "original_sku": "ABC123",    // Original Oscar SKU
    "callout_number": "5",       // Oscar callout order
    "part_id": "12345"          // Oscar part ID
}
```

### SKU Generation Logic
```python
import hashlib
hash_input = f"{original_sku}-{part_id}"
sku_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:4].upper()
unique_wordpress_sku = f"{original_sku}-{sku_suffix}"
```

## Update Strategy Documentation

### ⚠️ Critical Note for Image Updates
When updating product images, **DO NOT** match by WordPress SKU. Instead:

1. **Query products by metadata**: `meta_key='original_sku'` and `meta_value='ABC123'`
2. **Find all WordPress products** with that original SKU
3. **Update each product separately** (since one Oscar SKU = multiple WordPress products)

```python
# CORRECT approach for image updates
def update_images_for_oscar_sku(oscar_sku, image_data):
    # Find all WordPress products with this original SKU
    products = wcapi.get("products", params={
        "meta_key": "original_sku",
        "meta_value": oscar_sku
    })
    
    # Update each WordPress product
    for product in products:
        wcapi.put(f"products/{product['id']}", {
            "images": image_data
        })
```

### ⚠️ Critical Note for Pricing Updates  
When updating product pricing, **DO NOT** match by WordPress SKU. Instead:

1. **Query products by metadata**: `meta_key='original_sku'` and `meta_value='ABC123'`
2. **Apply same pricing** to all WordPress products with that original SKU
3. **Maintain price consistency** across all usage contexts

```python
# CORRECT approach for pricing updates
def update_pricing_for_oscar_sku(oscar_sku, new_price):
    # Find all WordPress products with this original SKU
    products = wcapi.get("products", params={
        "meta_key": "original_sku", 
        "meta_value": oscar_sku
    })
    
    # Update pricing for each WordPress product
    for product in products:
        wcapi.put(f"products/{product['id']}", {
            "regular_price": str(new_price),
            "price": str(new_price)
        })
```

## Context Table

| Aspect | Oscar Database | WordPress Implementation | Update Strategy |
|--------|---------------|-------------------------|-----------------|
| **SKU Uniqueness** | Allows duplicates | Requires unique SKUs | Generate hash-based unique SKUs |
| **SKU Storage** | `part_number` field | WordPress `sku` field + `original_sku` meta | Store both for traceability |
| **Product Count** | 1,479 unique SKUs | 3,688 individual products | One Oscar part = One WordPress product |
| **Image Updates** | Update by `part_number` | **Match by `original_sku` metadata** | Query meta, update all matches |
| **Pricing Updates** | Update by `part_number` | **Match by `original_sku` metadata** | Query meta, update all matches |
| **Navigation** | Part Number → Usage List | Serial → Parent → Child → Product List | Hierarchical browsing |
| **Search** | Search by part number | Search by original_sku meta or WordPress SKU | Dual search capability |

## Key Benefits

1. **WordPress Compatibility**: Unique SKUs satisfy WooCommerce requirements
2. **Oscar Traceability**: Original SKUs preserved for updates and reporting  
3. **Flexible Updates**: Can update by original Oscar SKU across multiple WordPress products
4. **Better Navigation**: Individual products enable proper category hierarchy
5. **Future-Proof**: Supports both WordPress SKU search and Oscar SKU matching

## Migration Impact

- **Before**: 1,479 concatenated products with complex names
- **After**: 3,688 individual products with proper hierarchy
- **Update Scripts**: Must use `skuoriginal_` metadata for matching
- **Reporting**: Can aggregate by original SKU or report individual usage contexts

## Vector Image Management Strategy

### Image Upload Challenges
After bulk import with images, some products may have failed image uploads. Key considerations:

1. **Error Handling**: Run reports to identify products with `has_diagram_image=false` or missing images
2. **Vector Reprocessing**: Can regenerate vectors for failed products using original HTML diagrams
3. **One Vector = Multiple SKUs**: Each diagram represents multiple parts with different callout numbers

### SKU-to-Vector Mapping
**Critical Issue**: One vector diagram contains multiple SKUs, so we need tracking for troubleshooting.

**Solution**: During conversion, create mapping files:
```json
{
  "master_Air_filter.png": {
    "source_html": "LSFAL11A4PA157987/air intake system/Air filter.html",
    "skus": ["C00041192", "C00017370", "C00074267", ...],
    "diagram_name": "Air filter",
    "category": "air intake system"
  }
}
```

### Image Troubleshooting Workflow
1. **Identify Failed Products**: Query products with missing images
2. **Group by Original SKU**: Find all WordPress products for each failed Oscar SKU  
3. **Lookup Vector Source**: Use mapping to find which HTML diagram contains the SKU
4. **Regenerate Vector**: Convert specific HTML diagram to PNG
5. **Batch Update**: Apply same image to all products with that original SKU

### Vector Batch Processing
```python
# Find products needing images
failed_products = wcapi.get("products", params={
    "meta_key": "has_diagram_image", 
    "meta_value": "false"
})

# Group by original_sku to minimize vector regeneration
sku_groups = group_by_original_sku(failed_products)

# For each unique Oscar SKU, find its vector and update all related products
for oscar_sku, products in sku_groups.items():
    vector_info = lookup_vector_for_sku(oscar_sku)  # Use mapping file
    regenerated_image = convert_html_to_png(vector_info['source_html'])
    update_all_products_with_image(products, regenerated_image)
```