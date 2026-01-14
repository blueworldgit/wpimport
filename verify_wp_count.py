#!/usr/bin/env python3
"""Simple WordPress category count verification using requests"""
import sys
import os
sys.path.append('scripts')
from fast_create_categories import FastCategoryCreator
import requests

def count_wordpress_categories():
    # Create an instance
    creator = FastCategoryCreator()
    creator.load_credentials()
    
    # Get WordPress URL from config
    sys.path.append('.')
    from config import WORDPRESS_URL
    
    print(f"📊 WordPress Category Count Verification")
    print(f"=" * 50)
    print(f"🔗 Connecting to: {WORDPRESS_URL}")
    
    # Get all categories
    url = f"{WORDPRESS_URL}/wp-json/wc/v3/products/categories"
    auth = (creator.consumer_key, creator.consumer_secret)
    
    all_categories = []
    page = 1
    
    while True:
        params = {'page': page, 'per_page': 100}
        response = requests.get(url, auth=auth, params=params)
        
        if response.status_code != 200:
            print(f"❌ Error fetching categories: {response.status_code}")
            return
        
        data = response.json()
        if not data:
            break
        
        all_categories.extend(data)
        page += 1
        
        if len(data) < 100:  # Last page
            break
    
    print(f"🏷️  Total categories found: {len(all_categories)}")
    
    # Count by hierarchy level
    brand_count = 0
    serial_count = 0
    parent_count = 0
    child_count = 0
    uncategorized = 0
    
    for cat in all_categories:
        name = cat['name']
        parent_id = cat['parent']
        
        if name == 'Uncategorized':
            uncategorized += 1
        elif name == 'Maxus':
            brand_count += 1
        elif name == 'LSFAL11A4PA157987':
            serial_count += 1
        elif parent_id != 0:  # Has a parent
            # Check if parent is a serial (meaning this is a parent category)
            parent_name = None
            for p in all_categories:
                if p['id'] == parent_id:
                    parent_name = p['name']
                    break
            
            if parent_name == 'LSFAL11A4PA157987':
                parent_count += 1
            else:
                child_count += 1
    
    print(f"\n📊 Breakdown by hierarchy level:")
    print(f"   🏢 Brands: {brand_count}")
    print(f"   🚗 Serials: {serial_count}")
    print(f"   📂 Parent categories: {parent_count}")
    print(f"   📄 Child categories: {child_count}")
    if uncategorized > 0:
        print(f"   ❓ Uncategorized: {uncategorized}")
    
    expected_total = brand_count + serial_count + parent_count + child_count
    print(f"\n🎯 Expected structure total: {expected_total}")
    print(f"📊 Actual WordPress total: {len(all_categories)}")
    
    if expected_total == 204:
        print(f"✅ SUCCESS: Got expected 204 categories!")
    elif expected_total == 200:
        print(f"⚠️  Still getting 200 - missing 4 categories")
        print(f"   Expected: 1+1+47+155 = 204")
        print(f"   Got: {brand_count}+{serial_count}+{parent_count}+{child_count} = {expected_total}")
    else:
        print(f"❓ Unexpected count: {expected_total}")
        print(f"   Expected: 1+1+47+155 = 204")
        print(f"   Got: {brand_count}+{serial_count}+{parent_count}+{child_count} = {expected_total}")

if __name__ == "__main__":
    count_wordpress_categories()