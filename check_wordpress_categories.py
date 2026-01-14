#!/usr/bin/env python3
"""Check which categories already exist in WordPress"""
import sys
import os
sys.path.append('scripts')
from fast_create_categories import FastCategoryCreator

# Create an instance
creator = FastCategoryCreator(serial_filter='LSFAL11A4PA157987')
if not creator.connect():
    print("❌ Failed to connect to database")
    sys.exit(1)

creator.load_credentials()

print("🔍 Checking existing WordPress categories...")

# Load existing categories
creator.preload_existing_categories()

# Check which problematic categories exist
problem_categories = ['Rear View Mirror', 'Front Lamp', 'Rear Lamp', 'Antenna', 'Body Interior and Exterior Electronics']

print(f"\n📊 Status of problematic categories in WordPress:")
for cat in problem_categories:
    if cat in creator.existing_categories:
        cat_id = creator.existing_categories[cat]
        print(f"   ✅ '{cat}': EXISTS in WordPress (ID: {cat_id})")
    else:
        print(f"   ❌ '{cat}': NOT found in WordPress")

# Also check how many total categories exist
print(f"\n📊 WordPress category summary:")
print(f"   Total existing categories: {len(creator.existing_categories)}")

# Show a sample of existing categories
existing_names = list(creator.existing_categories.keys())
if len(existing_names) > 10:
    print(f"   Sample categories: {existing_names[:10]}")
else:
    print(f"   All categories: {existing_names}")

creator.conn.close()