#!/usr/bin/env python3
"""
Debug script to check why specific SKUs aren't finding their PNG files
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.upload_missing_images_optimized import build_png_cache, find_sku_png_file, get_woocommerce_products

def debug_missing_images():
    """Debug why specific SKUs aren't finding images"""
    
    print("🔍 Debugging Missing Images")
    print("=" * 50)
    
    # Get products from WooCommerce
    print("Fetching WooCommerce products...")
    products = get_woocommerce_products()
    
    # Build PNG cache
    images_dir = "images/converted"
    build_png_cache(images_dir)
    
    # Check problematic SKUs
    problem_skus = ['C00073046-blu', 'C00073046-bla', 'C00073045-gre']
    
    for sku in problem_skus:
        print(f"\n🔍 Checking SKU: {sku}")
        
        # Find the product in WooCommerce
        matching_product = None
        for product in products:
            # Check original_sku metadata
            for meta in product.get('meta_data', []):
                if meta.get('key') == 'original_sku' and meta.get('value') == sku:
                    matching_product = product
                    break
            if matching_product:
                break
        
        if matching_product:
            product_name = matching_product.get('name', 'Unknown')
            print(f"   📦 WooCommerce Product: '{product_name}'")
            print(f"   🏷️  Product ID: {matching_product.get('id')}")
            
            # Try to find the PNG file
            result = find_sku_png_file(sku, product_name, images_dir)
            
            if result:
                print(f"   ✅ Found PNG: {Path(result).name}")
            else:
                print(f"   ❌ No PNG found for: '{product_name}'")
                
                # Check what PNG files exist for this SKU base
                base_sku = sku.split('-')[0]  # Get C00073046 from C00073046-blu
                png_files = list(Path(images_dir).glob(f"{base_sku}*.png"))
                if png_files:
                    print(f"   📁 Available PNG files for {base_sku}:")
                    for png in png_files[:5]:
                        print(f"      - {png.name}")
        else:
            print(f"   ❌ Product not found in WooCommerce")

if __name__ == "__main__":
    debug_missing_images()