#!/usr/bin/env python3
"""Check for duplicate categories in Oscar database"""
import sys
import os
sys.path.append('scripts')
from fast_create_categories import FastCategoryCreator

# Create an instance to get database connection
creator = FastCategoryCreator(serial_filter='LSFAL11A4PA157987')
if not creator.connect():
    print("❌ Failed to connect to database")
    sys.exit(1)

cursor = creator.conn.cursor()

print("🔍 Checking for duplicate parent categories in LSFAL11A4PA157987...")

# Check for duplicate parent categories
cursor.execute("""
    SELECT 
        pt.title as parent_category,
        COUNT(*) as count,
        STRING_AGG(DISTINCT pt.id::text, ', ') as parent_ids
    FROM motorpartsdata_serialnumber sn
    JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
    WHERE sn.serial = %s
    GROUP BY pt.title
    HAVING COUNT(*) > 1
    ORDER BY count DESC, pt.title
""", ('LSFAL11A4PA157987',))

duplicates = cursor.fetchall()

if duplicates:
    print(f"❌ Found {len(duplicates)} duplicate parent categories:")
    for row in duplicates:
        category, count, ids = row
        print(f"   • '{category}': {count} times (IDs: {ids})")
        
        # Check what children each duplicate has
        cursor.execute("""
            SELECT 
                pt.id as parent_id,
                pt.title as parent_title,
                ct.title as child_title
            FROM motorpartsdata_serialnumber sn
            JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
            LEFT JOIN motorpartsdata_childtitle ct ON ct.parent_id = pt.id
            WHERE sn.serial = %s AND pt.title = %s
            ORDER BY pt.id, ct.title
        """, ('LSFAL11A4PA157987', category))
        
        children = cursor.fetchall()
        print(f"      Children for each duplicate:")
        current_parent_id = None
        for child_row in children:
            parent_id, parent_title, child_title = child_row
            if parent_id != current_parent_id:
                print(f"        Parent ID {parent_id}:")
                current_parent_id = parent_id
            print(f"          → {child_title}")
        print()
else:
    print("✅ No duplicate parent categories found")

print("\n🔍 Checking for duplicate child categories...")

# Check for duplicate child categories  
cursor.execute("""
    SELECT 
        ct.title as child_category,
        COUNT(*) as count,
        STRING_AGG(DISTINCT ct.id::text, ', ') as child_ids,
        STRING_AGG(DISTINCT pt.title, ' | ') as parent_categories
    FROM motorpartsdata_serialnumber sn
    JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
    JOIN motorpartsdata_childtitle ct ON ct.parent_id = pt.id
    WHERE sn.serial = %s
    GROUP BY ct.title
    HAVING COUNT(*) > 1
    ORDER BY count DESC, ct.title
""", ('LSFAL11A4PA157987',))

child_duplicates = cursor.fetchall()

if child_duplicates:
    print(f"❌ Found {len(child_duplicates)} duplicate child categories:")
    for row in child_duplicates:
        category, count, ids, parents = row
        print(f"   • '{category}': {count} times (IDs: {ids})")
        print(f"      Under parents: {parents}")
else:
    print("✅ No duplicate child categories found")

cursor.close()
creator.conn.close()