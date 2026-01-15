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
import html
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
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
_image_hash_cache = {}  # Cache image file hashes for deduplication
_uploaded_image_cache = {}  # Cache of already uploaded images hash -> media_id
_close_matches = []  # Track all close/smart matches for end report

def get_image_hash(image_path):
    """Get SHA256 hash of image file for deduplication"""
    if image_path in _image_hash_cache:
        return _image_hash_cache[image_path]
    
    try:
        with open(image_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()[:16]  # First 16 chars for speed
        _image_hash_cache[image_path] = file_hash
        return file_hash
    except Exception as e:
        return None

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
        # Extract SKU from filename (everything before the first non-SKU character after the base)
        filename = png_file.stem  # Remove .png extension
        if '-' in filename:
            # For files like "C00073046-blu-BEARING-CRANKSHAFT_LOWER.png"
            # Extract full SKU including variant: "C00073046-blu"
            parts = filename.split('-')
            if len(parts) >= 2:
                # Try different SKU patterns
                potential_skus = [
                    parts[0],  # Base SKU: C00073046
                    f"{parts[0]}-{parts[1]}",  # Variant SKU: C00073046-blu
                ]
                
                # Only add variant SKU if it looks like a color/variant (short suffix)
                if len(parts) >= 2 and len(parts[1]) <= 4:  # Short suffixes like "blu", "gre", "bla"
                    for sku in potential_skus:
                        if sku not in _png_file_cache:
                            _png_file_cache[sku] = []
                        _png_file_cache[sku].append(str(png_file))
                else:
                    # Regular SKU without variant
                    sku = parts[0]
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
    
    # Decode HTML entities and convert product name to match PNG naming convention
    decoded_name = html.unescape(product_name)  # Convert &amp; to & etc.
    
    # Apply the same transformations as the PNG conversion script
    safe_name = decoded_name.replace(' ', '_').replace('&', 'and').replace('/', '-').replace('\\', '-')
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '_-')  # Remove special chars
    
    # Expected filename format: SKU-TITLE.png
    expected_filename = f"{original_sku}-{safe_name}.png"
    
    # Try exact match first
    for file_path in available_files:
        if Path(file_path).name == expected_filename:
            return file_path
    
    # Try variations with different character handling
    variations = [
        f"{original_sku}-{safe_name.replace('_', '-')}.png",
        f"{original_sku}-{safe_name.replace('-', '_')}.png", 
        f"{original_sku}-{safe_name.upper()}.png",
        f"{original_sku}-{safe_name.lower()}.png",
        # Also try without special character replacements
        f"{original_sku}-{decoded_name.replace(' ', '_')}.png",
        f"{original_sku}-{decoded_name.replace(' ', '-')}.png",
    ]
    
    for variation in variations:
        for file_path in available_files:
            if Path(file_path).name == variation:
                return file_path
    
    # Smart fuzzy matching - find the best semantic match
    def calculate_match_score(filename, search_terms):
        """Calculate how well a filename matches the search terms"""
        filename_lower = filename.lower()
        score = 0
        
        # Look for each word in the search terms
        for term in search_terms:
            if term.lower() in filename_lower:
                # Give higher score for longer terms (more specific)
                score += len(term) * 2
                # Bonus for exact word boundaries
                if f" {term.lower()} " in f" {filename_lower} ":
                    score += len(term)
        
        # Penalty for completely unrelated terms
        unrelated_terms = ["parking", "brake", "wire", "drawing"]
        for unrelated in unrelated_terms:
            if unrelated in filename_lower and unrelated not in decoded_name.lower():
                score -= 50  # Heavy penalty for unrelated matches
        
        return score
    
    # Extract meaningful terms from the decoded product name
    search_terms = [word for word in decoded_name.replace('-', ' ').replace('_', ' ').split() 
                   if len(word) > 2]  # Skip short words like "TO", "OF" etc.
    
    # Score all available files and pick the best match
    scored_files = []
    for file_path in available_files:
        filename = Path(file_path).name
        score = calculate_match_score(filename, search_terms)
        if score > 0:  # Only consider files with positive scores
            scored_files.append((score, file_path))
    
    if scored_files:
        # Sort by score (highest first) and return the best match
        scored_files.sort(key=lambda x: x[0], reverse=True)
        best_match = scored_files[0][1]
        # Record smart match for end report
        _close_matches.append({
            'type': 'smart_match',
            'sku': original_sku,
            'product_name': product_name,
            'matched_file': Path(best_match).name,
            'score': scored_files[0][0]
        })
        print(f"      🎯 Smart match: {Path(best_match).name} for '{product_name}' (score: {scored_files[0][0]})")
        return best_match
    
    # Last resort: return first available file for this SKU
    if available_files:
        closest_match = available_files[0]
        # Record closest match for end report
        _close_matches.append({
            'type': 'closest_match',
            'sku': original_sku,
            'product_name': product_name,
            'matched_file': Path(closest_match).name,
            'score': 0
        })
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
    """
    Get products from WooCommerce that need image processing.
    Optimized to fetch only required fields for much faster performance.
    """
    wcapi = get_wordpress_api()
    products = []
    page = 1
    per_page = 100
    
    while True:
        params = {
            'page': page,
            'per_page': per_page,
            'status': 'publish',
            # OPTIMIZATION: Only fetch fields we actually need - reduces payload by ~80-90%
            '_fields': 'id,name,images,meta_data'
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

def upload_image_to_wordpress_optimized(image_path):
    """Optimized image upload with hash-based deduplication"""
    try:
        # Check if we've already uploaded this exact image content
        image_hash = get_image_hash(image_path)
        if image_hash and image_hash in _uploaded_image_cache:
            return _uploaded_image_cache[image_hash]
        
        # Get WordPress API instance
        wcapi = get_wordpress_api()
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(str(image_path))
        if not mime_type:
            mime_type = 'image/png'
        
        # Read image data
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Skip very large files (>2MB) - compress or skip
        if len(image_data) > 2 * 1024 * 1024:  # 2MB limit
            tqdm.write(f"      ⚠️  Skipping large file: {Path(image_path).name} ({len(image_data)//1024}KB)")
            return None
        
        # Upload to WordPress using REST API directly
        headers = {
            'Content-Disposition': f'attachment; filename={os.path.basename(image_path)}',
            'Content-Type': mime_type
        }
        
        response = requests.post(
            f"{WORDPRESS_URL}/wp-json/wp/v2/media",
            data=image_data,
            headers=headers,
            auth=get_wp_auth(),
            timeout=30  # Reduced timeout for faster failure detection
        )
        
        if response.status_code == 201:
            media_data = response.json()
            media_id = media_data['id']
            # Cache the result to avoid re-uploading identical images
            if image_hash:
                _uploaded_image_cache[image_hash] = media_id
            return media_id
        else:
            tqdm.write(f"      ❌ Upload failed: {Path(image_path).name} - HTTP {response.status_code}")
            return None
            
    except Exception as e:
        tqdm.write(f"      ❌ Upload error: {Path(image_path).name} - {str(e)[:100]}")
        return None

def upload_image_to_wordpress(wcapi, image_path):
    """Wrapper for backward compatibility"""
    return upload_image_to_wordpress_optimized(image_path)

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
    
    # Step 2: Upload unique images with concurrent processing
    print(f"\n🔄 Uploading {len(image_upload_plan)} unique images with concurrent processing...")
    
    # Build hash-based deduplication map
    hash_to_paths = defaultdict(list)
    for image_path in image_upload_plan.keys():
        image_hash = get_image_hash(image_path)
        if image_hash:
            hash_to_paths[image_hash].append(image_path)
    
    print(f"   📊 Deduplication: {len(image_upload_plan)} files → {len(hash_to_paths)} unique images")
    
    image_to_media_id = {}  # image_path -> media_id
    upload_success_count = 0
    
    if dry_run:
        # Simulate uploads for dry run
        for i, image_path in enumerate(image_upload_plan.keys()):
            image_to_media_id[image_path] = f"mock_media_id_{i+1}"
            upload_success_count += 1
        print(f"   🔍 DRY RUN: Would upload {len(hash_to_paths)} unique images")
    else:
        # Use ThreadPoolExecutor for concurrent uploads (limit to 3 concurrent for API safety)
        unique_images = [paths[0] for paths in hash_to_paths.values()]  # Take first path for each hash
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit upload tasks
            future_to_path = {executor.submit(upload_image_to_wordpress_optimized, path): path 
                            for path in unique_images}
            
            # Process completed uploads with progress bar
            for future in tqdm(as_completed(future_to_path), total=len(unique_images), desc="Uploading"):
                image_path = future_to_path[future]
                try:
                    media_id = future.result()
                    if media_id:
                        # Map the media_id to all images with the same hash
                        image_hash = get_image_hash(image_path)
                        if image_hash and image_hash in hash_to_paths:
                            for duplicate_path in hash_to_paths[image_hash]:
                                image_to_media_id[duplicate_path] = media_id
                        upload_success_count += 1
                except Exception as e:
                    tqdm.write(f"      ❌ Upload failed: {Path(image_path).name}: {e}")
    
    print(f"   📊 Successfully processed {upload_success_count}/{len(hash_to_paths)} unique images")
    
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
            time.sleep(0.01)  # 10ms instead of 50ms for maximum speed
    
    return {
        'unique_images': upload_success_count,
        'total_products': product_update_success,
        'products_without_images': len(products_without_images),
        'success_rate': (product_update_success / total_update_attempts * 100) if total_update_attempts > 0 else 0,
        'close_matches': _close_matches.copy()  # Return copy of close matches for reporting
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
    
    # Report close matches at the end
    close_matches = results.get('close_matches', [])
    if close_matches:
        print(f"\n⚠️  CLOSE MATCHES REPORT ({len(close_matches)} products)")
        print("=" * 50)
        
        # Group by type
        smart_matches = [m for m in close_matches if m['type'] == 'smart_match']
        closest_matches = [m for m in close_matches if m['type'] == 'closest_match']
        
        if smart_matches:
            print(f"\n🎯 Smart Matches ({len(smart_matches)} products):")
            print("   These used semantic matching but may not be perfect:")
            for match in smart_matches[:10]:  # Show first 10
                print(f"   • {match['sku']}: '{match['product_name'][:50]}...' → {match['matched_file']}")
            if len(smart_matches) > 10:
                print(f"   ... and {len(smart_matches) - 10} more smart matches")
        
        if closest_matches:
            print(f"\n🔍 Closest Matches ({len(closest_matches)} products):")
            print("   These used fallback matching and may be incorrect:")
            for match in closest_matches[:10]:  # Show first 10
                print(f"   • {match['sku']}: '{match['product_name'][:50]}...' → {match['matched_file']}")
            if len(closest_matches) > 10:
                print(f"   ... and {len(closest_matches) - 10} more closest matches")
        
        print(f"\n💡 Consider reviewing these {len(close_matches)} matches for accuracy.")
        print("   Exact matches are preferred over smart/closest matches.")
        
        # Save close matches report to file if not dry run
        if not args.dry_run:
            report_file = Path("close_matches_report.json")
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(close_matches, f, indent=2, ensure_ascii=False)
            print(f"\n📋 Close matches report saved to: {report_file}")
            print(f"   Review this file to identify products that may need better image matches.")
    else:
        print(f"\n✅ All products found exact image matches!")
    
    if args.dry_run:
        print("\n🔍 This was a DRY RUN - no actual changes were made")
    
    print("✅ Optimized image upload process completed!")
    return 0

if __name__ == "__main__":
    exit(main())