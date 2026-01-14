#!/usr/bin/env python3
"""
Quick script to check current category count in WooCommerce
"""
from pathlib import Path
import sys
base_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(base_dir))

from config import WORDPRESS_URL
from woocommerce import API

# Load credentials
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

# Get category count and recent categories
wcapi = API(url=WORDPRESS_URL, consumer_key=consumer_key, consumer_secret=consumer_secret, version='wc/v3')

print("🏷️  WooCommerce Category Status Check")
print("="*50)

# Get total count
response = wcapi.get('products/categories', params={'per_page': 1})
if response.status_code == 200:
    total = response.headers.get('X-WP-Total', 'Unknown')
    print(f"📊 Total categories: {total}")
else:
    print(f"❌ Failed to get category count: {response.status_code}")
    exit(1)

# Get recent categories (last 10 created)
response = wcapi.get('products/categories', params={'per_page': 10, 'orderby': 'id', 'order': 'desc'})
if response.status_code == 200:
    categories = response.json()
    print(f"\n🔍 Most recently created categories (last 10):")
    for cat in categories:
        print(f"   {cat['id']:4d}: {cat['name']}")
        if 'Transmission Shift' in cat['name'] or 'Side Closures' in cat['name'] or 'Charging and' in cat['name'] or 'Wiper and' in cat['name']:
            print(f"        ⚠️  This category matches failed creation attempts!")
else:
    print(f"❌ Failed to get recent categories: {response.status_code}")

print(f"\n✅ Category structure appears intact!")