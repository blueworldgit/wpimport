#!/usr/bin/env python3
"""Check WordPress products vs script reports"""
import sys
import os
sys.path.append('scripts')
from fast_create_categories import FastCategoryCreator
import requests

def check_product_discrepancy():
    creator = FastCategoryCreator()
    creator.load_credentials()
    
    # Get WordPress URL from config
    sys.path.append('.')
    from config import WORDPRESS_URL
    
    print(f"🔍 Investigating Product Count Discrepancy")
    print(f"=" * 60)
    
    # Get all products from WordPress
    url = f"{WORDPRESS_URL}/wp-json/wc/v3/products"
    auth = (creator.consumer_key, creator.consumer_secret)
    
    all_products = []
    page = 1
    
    while True:
        params = {'page': page, 'per_page': 100}
        response = requests.get(url, auth=auth, params=params)
        
        if response.status_code != 200:
            print(f"❌ Error fetching products: {response.status_code}")
            return
        
        data = response.json()
        if not data:
            break
        
        all_products.extend(data)
        page += 1
        
        if len(data) < 100:
            break
    
    print(f"📊 WordPress Products Total: {len(all_products)}")
    
    # Filter products that look like our new format (with hash suffixes)
    new_format_products = []
    b00003507_products = []
    
    for product in all_products:
        sku = product.get('sku', '')
        
        # Check if it matches our new hash format (original-XXXX)
        if '-' in sku and len(sku.split('-')[-1]) == 4:
            new_format_products.append(product)
            
        # Check specifically for B00003507 variations
        if sku.startswith('B00003507'):
            b00003507_products.append(product)
    
    print(f"📊 New Hash Format Products: {len(new_format_products)}")
    print(f"📊 B00003507 Variations: {len(b00003507_products)}")
    
    if b00003507_products:
        print(f"\n📋 B00003507 Products Found:")
        for product in b00003507_products:
            sku = product.get('sku', 'N/A')
            name = product.get('name', 'N/A')
            status = product.get('status', 'N/A')
            print(f"   • SKU: {sku} | Status: {status}")
            print(f"     Name: {name[:80]}...")
    
    # Check product status distribution
    status_counts = {}
    for product in all_products:
        status = product.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"\n📊 Product Status Distribution:")
    for status, count in status_counts.items():
        print(f"   • {status}: {count}")

if __name__ == "__main__":
    check_product_discrepancy()