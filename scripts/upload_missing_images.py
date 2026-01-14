"""
Upload Images to Products with Missing Images
============================================

This script finds WordPress products that are missing images and uploads
the appropriate diagram images based on their original_sku metadata.

Process:
1. Query WordPress for products with no images or has_diagram_image=false
2. Group products by their original_sku to minimize image processing
3. Find corresponding SKU-named PNG files from conversion process
4. Upload images to all products with the same original_sku

Usage:
    python scripts/upload_missing_images.py --limit 50
    python scripts/upload_missing_images.py --dry-run
    python scripts/upload_missing_images.py --original-sku ABC123
"""

import os
import sys
import json
import argparse
import mimetypes
import requests
from collections import defaultdict
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import WORDPRESS_URL
from woocommerce import API

def get_wordpress_api():
    """Initialize WordPress API connection"""
    base_dir = Path(__file__).parent.parent
    
    # Load API keys from keys.txt
    keys_file = base_dir / 'keys.txt'
    try:
        with open(keys_file, 'r') as f:
            content = f.read().strip()
            lines = content.split('\n')
            consumer_key = None
            consumer_secret = None
            
            for line in lines:
                if 'ck_' in line:
                    consumer_key = line.strip()
                elif 'cs_' in line:
                    consumer_secret = line.strip()
        
        if not consumer_key or not consumer_secret:
            raise Exception("API keys not found in keys.txt")
            
    except Exception as e:
        raise Exception(f"Could not load API keys: {e}")
    
    return API(
        url=WORDPRESS_URL,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        version="wc/v3",
        timeout=30
    )

def find_products_missing_images(wcapi, limit=None, specific_sku=None, force_overwrite=False):
    """
    Find WordPress products that are missing images OR all products if force_overwrite=True
    
    Args:
        wcapi: WordPress API instance
        limit: Optional limit on number of products to process
        specific_sku: Optional specific original_sku to process
        force_overwrite: If True, process ALL products regardless of existing images
    
    Returns:
        List of products needing images
    """
    if force_overwrite:
        print("🔄 FORCE OVERWRITE MODE - Processing ALL products regardless of existing images")
    else:
        print("🔍 Finding products with missing images...")
    
    products_needing_images = []
    page = 1
    per_page = 100
    
    while True:
        params = {
            'per_page': per_page,
            'page': page,
            'status': 'publish'
        }
        
        if specific_sku:
            params.update({
                'meta_key': 'original_sku',
                'meta_value': specific_sku
            })
        
        try:
            products = wcapi.get("products", params=params).json()
            
            if not products or len(products) == 0:
                break
                
            for product in products:
                if force_overwrite:
                    # In force overwrite mode, add ALL products
                    products_needing_images.append(product)
                    continue
                
                # Original logic: Check if product has no images
                if not product.get('images', []):
                    products_needing_images.append(product)
                    continue
                    
                # Check if has_diagram_image metadata is false
                meta_data = product.get('meta_data', [])
                has_diagram_image = None
                
                for meta in meta_data:
                    if meta.get('key') == 'has_diagram_image':
                        has_diagram_image = meta.get('value')
                        break
                
                if has_diagram_image == 'false' or has_diagram_image == False:
                    products_needing_images.append(product)
                
            print(f"   Checked page {page} ({len(products)} products)")
            
            if limit and len(products_needing_images) >= limit:
                products_needing_images = products_needing_images[:limit]
                break
                
            if len(products) < per_page:
                break
                
            page += 1
            
        except Exception as e:
            print(f"❌ Error fetching products page {page}: {e}")
            break
    
    if force_overwrite:
        print(f"📊 Found {len(products_needing_images)} products for image overwrite")
    else:
        print(f"📊 Found {len(products_needing_images)} products needing images")
    return products_needing_images

def group_products_by_original_sku(products):
    """Group products by their original_sku metadata"""
    print("🔄 Grouping products by original SKU...")
    
    sku_groups = defaultdict(list)
    no_sku_products = []
    
    for product in products:
        original_sku = None
        
        # Find original_sku in metadata
        meta_data = product.get('meta_data', [])
        for meta in meta_data:
            if meta.get('key') == 'original_sku':
                original_sku = meta.get('value')
                break
        
        if original_sku:
            sku_groups[original_sku].append(product)
        else:
            no_sku_products.append(product)
    
    if no_sku_products:
        print(f"⚠️  {len(no_sku_products)} products found without original_sku metadata")
    
    print(f"📦 Grouped into {len(sku_groups)} unique original SKUs")
    return dict(sku_groups), no_sku_products

def find_sku_png_file(original_sku, product_name, images_dir="images/converted"):
    """
    Find the PNG file for a given original_sku and product name
    
    Args:
        original_sku: The original Oscar SKU (e.g., 'C00041192')  
        product_name: The WordPress product name (e.g., 'MOUNT-AIR CLEANER')
        images_dir: Directory containing converted PNG files
    
    Returns:
        Path to PNG file or None if not found
    """
    images_path = Path(images_dir)
    
    # Convert WordPress product name to match the PNG file naming convention
    # Need to match the same logic used in convert_svg_to_png.py
    safe_name = product_name.replace(' ', '_').replace('&', 'and').replace('/', '-').replace('\\', '-')
    # Don't convert hyphens to underscores - preserve them as the conversion script does
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '_-')  # Remove special chars
    
    # Expected filename format: SKU-TITLE.png (e.g., "C00041192-MOUNT-AIR_CLEANER.png")
    expected_filename = f"{original_sku}-{safe_name}.png"
    expected_path = images_path / expected_filename
    
    if expected_path.exists():
        return str(expected_path)
    
    # If exact match not found, try some variations
    variations = [
        # Try with different character replacements
        f"{original_sku}-{safe_name.replace('_', '-')}.png",
        f"{original_sku}-{safe_name.replace('-', '_')}.png", 
        f"{original_sku}-{safe_name.upper()}.png",
        f"{original_sku}-{safe_name.lower()}.png",
    ]
    
    for variation in variations:
        variant_path = images_path / variation
        if variant_path.exists():
            return str(variant_path)
    
    # If still no match, look for any file that starts with the SKU
    sku_pattern = f"{original_sku}-"
    for png_file in images_path.glob(f"{sku_pattern}*.png"):
        # Return the first match for this SKU - may not be perfect but better than nothing
        print(f"      🔍 Using closest match: {png_file.name} for '{product_name}'")
        return str(png_file)
    
    return None

def get_wp_auth():
    """Get WordPress authentication from productioncreds.txt file"""
    base_dir = Path(__file__).parent.parent
    creds_file = base_dir / 'productioncreds.txt'
    
    try:
        with open(creds_file, 'r') as f:
            content = f.read()
            
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Look for the patterns we need
        wp_username = None
        wp_app_password = None
        
        for i, line in enumerate(lines):
            # Look for "developer" username
            if line == "developer":
                wp_username = line
                # App password should be a few lines after
                # Look for the pattern with spaces (application password format)
                for j in range(i+1, min(len(lines), i+4)):
                    if ' ' in lines[j] and len(lines[j]) > 20:  # App passwords have spaces and are long
                        wp_app_password = lines[j]
                        break
                break
        
        if wp_username and wp_app_password:
            print(f"   🔑 Found WordPress credentials: {wp_username} / {wp_app_password[:10]}...")
            return (wp_username, wp_app_password)
        
        raise Exception(f"WordPress credentials not found. Found username: {wp_username}, app_password: {bool(wp_app_password)}")
        
    except Exception as e:
        raise Exception(f"Could not load WordPress credentials: {e}")

def upload_image_to_wordpress(image_path, alt_text=""):
    """Upload image to WordPress media library using REST API"""
    try:
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(str(image_path))
        if not mime_type:
            mime_type = 'image/png'
        
        # Read image data
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Upload to WordPress
        headers = {
            'Content-Disposition': f'attachment; filename={os.path.basename(image_path)}',
            'Content-Type': mime_type
        }
        
        response = requests.post(
            f"{WORDPRESS_URL}/wp-json/wp/v2/media",
            data=image_data,
            headers=headers,
            auth=get_wp_auth(),
            timeout=60
        )
        
        if response.status_code == 201:
            media_data = response.json()
            return {"id": media_data['id']}
        else:
            print(f"   ❌ Image upload failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Image upload error: {e}")
        return None

def upload_image_to_products(wcapi, products, image_path, dry_run=False):
    """
    Upload an image to multiple WordPress products
    
    Args:
        wcapi: WordPress API instance
        products: List of products to update
        image_path: Path to the image file
        dry_run: If True, don't actually upload
    
    Returns:
        Number of successful uploads
    """
    if dry_run:
        print(f"   [DRY RUN] Would upload {image_path} to {len(products)} products")
        return len(products)
    
    success_count = 0
    
    # Upload image to WordPress media library
    print(f"   📤 Uploading to media library...")
    image_data = upload_image_to_wordpress(image_path, f"Diagram for SKU")
    
    if not image_data:
        print(f"   ❌ Failed to upload image to media library")
        return 0
    
    image_id = image_data.get('id')
    print(f"   ✅ Image uploaded to media library (ID: {image_id})")
    
    # Update each product with the image
    for product in products:
        try:
            update_data = {
                'images': [
                    {
                        'id': image_id,
                        'position': 0
                    }
                ],
                'meta_data': []
            }
            
            # Preserve existing metadata and update has_diagram_image
            existing_meta = product.get('meta_data', [])
            updated_meta = []
            has_diagram_updated = False
            
            for meta in existing_meta:
                if meta.get('key') == 'has_diagram_image':
                    updated_meta.append({
                        'key': 'has_diagram_image',
                        'value': 'true'
                    })
                    has_diagram_updated = True
                else:
                    updated_meta.append(meta)
            
            # Add has_diagram_image if it wasn't present
            if not has_diagram_updated:
                updated_meta.append({
                    'key': 'has_diagram_image',
                    'value': 'true'
                })
            
            update_data['meta_data'] = updated_meta
            
            response = wcapi.put(f"products/{product['id']}", update_data)
            
            if response.status_code == 200:
                success_count += 1
            else:
                print(f"   ⚠️  Failed to update product {product['id']}: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error updating product {product['id']}: {e}")
    
    print(f"   ✅ Successfully updated {success_count}/{len(products)} products")
    return success_count

def main():
    parser = argparse.ArgumentParser(description='Upload missing images to WordPress products')
    parser.add_argument('--limit', type=int, help='Limit number of products to process')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--original-sku', type=str, help='Process only products with specific original_sku')
    parser.add_argument('--images-dir', type=str, default='images/converted', help='Directory containing converted PNG files')
    parser.add_argument('--force-overwrite', action='store_true', help='Process ALL products and overwrite existing images')
    
    args = parser.parse_args()
    
    print("🖼️  WordPress Image Upload Script")
    print("=" * 50)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
    
    if args.force_overwrite:
        print("⚠️  FORCE OVERWRITE MODE - Will process ALL products and replace existing images")
    
    # Initialize WordPress API
    try:
        wcapi = get_wordpress_api()
        print("✅ WordPress API connection established")
    except Exception as e:
        print(f"❌ Failed to connect to WordPress API: {e}")
        return 1
    
    # Find products needing images
    products_needing_images = find_products_missing_images(
        wcapi, 
        limit=args.limit,
        specific_sku=args.original_sku,
        force_overwrite=args.force_overwrite
    )
    
    if not products_needing_images:
        print("🎉 No products found needing images!")
        return 0
    
    # Group products by original_sku
    sku_groups, no_sku_products = group_products_by_original_sku(products_needing_images)
    
    if no_sku_products:
        print(f"⚠️  Skipping {len(no_sku_products)} products without original_sku metadata")
    
    # Use optimized upload process
    stats = upload_images_optimized(wcapi, sku_groups, args.images_dir, args.dry_run)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 UPLOAD SUMMARY")
    print("=" * 50)
    print(f"Unique images uploaded: {stats['unique_images']}")
    print(f"Products updated successfully: {stats['total_products']}")
    print(f"Products without images: {stats['products_without_images']}")
    
    if stats['total_products'] > 0 or stats['products_without_images'] > 0:
        total_attempted = stats['total_products'] + stats['products_without_images']
        success_rate = (stats['total_products'] / total_attempted) * 100
        print(f"Success rate: {success_rate:.1f}%")
    
    if args.dry_run:
        print("\n🔍 This was a DRY RUN - no actual changes were made")
    
    print("✅ Image upload process completed!")
    return 0
    
def upload_images_optimized(wcapi, sku_groups, images_dir, dry_run=False):
    """
    Optimized upload function that deduplicates image uploads and batches product updates
    
    Args:
        wcapi: WordPress API instance
        sku_groups: Dictionary of original_sku -> [products]
        images_dir: Directory containing PNG files
        dry_run: If True, don't actually upload
    
    Returns:
        Dictionary with success stats
    """
    from collections import defaultdict
    import time
    
    # Step 1: Build image upload plan (deduplicate identical images)
    print("📋 Building optimized upload plan...")
    
    image_upload_plan = {}  # image_path -> [products_that_need_it]
    products_without_images = []
    
    total_products = sum(len(products) for products in sku_groups.values())
    processed_products = 0
    
    for original_sku, products in sku_groups.items():
        print(f"   📦 Planning SKU: {original_sku} ({len(products)} products)")
        
        for product in products:
            processed_products += 1
            product_name = product.get('name', f"Part {original_sku}")
            
            # Find PNG file for this product
            image_path = find_sku_png_file(original_sku, product_name, images_dir)
            
            if image_path and os.path.exists(image_path):
                # Group products by their image path
                if image_path not in image_upload_plan:
                    image_upload_plan[image_path] = []
                image_upload_plan[image_path].append(product)
            else:
                products_without_images.append({
                    'product': product,
                    'sku': original_sku,
                    'name': product_name
                })
    
    print(f"📊 Upload plan created:")
    print(f"   Unique images to upload: {len(image_upload_plan)}")
    print(f"   Total products to update: {total_products - len(products_without_images)}")
    print(f"   Products without images: {len(products_without_images)}")
    
    if products_without_images:
        print(f"⚠️  Products without matching images:")
        for item in products_without_images[:5]:  # Show first 5
            print(f"      - {item['sku']}: {item['name']}")
        if len(products_without_images) > 5:
            print(f"      ... and {len(products_without_images) - 5} more")
    
    if dry_run:
        print("\n🔍 DRY RUN - Would execute the optimized upload plan above")
        return {
            'unique_images': len(image_upload_plan),
            'total_products': total_products - len(products_without_images),
            'products_without_images': len(products_without_images),
            'success_rate': 100.0 if not products_without_images else 0.0
        }
    
    # Step 2: Upload unique images and collect media IDs
    print(f"\n🎨 Uploading {len(image_upload_plan)} unique images...")
    
    image_media_ids = {}  # image_path -> media_id
    upload_success_count = 0
    
    for i, (image_path, products_for_image) in enumerate(image_upload_plan.items(), 1):
        image_name = os.path.basename(image_path)
        print(f"   📤 [{i}/{len(image_upload_plan)}] {image_name} ({len(products_for_image)} products)")
        
        # Upload image to media library
        image_data = upload_image_to_wordpress(image_path, f"Diagram for multiple products")
        
        if image_data and image_data.get('id'):
            image_media_ids[image_path] = image_data['id']
            upload_success_count += 1
            print(f"      ✅ Uploaded (Media ID: {image_data['id']})")
        else:
            print(f"      ❌ Failed to upload {image_name}")
            # Remove failed uploads from plan
            del image_upload_plan[image_path]
    
    print(f"   📊 Uploaded {upload_success_count}/{len(image_media_ids)} images successfully")
    
    # Step 3: Batch update products with their media IDs
    print(f"\n🔄 Updating products with images...")
    
    product_update_success = 0
    total_update_attempts = 0
    
    for image_path, products_for_image in image_upload_plan.items():
        if image_path not in image_media_ids:
            continue  # Skip if image upload failed
            
        media_id = image_media_ids[image_path]
        image_name = os.path.basename(image_path)
        
        print(f"   🖼️  Applying {image_name} to {len(products_for_image)} products...")
        
        # Update products in batches (WooCommerce supports up to 100 items per batch)
        batch_size = 100
        for batch_start in range(0, len(products_for_image), batch_size):
            batch_products = products_for_image[batch_start:batch_start + batch_size]
            
            # Prepare batch update data
            update_data = []
            for product in batch_products:
                # Preserve existing metadata and update has_diagram_image
                existing_meta = product.get('meta_data', [])
                updated_meta = []
                has_diagram_updated = False
                
                for meta in existing_meta:
                    if meta.get('key') == 'has_diagram_image':
                        updated_meta.append({
                            'key': 'has_diagram_image',
                            'value': 'true'
                        })
                        has_diagram_updated = True
                    else:
                        updated_meta.append(meta)
                
                # Add has_diagram_image if it wasn't present
                if not has_diagram_updated:
                    updated_meta.append({
                        'key': 'has_diagram_image',
                        'value': 'true'
                    })
                
                update_data.append({
                    'id': product['id'],
                    'images': [
                        {
                            'id': media_id,
                            'position': 0
                        }
                    ],
                    'meta_data': updated_meta
                })
            
            # Execute batch update
            try:
                response = wcapi.post("products/batch", {
                    'update': update_data
                })
                
                if response.status_code == 200:
                    batch_result = response.json()
                    successful_updates = len(batch_result.get('update', []))
                    product_update_success += successful_updates
                    total_update_attempts += len(update_data)
                    print(f"      ✅ Updated {successful_updates}/{len(update_data)} products in batch")
                else:
                    total_update_attempts += len(update_data)
                    print(f"      ❌ Batch update failed: {response.status_code}")
                    
            except Exception as e:
                total_update_attempts += len(update_data)
                print(f"      ❌ Error in batch update: {e}")
            
            # Small delay between batches to be nice to the API
            time.sleep(0.2)
    
    return {
        'unique_images': upload_success_count,
        'total_products': product_update_success,
        'products_without_images': len(products_without_images),
        'success_rate': (product_update_success / total_update_attempts * 100) if total_update_attempts > 0 else 0
    }

if __name__ == "__main__":
    exit(main())