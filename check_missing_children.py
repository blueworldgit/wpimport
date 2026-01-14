#!/usr/bin/env python3
"""Find which 5 child categories are missing from WordPress"""
import sys
import os
sys.path.append('scripts')
from fast_create_categories import FastCategoryCreator
import requests

def find_missing_categories():
    # Create an instance
    creator = FastCategoryCreator(serial_filter='LSFAL11A4PA157987')
    if not creator.connect():
        print("❌ Failed to connect to database")
        return
    
    creator.load_credentials()
    
    # Get WordPress URL from config
    sys.path.append('.')
    from config import WORDPRESS_URL
    
    print(f"🔍 Finding Missing Child Categories")
    print(f"=" * 50)
    
    # Get all child categories from database
    cursor = creator.conn.cursor()
    cursor.execute("""
        SELECT DISTINCT ct.title as child_category
        FROM motorpartsdata_serialnumber sn
        JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
        JOIN motorpartsdata_childtitle ct ON ct.parent_id = pt.id
        WHERE sn.serial = %s
        ORDER BY ct.title
    """, ('LSFAL11A4PA157987',))
    
    db_children = {creator.sanitize_category_name(row[0]) for row in cursor.fetchall()}
    print(f"📊 Database has {len(db_children)} unique child categories")
    
    # Get all categories from WordPress
    url = f"{WORDPRESS_URL}/wp-json/wc/v3/products/categories"
    auth = (creator.consumer_key, creator.consumer_secret)
    
    all_wp_categories = []
    page = 1
    
    while True:
        params = {'page': page, 'per_page': 100}
        response = requests.get(url, auth=auth, params=params)
        
        if response.status_code != 200:
            print(f"❌ Error fetching WordPress categories: {response.status_code}")
            return
        
        data = response.json()
        if not data:
            break
        
        all_wp_categories.extend(data)
        page += 1
        
        if len(data) < 100:
            break
    
    # Get only child categories from WordPress
    wp_children = set()
    for cat in all_wp_categories:
        name = cat['name']
        parent_id = cat['parent']
        
        if parent_id != 0:  # Has a parent
            # Check if parent is NOT the serial (meaning this is a child category)
            parent_name = None
            for p in all_wp_categories:
                if p['id'] == parent_id:
                    parent_name = p['name']
                    break
            
            if parent_name != 'LSFAL11A4PA157987' and parent_name != 'Maxus':
                wp_children.add(name)
    
    print(f"📊 WordPress has {len(wp_children)} child categories")
    
    # Find missing categories
    missing = db_children - wp_children
    extra = wp_children - db_children
    
    if missing:
        print(f"\n❌ MISSING from WordPress ({len(missing)} categories):")
        for cat in sorted(missing):
            print(f"   • '{cat}'")
    
    if extra:
        print(f"\n➕ EXTRA in WordPress ({len(extra)} categories):")
        for cat in sorted(extra)[:10]:  # Show first 10
            print(f"   • '{cat}'")
        if len(extra) > 10:
            print(f"   ... and {len(extra) - 10} more")
    
    if not missing and not extra:
        print(f"✅ Perfect match! All categories are synchronized")
    
    cursor.close()
    creator.conn.close()

if __name__ == "__main__":
    find_missing_categories()