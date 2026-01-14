#!/usr/bin/env python3
"""Test script to verify dual-role category detection"""
import psycopg2
from psycopg2.extras import RealDictCursor

# Connect to database
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='oscar',
    user='postgres',
    password='postgres123'
)

cursor = conn.cursor(cursor_factory=RealDictCursor)

# Test the same logic as our category creator
print("🔍 Testing dual-role category detection for LSFAL11A4PA157987...")

cursor.execute("""
    SELECT 
        pt.title as parent_category,
        ct.title as child_category
    FROM motorpartsdata_serialnumber sn
    LEFT JOIN motorpartsdata_parenttitle pt ON sn.id = pt.serial_number_id
    LEFT JOIN motorpartsdata_childtitle ct ON pt.id = ct.parent_id
    WHERE sn.serial = %s AND ct.title IS NOT NULL
    ORDER BY pt.title, ct.title
""", ('LSFAL11A4PA157987',))

rows = cursor.fetchall()

# Find dual-role categories (same logic as fast_create_categories.py)
all_parents = set()
all_children = set()

for row in rows:
    if row['parent_category']:
        all_parents.add(row['parent_category'])
    if row['child_category']:
        all_children.add(row['child_category'])

dual_role_categories = all_parents.intersection(all_children)

print(f"📊 Analysis:")
print(f"   Total database rows: {len(rows)}")
print(f"   Unique parent categories: {len(all_parents)}")
print(f"   Unique child categories: {len(all_children)}")
print(f"   Dual-role categories: {len(dual_role_categories)}")

if dual_role_categories:
    print(f"\n🔄 Dual-role categories:")
    for cat in sorted(dual_role_categories):
        print(f"   • {cat}")

print(f"\n✅ Corrected counts:")
print(f"   📂 Parent categories: {len(all_parents)}")  
print(f"   📄 Child categories (excluding dual-role): {len(all_children) - len(dual_role_categories)}")
print(f"   🎯 Expected WordPress categories: 1 brand + 1 serial + {len(all_parents)} parents + {len(all_children) - len(dual_role_categories)} children = {1 + 1 + len(all_parents) + (len(all_children) - len(dual_role_categories))}")

cursor.close()
conn.close()