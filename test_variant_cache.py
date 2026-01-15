#!/usr/bin/env python3
"""
Simple test for PNG cache with variant SKUs
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.upload_missing_images_optimized import build_png_cache, find_sku_png_file

def test_variant_skus():
    """Test if variant SKUs are properly cached"""
    
    print("🧪 Testing Variant SKU Caching")
    print("=" * 40)
    
    # Build PNG cache
    images_dir = "images/converted"
    png_cache = build_png_cache(images_dir)
    
    # Test variant SKUs
    test_skus = ['C00073046-blu', 'C00073046-bla', 'C00073045-gre']
    
    for sku in test_skus:
        print(f"\n🔍 Testing SKU: {sku}")
        
        # Check if SKU is in cache
        if sku in png_cache:
            print(f"   ✅ Found in cache: {len(png_cache[sku])} files")
            for file in png_cache[sku][:3]:  # Show first 3
                print(f"      - {Path(file).name}")
        else:
            print(f"   ❌ Not found in cache")
            # Check base SKU
            base_sku = sku.split('-')[0]
            if base_sku in png_cache:
                print(f"   📁 Base SKU {base_sku} has {len(png_cache[base_sku])} files")
        
        # Test find function
        result = find_sku_png_file(sku, "BEARING-CRANKSHAFT LOWER", images_dir)
        if result:
            print(f"   🎯 find_sku_png_file result: {Path(result).name}")
        else:
            print(f"   ❌ find_sku_png_file failed")

if __name__ == "__main__":
    test_variant_skus()