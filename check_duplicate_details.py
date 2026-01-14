#!/usr/bin/env python3
"""Check if duplicate child categories have different parent relationships or data"""
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

print("🔍 Analyzing the first few duplicate child categories...")

# Get a sample of duplicates to understand the pattern
cursor.execute("""
    SELECT 
        ct.title as child_category,
        ct.id as child_id,
        pt.title as parent_title,
        pt.id as parent_id,
        sn.serial
    FROM motorpartsdata_serialnumber sn
    JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
    JOIN motorpartsdata_childtitle ct ON ct.parent_id = pt.id
    WHERE sn.serial = %s 
    AND ct.title IN (
        'JE11CA001 - Engine ASM',
        'JE580A001 - Rear View Mirror', 
        'JE650A001 - Front Lamp',
        'JE741A001 - Antenna',
        'JE830A001 - Body Interior & Exterior Electronics'
    )
    ORDER BY ct.title, ct.id
""", ('LSFAL11A4PA157987',))

sample_duplicates = cursor.fetchall()

current_category = None
for row in sample_duplicates:
    child_category, child_id, parent_title, parent_id, serial = row
    
    if current_category != child_category:
        print(f"\n📂 '{child_category}':")
        current_category = child_category
    
    print(f"   ID {child_id}: Parent '{parent_title}' (ID {parent_id})")

# Check if this is a data migration issue by looking at ID ranges
cursor.execute("""
    SELECT 
        MIN(ct.id) as min_id,
        MAX(ct.id) as max_id,
        COUNT(*) as total_children
    FROM motorpartsdata_serialnumber sn
    JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
    JOIN motorpartsdata_childtitle ct ON ct.parent_id = pt.id
    WHERE sn.serial = %s
""", ('LSFAL11A4PA157987',))

id_stats = cursor.fetchone()
print(f"\n📊 Child ID statistics:")
print(f"   Min ID: {id_stats[0]}")
print(f"   Max ID: {id_stats[1]}")
print(f"   Total children: {id_stats[2]}")

# Check if duplicates are in different ID ranges (suggesting data migration)
cursor.execute("""
    SELECT 
        CASE 
            WHEN ct.id <= 200 THEN 'Low IDs (≤200)'
            ELSE 'High IDs (>200)'
        END as id_range,
        COUNT(*) as count
    FROM motorpartsdata_serialnumber sn
    JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
    JOIN motorpartsdata_childtitle ct ON ct.parent_id = pt.id
    WHERE sn.serial = %s
    GROUP BY CASE WHEN ct.id <= 200 THEN 'Low IDs (≤200)' ELSE 'High IDs (>200)' END
""", ('LSFAL11A4PA157987',))

id_ranges = cursor.fetchall()
print(f"\n📊 ID range distribution:")
for range_name, count in id_ranges:
    print(f"   {range_name}: {count} children")

cursor.close()
creator.conn.close()