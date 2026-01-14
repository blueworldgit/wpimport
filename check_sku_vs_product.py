#!/usr/bin/env python3
"""Check SKU B00004955 in Oscar and product ID 15078 in WordPress"""
import sys
import os
sys.path.append('scripts')
from fast_create_categories import FastCategoryCreator
import requests

def check_sku_vs_product():
    # Connect to Oscar database
    creator = FastCategoryCreator(serial_filter='LSFAL11A4PA157987')
    if not creator.connect():
        print("❌ Failed to connect to database")
        return
    
    creator.load_credentials()
    
    # Get WordPress URL from config
    sys.path.append('.')
    from config import WORDPRESS_URL
    
    print(f"🔍 Checking SKU B00004955 in Oscar vs Product ID 15078 in WordPress")
    print(f"=" * 80)
    
    # Check Oscar database for this SKU
    cursor = creator.conn.cursor()
    cursor.execute("""
        SELECT 
            p.id as part_id,
            p.part_number as sku,
            p.usage_name,
            ct.title as child_category,
            pt.title as parent_category,
            sn.serial
        FROM motorpartsdata_part p
        JOIN motorpartsdata_childtitle ct ON p.child_title_id = ct.id
        JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id
        JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
        WHERE p.part_number = %s AND sn.serial = %s
        ORDER BY p.usage_name
    """, ('B00004955', 'LSFAL11A4PA157987'))
    
    oscar_results = cursor.fetchall()
    
    print(f"📊 Oscar Database Results for SKU 'B00004955':")
    print(f"   Found {len(oscar_results)} entries:")
    
    for i, row in enumerate(oscar_results, 1):
        part_id, sku, usage_name, child_cat, parent_cat, serial = row
        print(f"   {i}. Part ID: {part_id}")
        print(f"      Usage Name: '{usage_name}'")
        print(f"      Child Category: '{child_cat}'")
        print(f"      Parent Category: '{parent_cat}'")
        print()
    
    # Check WordPress product
    url = f"{WORDPRESS_URL}/wp-json/wc/v3/products/15078"
    auth = (creator.consumer_key, creator.consumer_secret)
    
    print(f"📊 WordPress Product ID 15078:")
    response = requests.get(url, auth=auth)
    
    if response.status_code == 200:
        product = response.json()
        print(f"   SKU: {product.get('sku', 'N/A')}")
        print(f"   Name: '{product.get('name', 'N/A')}'")
        print(f"   Status: {product.get('status', 'N/A')}")
        
        categories = product.get('categories', [])
        if categories:
            print(f"   Categories ({len(categories)}):")
            for cat in categories:
                print(f"      • {cat['name']} (ID: {cat['id']})")
        else:
            print(f"   Categories: None")
    else:
        print(f"   ❌ Error fetching product: {response.status_code}")
    
    print(f"\n🎯 Analysis:")
    if len(oscar_results) > 1:
        print(f"   • Oscar has {len(oscar_results)} different usage names for same SKU")
        print(f"   • Each usage name represents same part in different applications")
        print(f"   • WordPress should show 1 product with multiple categories")
    else:
        print(f"   • Only 1 usage found in Oscar")
    
    cursor.close()
    creator.conn.close()

if __name__ == "__main__":
    check_sku_vs_product()