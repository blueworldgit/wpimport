#!/usr/bin/env python3
"""Analyze Oscar database for duplicate categories"""
import psycopg2
from config import *

def sanitize_category_name(name):
    if not name:
        return name
    return name.replace('/', ' ').replace('&', 'and').strip()

# Connect to database
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='oscar',
    user='postgres',
    password='postgres123'
)

cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

# Get the data for our serial
query = """
    SELECT 
        vb.brand_name as vehicle_brand,
        vs.serial as serial,
        pc.category_name as parent_category,
        cc.category_name as child_category
    FROM vehicle_brand vb
    JOIN vehicle_serial vs ON vb.id = vs.brand_id
    JOIN product p ON vs.id = p.vehicle_serial_id
    JOIN part_category pc ON p.parent_category_id = pc.id
    JOIN part_category cc ON p.child_category_id = cc.id
    WHERE vs.serial = %s
    ORDER BY vb.brand_name, vs.serial, pc.category_name, cc.category_name
"""

cursor.execute(query, ('LSFAL11A4PA157987',))
rows = cursor.fetchall()

print(f"📊 Found {len(rows)} total rows for LSFAL11A4PA157987")

# Analyze categories
parents = {}  # {parent_name: count}
children = {}  # {child_name: count}
category_roles = {}  # {category_name: ['parent', 'child']}

for row in rows:
    parent = sanitize_category_name(row['parent_category'])
    child = sanitize_category_name(row['child_category'])
    
    # Count occurrences
    parents[parent] = parents.get(parent, 0) + 1
    children[child] = children.get(child, 0) + 1
    
    # Track roles
    if parent not in category_roles:
        category_roles[parent] = []
    if 'parent' not in category_roles[parent]:
        category_roles[parent].append('parent')
        
    if child not in category_roles:
        category_roles[child] = []
    if 'child' not in category_roles[child]:
        category_roles[child].append('child')

# Find categories that appear as both parent AND child
dual_role = {}
for name, roles in category_roles.items():
    if len(roles) > 1:
        dual_role[name] = roles

print(f"\n🔍 ANALYSIS:")
print(f"   📂 Unique parent categories: {len(parents)}")
print(f"   📄 Unique child categories: {len(children)}")
print(f"   🔄 Categories with dual roles (parent AND child): {len(dual_role)}")

if dual_role:
    print(f"\n⚠️  CATEGORIES WITH DUAL ROLES:")
    for name, roles in dual_role.items():
        parent_count = parents.get(name, 0)
        child_count = children.get(name, 0)
        print(f"   • '{name}': {roles} (as parent: {parent_count}x, as child: {child_count}x)")

# Find the specific 4 problematic categories
problem_cats = ['Rear View Mirror', 'Front Lamp', 'Rear Lamp', 'Antenna']
print(f"\n🎯 CHECKING PROBLEMATIC CATEGORIES:")
for cat in problem_cats:
    if cat in category_roles:
        roles = category_roles[cat]
        parent_count = parents.get(cat, 0)  
        child_count = children.get(cat, 0)
        print(f"   • '{cat}': {roles} (as parent: {parent_count}x, as child: {child_count}x)")
    else:
        print(f"   • '{cat}': NOT FOUND in database")

cursor.close()
conn.close()