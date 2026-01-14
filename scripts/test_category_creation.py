#!/usr/bin/env python3
"""
Test specific category creation to debug 400 errors
"""
from pathlib import Path
import sys
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))
from config import WORDPRESS_URL
from scripts.import_to_woocommerce import WooCommerceImporter

# Load WooCommerce credentials
keys_file = base_dir / 'keys.txt'
consumer_key = consumer_secret = None
if keys_file.exists():
    with open(keys_file, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
        for i, line in enumerate(lines):
            if 'Consumer key' in line and i+1 < len(lines): 
                consumer_key = lines[i+1]
            if 'Consumer secret' in line and i+1 < len(lines): 
                consumer_secret = lines[i+1]

# Test problematic categories
test_categories = [
    "Body Upper Structure",
    "Body Interior and Exterior Electronics", 
    "Power Transmission",
    "Refrigerant Plumbing and Hardware-Electric vehicle",
    "Emission Exhaust System"
]

# Create importer
checkpoint_dir = base_dir / 'data' / 'checkpoints_category_test'
log_dir = base_dir / 'logs'
importer = WooCommerceImporter(WORDPRESS_URL, consumer_key, consumer_secret, checkpoint_dir, log_dir)

print("Testing problematic category creation:")
print("=" * 60)

for category_name in test_categories:
    print(f"\nTesting category: '{category_name}'")
    
    # Try to get or create the category
    result = importer.get_or_create_category(category_name, parent_id=0)
    
    if result:
        print(f"  ✓ Success: ID {result}")
    else:
        print(f"  ❌ Failed to create")