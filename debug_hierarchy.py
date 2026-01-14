#!/usr/bin/env python3
"""Debug the hierarchy building process to understand why 5 categories are missing"""
import sys
import os
sys.path.append('scripts')
from fast_create_categories import FastCategoryCreator

def debug_hierarchy_building():
    # Create an instance
    creator = FastCategoryCreator(serial_filter='LSFAL11A4PA157987')
    if not creator.connect():
        print("❌ Failed to connect to database")
        return
    
    cursor = creator.conn.cursor()
    
    # Get the same data that the script uses
    cursor.execute("""
        SELECT 
            'Maxus' as vehicle_brand,
            sn.serial,
            pt.title as parent_category,
            ct.title as child_category
        FROM motorpartsdata_serialnumber sn
        LEFT JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
        LEFT JOIN motorpartsdata_childtitle ct ON ct.parent_id = pt.id
        WHERE sn.serial = %s
    """, ('LSFAL11A4PA157987',))
    
    rows = cursor.fetchall()
    print(f"📊 Processing {len(rows)} database rows...")
    
    # Track the exact same way the script does
    brands = set()
    serials = {}
    parents = {}
    children = {}
    
    missing_cats = {'Antenna', 'Body Interior and Exterior Electronics', 'Front Lamp', 'Rear Lamp', 'Rear View Mirror'}
    missing_raw_names = []
    
    for row in rows:
        brand = creator.sanitize_category_name(row[0])
        serial = creator.sanitize_category_name(row[1])
        parent = creator.sanitize_category_name(row[2])
        child = creator.sanitize_category_name(row[3])
        
        # Track the missing ones specifically
        if child in missing_cats:
            print(f"🎯 Processing missing category '{child}':")
            print(f"   Raw name: '{row[3]}'")
            print(f"   Parent: '{parent}'")
            missing_raw_names.append((child, row[3], parent))
        
        brands.add(brand)
        serials[serial] = brand
        parents[parent] = serial
        children[child] = parent
    
    print(f"\n📊 Final hierarchy:")
    print(f"   📂 Parent categories: {len(parents)}")
    print(f"   📄 Child categories: {len(children)}")
    
    print(f"\n🔍 Missing categories processing details:")
    for sanitized, raw, parent in missing_raw_names:
        in_children = sanitized in children
        print(f"   • '{sanitized}' (from '{raw}') → Parent: '{parent}' → In children dict: {in_children}")
        if in_children:
            print(f"     Children dict value: '{children[sanitized]}'")
    
    # Check if any of the missing ones ended up in parents instead of children
    print(f"\n🔍 Are missing categories accidentally in parents dict?")
    for cat in missing_cats:
        if cat in parents:
            print(f"   • '{cat}' found in parents dict → Serial: '{parents[cat]}'")
        else:
            print(f"   • '{cat}' NOT in parents dict")
    
    cursor.close()
    creator.conn.close()

if __name__ == "__main__":
    debug_hierarchy_building()