#!/usr/bin/env python3
"""Verify if specific categories actually appear as both parent and child"""
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

print("🔍 Checking for dual-role categories in LSFAL11A4PA157987...")

# Get all parent-child relationships for this serial
cursor.execute("""
    SELECT DISTINCT
        pt.title as parent_category,
        ct.title as child_category
    FROM motorpartsdata_serialnumber sn
    JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
    JOIN motorpartsdata_childtitle ct ON ct.parent_id = pt.id
    WHERE sn.serial = %s
    ORDER BY pt.title, ct.title
""", ('LSFAL11A4PA157987',))

rows = cursor.fetchall()
print(f"📊 Found {len(rows)} parent-child relationships")

# Build sets of parents and children
parents_set = set()
children_set = set()

for row in rows:
    parents_set.add(row[0])  # parent_category
    children_set.add(row[1])  # child_category

print(f"📂 Unique parent categories: {len(parents_set)}")
print(f"📄 Unique child categories: {len(children_set)}")

# Find dual-role categories
dual_role = parents_set.intersection(children_set)
print(f"🔄 Categories that appear as BOTH parent AND child: {len(dual_role)}")

if dual_role:
    print(f"\n❓ Dual-role categories found:")
    for cat in sorted(dual_role):
        print(f"   • '{cat}'")
        
        # Verify each one
        cursor.execute("""
            SELECT DISTINCT 'parent' as role, pt.title as category 
            FROM motorpartsdata_serialnumber sn
            JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
            WHERE sn.serial = %s AND pt.title = %s
            UNION
            SELECT DISTINCT 'child' as role, ct.title as category
            FROM motorpartsdata_serialnumber sn
            JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
            JOIN motorpartsdata_childtitle ct ON ct.parent_id = pt.id
            WHERE sn.serial = %s AND ct.title = %s
        """, ('LSFAL11A4PA157987', cat, 'LSFAL11A4PA157987', cat))
        
        roles = cursor.fetchall()
        role_types = [r[0] for r in roles]
        print(f"      Confirmed roles: {role_types}")
else:
    print("\n✅ No dual-role categories found!")
    print("   Each category appears in only ONE role (either parent OR child)")

print(f"\n🎯 Correct category counts:")
print(f"   📂 Parent categories: {len(parents_set)}")
print(f"   📄 Child categories: {len(children_set)}")
if dual_role:
    print(f"   📊 After removing dual-role from children: {len(children_set) - len(dual_role)}")
else:
    print(f"   📊 No dual-role categories to remove")

# Check the specific problem categories
problem_cats = ['Rear View Mirror', 'Front Lamp', 'Rear Lamp', 'Antenna', 'Body Interior and Exterior Electronics']
print(f"\n🎯 Checking the 5 suspected dual-role categories:")
for cat in problem_cats:
    is_parent = cat in parents_set
    is_child = cat in children_set
    print(f"   • '{cat}': Parent={is_parent}, Child={is_child}")

cursor.close()
creator.conn.close()