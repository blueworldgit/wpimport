#!/usr/bin/env python3
"""Test category name sanitization to understand the dual-role issue"""
import re
import sys
import os
sys.path.append('scripts')
from fast_create_categories import FastCategoryCreator

def sanitize_category_name(name):
    """Same sanitization function from fast_create_categories.py"""
    if not name:
        return "Uncategorized"
    
    # Remove diagram codes (JE123A001 - ) from category names
    name = re.sub(r'^[A-Z]{2}\d+[A-Z]?\d+\s*-\s*', '', name)
    
    # Replace problematic characters but keep full length
    sanitized = name.replace('&', 'and').replace('/', '-').replace('\\', '-')
    sanitized = sanitized.replace('(', '').replace(')', '').replace(',', '')
    
    # Clean up extra spaces and dashes
    sanitized = re.sub(r'\s+', ' ', sanitized)
    sanitized = re.sub(r'-+', '-', sanitized)
    
    return sanitized.strip()

# Create an instance to get database connection
creator = FastCategoryCreator(serial_filter='LSFAL11A4PA157987')
if not creator.connect():
    print("❌ Failed to connect to database")
    sys.exit(1)

cursor = creator.conn.cursor()

print("🔍 Checking sanitization impact on dual-role detection...")

# Get all categories with their raw names
cursor.execute("""
    SELECT DISTINCT
        pt.title as parent_category,
        ct.title as child_category
    FROM motorpartsdata_serialnumber sn
    JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
    JOIN motorpartsdata_childtitle ct ON ct.parent_id = pt.id
    WHERE sn.serial = %s
""", ('LSFAL11A4PA157987',))

rows = cursor.fetchall()

# Build sets using sanitized names like the creation script does
all_parents_raw = set()
all_children_raw = set()
all_parents_sanitized = set()
all_children_sanitized = set()

sanitization_changes = {}

for row in rows:
    parent_raw = row[0]
    child_raw = row[1]
    
    parent_sanitized = sanitize_category_name(parent_raw)
    child_sanitized = sanitize_category_name(child_raw)
    
    all_parents_raw.add(parent_raw)
    all_children_raw.add(child_raw)
    all_parents_sanitized.add(parent_sanitized)
    all_children_sanitized.add(child_sanitized)
    
    # Track sanitization changes
    if parent_raw != parent_sanitized:
        sanitization_changes[parent_raw] = parent_sanitized
    if child_raw != child_sanitized:
        sanitization_changes[child_raw] = child_sanitized

print(f"📊 Raw names:")
print(f"   📂 Raw parents: {len(all_parents_raw)}")
print(f"   📄 Raw children: {len(all_children_raw)}")
dual_role_raw = all_parents_raw.intersection(all_children_raw)
print(f"   🔄 Raw dual-role: {len(dual_role_raw)}")

print(f"\n📊 Sanitized names:")
print(f"   📂 Sanitized parents: {len(all_parents_sanitized)}")
print(f"   📄 Sanitized children: {len(all_children_sanitized)}")
dual_role_sanitized = all_parents_sanitized.intersection(all_children_sanitized)
print(f"   🔄 Sanitized dual-role: {len(dual_role_sanitized)}")

if sanitization_changes:
    print(f"\n⚠️  Sanitization changed {len(sanitization_changes)} category names:")
    for original, sanitized in sanitization_changes.items():
        print(f"   '{original}' → '{sanitized}'")

if dual_role_sanitized:
    print(f"\n❓ Sanitized dual-role categories:")
    for cat in sorted(dual_role_sanitized):
        print(f"   • '{cat}'")

cursor.close()
creator.conn.close()