#!/usr/bin/env python3
"""
Optimized image upload script for WordPress products.
This version includes:
- Image deduplication (upload each unique image only once)
- Batch product updates (up to 100 products per API call)
- Force overwrite capability
- Improved progress tracking
"""

import os
import sys
import json
import argparse
import time
import mimetypes
import requests
from collections import defaultdict
from pathlib import Path
from tqdm import tqdm

# Add parent directory to path to import config
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from config import WORDPRESS_URL
from woocommerce import API

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
            return (wp_username, wp_app_password)
        
        raise Exception(f"WordPress credentials not found. Found username: {wp_username}, app_password: {bool(wp_app_password)}")
        
    except Exception as e:
        raise Exception(f"Could not load WordPress credentials: {e}")

def get_wordpress_api():
    """Initialize and return WordPress API client."""
    wp_username, wp_app_password = get_wp_auth()
    
    return API(
        url=WORDPRESS_URL,
        consumer_key=wp_username,
        consumer_secret=wp_app_password,
        version="wc/v3",
        timeout=30
    )

# Removed sanitize_filename function - using original matching logic instead

# Global cache for PNG file lookups
_png_file_cache = {}
_images_dir_cache = None

def build_png_cache(images_dir):
    """Build a cache of all PNG files for faster lookups"""
    global _png_file_cache, _images_dir_cache
    
    if _images_dir_cache == images_dir and _png_file_cache:
        return _png_file_cache
    
    print(f"📋 Building PNG file cache from {images_dir}...")
    _png_file_cache = {}
    _images_dir_cache = images_dir
    
    images_path = Path(images_dir)
    if not images_path.exists():
        return _png_file_cache
    
    # Build cache of all PNG files
    png_files = list(images_path.glob("*.png"))
    print(f"   📁 Found {len(png_files)} PNG files")
    
    for png_file in png_files:
        # Extract SKU and title from filename
        filename = png_file.stem  # Remove .png extension
        if '-' in filename:
            sku = filename.split('-', 1)[0]
            if sku not in _png_file_cache:
                _png_file_cache[sku] = []
            _png_file_cache[sku].append(str(png_file))
    
    print(f"   🗃️  Cached {len(_png_file_cache)} unique SKUs")
    return _png_file_cache

def find_sku_png_file(original_sku, product_name, images_dir):
    """
    Find the PNG file for a given original_sku and product name.
    Uses cached PNG file list for much faster lookups.
    
    Args:
        original_sku: The original Oscar SKU (e.g., 'C00041192')  
        product_name: The WordPress product name (e.g., 'MOUNT-AIR CLEANER')
        images_dir: Directory containing converted PNG files
    
    Returns:
        Path to PNG file or None if not found
    """
    from pathlib import Path
    
    # Use cached PNG files for faster lookup
    png_cache = build_png_cache(images_dir)
    
    if original_sku not in png_cache:
        return None
    
    images_path = Path(images_dir)
    
    # Get cached files for this SKU
    available_files = png_cache.get(original_sku, [])
    
    if not available_files:
        return None
    
    # Convert WordPress product name to match the PNG file naming convention
    safe_name = product_name.replace(' ', '_').replace('&', 'and').replace('/', '-').replace('\\', '-')
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '_-')  # Remove special chars
    
    # Expected filename format: SKU-TITLE.png
    expected_filename = f"{original_sku}-{safe_name}.png"
    
    # Try exact match first
    for file_path in available_files:
        if Path(file_path).name == expected_filename:
            return file_path
    
    # Try variations
    variations = [
        f"{original_sku}-{safe_name.replace('_', '-')}.png",
        f"{original_sku}-{safe_name.replace('-', '_')}.png", 
        f"{original_sku}-{safe_name.upper()}.png",
        f"{original_sku}-{safe_name.lower()}.png",
    ]
    
    for variation in variations:
        for file_path in available_files:
            if Path(file_path).name == variation:
                return file_path
    
    # Return first available file for this SKU (closest match)
    if available_files:
        closest_match = available_files[0]
        print(f"      🔍 Using closest match: {Path(closest_match).name} for '{product_name}'")
        return closest_match
    
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
            return (wp_username, wp_app_password)
        
        raise Exception(f"WordPress credentials not found. Found username: {wp_username}, app_password: {bool(wp_app_password)}")
        
    except Exception as e:
        raise Exception(f"Could not load WordPress credentials: {e}")

def get_woocommerce_products(limit=None, specific_sku=None):
    """Get products from WooCommerce that need image processing."""
    wcapi = get_wordpress_api()
    products = []
    page = 1
    per_page = 100
    
    while True:
        params = {
            'page': page,
            'per_page': per_page,
            'status': 'publish'
        }
        
        if specific_sku:
            params['meta_key'] = 'original_sku'
            params['meta_value'] = specific_sku
        
        try:
            response = wcapi.get("products", params=params)
            if response.status_code != 200:
                print(f"❌ Error fetching products: {response.status_code}")
                break
                
            batch_products = response.json()
            if not batch_products:
                break
                
            products.extend(batch_products)
            
            if limit and len(products) >= limit:
                products = products[:limit]
                break
                
            page += 1
            
        except Exception as e:
            print(f"❌ Error fetching products: {e}")
            break
    
    return products

def should_process_product(product, force_overwrite=False):
    """Determine if a product needs image processing."""
    # Get current images
    current_images = product.get('images', [])
    
    # If force overwrite, process all products
    if force_overwrite:
        return True
    
    # If no images, definitely process
    if not current_images:
        return True
    
    # If has images but they're placeholders or default, process
    for image in current_images:
        src = image.get('src', '').lower()
        if any(keyword in src for keyword in ['placeholder', 'default', 'woocommerce']):
            return True
    
    return False

def upload_image_to_wordpress(wcapi, image_path):
    """Upload image to WordPress media library using REST API (exact copy of working original)"""
    try:
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(str(image_path))
        if not mime_type:
            mime_type = 'image/png'
        
        # Read image data
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Upload to WordPress using REST API directly (not WooCommerce API)
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
            return media_data['id']
        else:
            print(f"      ❌ Image upload failed: HTTP {response.status_code}")
            print(f"      Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"      ❌ Image upload error: {e}")
        return None

def upload_images_optimized(products, images_dir, dry_run=False, force_overwrite=False):
    """
    Optimized upload function that deduplicates image uploads and batches product updates.
    
    Args:
        products: List of WooCommerce products
        images_dir: Directory containing PNG files
        dry_run: If True, don't actually upload
        force_overwrite: If True, process all products regardless of existing images
    
    Returns:
        Dictionary with success stats
    """
    wcapi = get_wordpress_api()
    
    print("🔍 Filtering products that need images...")
    
    # Filter products that need processing
    products_needing_images = []
    for product in products:
        # Check if product has original_sku metadata
        original_sku = None
        for meta in product.get('meta_data', []):
            if meta.get('key') == 'original_sku':
                original_sku = meta.get('value')
                break
        
        if not original_sku:
            continue
        
        # Check if product needs processing
        if should_process_product(product, force_overwrite):
            product['original_sku'] = original_sku
            products_needing_images.append(product)
    
    if not products_needing_images:
        print("🎉 No products found needing images!")
        return {
            'unique_images': 0,
            'total_products': 0,
            'products_without_images': 0,
            'success_rate': 100.0
        }
    
    print(f"📦 Found {len(products_needing_images)} products needing images")
    
    # Step 1: Build image upload plan (deduplicate identical images)
    print("📋 Building optimized upload plan...")
    
    # Pre-build PNG cache for faster lookups
    build_png_cache(images_dir)
    
    image_upload_plan = {}  # image_path -> [products_that_need_it]
    products_without_images = []
    
    # Process products with progress bar
    for product in tqdm(products_needing_images, desc="Finding images", unit="products"):
        original_sku = product['original_sku']
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
    print(f"   Total products with images: {sum(len(products) for products in image_upload_plan.values())}")
    print(f"   Products without images: {len(products_without_images)}")
    
    if len(products_without_images) > 0:
        print(f"\n⚠️  Products without matching images:")
        for item in products_without_images[:5]:  # Show first 5
            print(f"     - {item['sku']}: {item['name']}")
        if len(products_without_images) > 5:
            print(f"     ... and {len(products_without_images) - 5} more")
    
    # Step 2: Upload unique images and get media IDs
    print(f"\n🔄 Uploading {len(image_upload_plan)} unique images...")
    
    image_to_media_id = {}  # image_path -> media_id
    upload_success_count = 0
    
    # Add progress bar for image uploads
    upload_items = list(image_upload_plan.items())
    
    for image_path, products_needing_it in tqdm(upload_items, desc="Uploading images", unit="images"):
        image_name = os.path.basename(image_path)
        
        if dry_run:
            print(f"      🔍 DRY RUN: Would upload {image_path}")
            image_to_media_id[image_path] = f"mock_media_id_{len(image_to_media_id)+1}"
            upload_success_count += 1
        else:
            try:
                media_id = upload_image_to_wordpress(wcapi, image_path)
                if media_id:
                    image_to_media_id[image_path] = media_id
                    upload_success_count += 1
                else:
                    tqdm.write(f"      ❌ Failed to upload {image_name}")
            except Exception as e:
                tqdm.write(f"      ❌ Error uploading {image_name}: {e}")
    
    print(f"   📊 Successfully uploaded {upload_success_count}/{len(image_upload_plan)} unique images")
    
    # Step 3: Batch update products with their media IDs
    print(f"\n🔄 Updating products with uploaded images...")
    
    # Collect all product updates
    all_product_updates = []
    
    for image_path, media_id in image_to_media_id.items():
        products_for_this_image = image_upload_plan[image_path]
        
        for product in products_for_this_image:
            all_product_updates.append({
                'id': product['id'],
                'images': [{'id': media_id}]
            })
    
    # Execute batch updates (WordPress supports up to 100 products per batch)
    batch_size = 100
    product_update_success = 0
    total_update_attempts = 0
    
    # Add progress bar for batch updates
    batches = [all_product_updates[i:i + batch_size] for i in range(0, len(all_product_updates), batch_size)]
    
    for batch in tqdm(batches, desc="Updating products", unit="batches"):
        
        if dry_run:
            print(f"      🔍 DRY RUN: Would update {len(batch)} products")
            product_update_success += len(batch)
            total_update_attempts += len(batch)
        else:
            # Prepare batch update data
            update_data = []
            for update in batch:
                update_data.append({
                    'id': update['id'],
                    'images': update['images']
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
                else:
                    total_update_attempts += len(update_data)
                    tqdm.write(f"      ❌ Batch update failed: {response.status_code}")
                    
            except Exception as e:
                total_update_attempts += len(update_data)
                tqdm.write(f"      ❌ Error in batch update: {e}")
            
            # Ultra-minimal delay between batches for speed
            time.sleep(0.05)
    
    return {
        'unique_images': upload_success_count,
        'total_products': product_update_success,
        'products_without_images': len(products_without_images),
        'success_rate': (product_update_success / total_update_attempts * 100) if total_update_attempts > 0 else 0
    }

def main():
    parser = argparse.ArgumentParser(description='Optimized image upload to WordPress products')
    parser.add_argument('--limit', type=int, help='Limit number of products to process')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--original-sku', type=str, help='Process only products with specific original_sku')
    parser.add_argument('--images-dir', type=str, default='images/converted', help='Directory containing converted PNG files')
    parser.add_argument('--force-overwrite', action='store_true', help='Process ALL products and overwrite existing images')
    
    args = parser.parse_args()
    
    print("🚀 WordPress Optimized Image Upload Script")
    print("=" * 50)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
    
    if args.force_overwrite:
        print("⚠️  FORCE OVERWRITE MODE - Will process ALL products and replace existing images")
    
    print(f"📂 Images directory: {args.images_dir}")
    
    # Get products from WooCommerce
    print("\n🔄 Fetching products from WooCommerce...")
    products = get_woocommerce_products(
        limit=args.limit,
        specific_sku=args.original_sku
    )
    
    if not products:
        print("❌ No products found")
        return 1
    
    print(f"✅ Found {len(products)} total products")
    
    # Use optimized upload process
    results = upload_images_optimized(
        products=products,
        images_dir=args.images_dir,
        dry_run=args.dry_run,
        force_overwrite=args.force_overwrite
    )
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 OPTIMIZED UPLOAD SUMMARY")
    print("=" * 50)
    print(f"Unique images uploaded: {results['unique_images']}")
    print(f"Products updated successfully: {results['total_products']}")
    print(f"Products without images: {results['products_without_images']}")
    print(f"Success rate: {results['success_rate']:.1f}%")
    
    # Calculate efficiency improvement
    total_products_processed = results['total_products'] + results['products_without_images']
    if total_products_processed > 0 and results['unique_images'] > 0:
        efficiency_ratio = total_products_processed / results['unique_images']
        print(f"Efficiency: {efficiency_ratio:.1f}x (uploaded {results['unique_images']} images for {total_products_processed} products)")
    
    if args.dry_run:
        print("\n🔍 This was a DRY RUN - no actual changes were made")
    
    print("✅ Optimized image upload process completed!")
    return 0

if __name__ == "__main__":
    exit(main())