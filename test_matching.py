#!/usr/bin/env python3
"""
Test the improved matching logic for the problematic cases
"""
import os
import sys
import html
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the fixed functions  
from scripts.upload_missing_images_optimized import build_png_cache, find_sku_png_file

def test_problematic_matches():
    """Test the specific cases from bugs.txt"""
    
    print("🧪 Testing Improved Matching Logic")
    print("=" * 50)
    
    # Build cache first
    images_dir = "images/converted"
    build_png_cache(images_dir)
    
    # Test cases from bugs.txt
    test_cases = [
        {
            'sku': 'B00003511',
            'product_name': 'BOLT-EXHAUST GAS RECIRCULATION INLET &amp; OUTLET PIPE',
            'expected_contains': 'EXHAUST_GAS_RECIRCULATION'
        },
        {
            'sku': 'B00003510', 
            'product_name': 'BOLT-MAP&amp;MAT SENSOR',
            'expected_contains': 'MAP'
        }
    ]
    
    print(f"🎯 Testing {len(test_cases)} problematic cases:\n")
    
    for i, case in enumerate(test_cases, 1):
        sku = case['sku']
        product_name = case['product_name']
        expected = case['expected_contains']
        
        print(f"{i}. SKU: {sku}")
        print(f"   Product: {product_name}")
        print(f"   Decoded: {html.unescape(product_name)}")
        
        # Find the match
        result = find_sku_png_file(sku, product_name, images_dir)
        
        if result:
            filename = Path(result).name
            print(f"   ✅ Found: {filename}")
            
            # Check if it's a good match
            if expected.lower() in filename.lower():
                print(f"   🎉 GOOD MATCH: Contains '{expected}'")
            else:
                print(f"   ⚠️  QUESTIONABLE: Expected '{expected}' not found")
        else:
            print(f"   ❌ No match found")
        
        print()

if __name__ == "__main__":
    test_problematic_matches()