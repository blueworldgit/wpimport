#!/usr/bin/env python3
"""Verify WordPress category count after creation"""
import sys
import os
sys.path.append('scripts')
from fast_create_categories import FastCategoryCreator
import asyncio
import aiohttp

async def count_wordpress_categories():
    # Create an instance
    creator = FastCategoryCreator(serial_filter='LSFAL11A4PA157987')
    creator.load_credentials()
    
    # Get all WordPress categories
    async with aiohttp.ClientSession() as session:
        auth = aiohttp.BasicAuth(creator.consumer_key, creator.consumer_secret)
        
        # Get all categories
        url = f"https://aimaxus.com/wp-json/wc/v3/products/categories"
        params = {'per_page': 100}
        
        all_categories = []
        page = 1
        
        while True:
            params['page'] = page
            async with session.get(url, auth=auth, params=params) as response:
                if response.status != 200:
                    print(f"❌ Error fetching categories: {response.status}")
                    return
                
                data = await response.json()
                if not data:
                    break
                
                all_categories.extend(data)
                page += 1
                
                if len(data) < 100:  # Last page
                    break
        
        print(f"📊 WordPress Category Count Verification")
        print(f"=" * 50)
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
            cat_id = cat['id']
            
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
        else:
            print(f"❓ Unexpected count: {expected_total}")

if __name__ == "__main__":
    asyncio.run(count_wordpress_categories())