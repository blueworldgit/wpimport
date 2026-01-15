#!/usr/bin/env python3
"""
Debug the exact logic path in upload_missing_images_optimized.py
to understand why variant SKUs show as "without images"
"""

import requests
import json
import sys
import os
from pathlib import Path

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
from upload_missing_images_optimized import (
    find_sku_png_file, 
    build_png_cache, 
    should_process_product, 
    get_wp_auth
)

# Load config
with open('config.py', 'r') as f:
    config_content = f.read()
    config = {}
    exec(config_content, config)

# Get WordPress authentication
wp_username, wp_app_password = get_wp_auth()

def debug_variant_sku_processing():
    """Debug the exact same logic path as the upload script"""
    
    print("🐛 Debugging Variant SKU Processing")
    print("=" * 50)
    
    # Build PNG cache (same as upload script)
    images_dir = "images/converted"
    print("📋 Building PNG cache...")
    png_cache = build_png_cache(images_dir)
    print(f"🗃️  Cached {len(png_cache)} unique SKUs")
    
    # Get products with variant SKUs that were reported as missing
    test_skus = ["C00073046-blu", "C00073046-bla", "C00073045-gre"]
    
    # Get products from WooCommerce (same as upload script)
    print("📡 Fetching products from WooCommerce...")
    
    # Get ALL products with variant SKUs
    all_products = []
    page = 1
    while True:
        response = requests.get(
            f"{config['WORDPRESS_URL']}/wp-json/wc/v3/products",
            params={'per_page': 100, 'page': page},
            auth=(wp_username, wp_app_password)
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch products: {response.status_code}")
            return
        
        products = response.json()
        if not products:  # No more products
            break
            
        all_products.extend(products)
        
        # Check if we have our test products yet
        test_products = [p for p in all_products if p.get('sku', '') in test_skus]
        if len(test_products) == len(test_skus):
            break  # Found all test products
            
        page += 1
        
        if page > 10:  # Safety limit
            break
    
    print(f"📊 Fetched {len(all_products)} total products")
    
    # Filter to only test products
    test_products = []
    for product in all_products:
        sku = product.get('sku', '')
        if sku in test_skus:
            test_products.append(product)
    
    print(f"🔍 Found {len(test_products)} test products")
    
    for product in test_products:
        print(f"\n🔍 Testing Product: {product['id']}")
        print(f"   📦 SKU: {product.get('sku', 'NO_SKU')}")
        print(f"   🏷️  Title: {product.get('name', 'NO_NAME')}")
        
        # Check if should process (same logic as upload script)
        should_process = should_process_product(product, force_overwrite=False)
        print(f"   ⚙️  should_process_product: {should_process}")
        
        if not should_process:
            print("   ⏭️  Product would be skipped in upload")
            continue
        
        # Find PNG file (same logic as upload script)
        sku = product.get('sku', '')
        title = product.get('name', '')
        
        print(f"   🔍 Looking for PNG file...")
        print(f"      SKU: '{sku}'")
        print(f"      Title: '{title}'")
        
        png_file = find_sku_png_file(sku, title, images_dir)
        print(f"   🎯 find_sku_png_file result: {png_file}")
        
        if png_file:
            print(f"   ✅ Found PNG file: {png_file}")
            print(f"   📁 Full path: {Path(images_dir) / png_file}")
            print(f"   💾 File exists: {(Path(images_dir) / png_file).exists()}")
        else:
            print(f"   ❌ NO PNG FILE FOUND")
            
            # Debug the cache lookup
            print("   🔍 Debug cache lookup:")
            print(f"      Cache size: {len(png_cache)}")
            if sku in png_cache:
                print(f"      ✅ SKU in cache: {png_cache[sku]}")
            else:
                print(f"      ❌ SKU NOT in cache")
                
                # Check for partial matches
                partial_matches = [k for k in png_cache.keys() if sku in k or k in sku]
                print(f"      🔍 Partial matches: {partial_matches[:5]}")

if __name__ == "__main__":
    debug_variant_sku_processing()