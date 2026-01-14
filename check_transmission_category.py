#!/usr/bin/env python3
"""
Check for the problematic category in WooCommerce
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

wcapi = API(url=WORDPRESS_URL, consumer_key=consumer_key, consumer_secret=consumer_secret, version='wc/v3')

print("🔍 Searching for Transmission Shift categories...")

# Search for the problematic category
response = wcapi.get('products/categories', params={'search': 'Transmission Shift', 'per_page': 20})
if response.status_code == 200:
    categories = response.json()
    print(f'Found {len(categories)} categories with "Transmission Shift":')
    for cat in categories:
        print(f'  ID {cat["id"]:4d}: "{cat["name"]}"')
        # Show character codes for special characters
        special_chars = []
        for c in cat['name']:
            if ord(c) > 127:
                special_chars.append(f'{c}(U+{ord(c):04X})')
        if special_chars:
            print(f'        Special chars: {", ".join(special_chars)}')
else:
    print(f'Failed: {response.status_code}')

# Also check by AT、Electric
print(f"\n🔍 Searching for categories with 'AT、Electric'...")
response = wcapi.get('products/categories', params={'search': 'AT、Electric', 'per_page': 20})
if response.status_code == 200:
    categories = response.json()
    print(f'Found {len(categories)} categories with "AT、Electric":')
    for cat in categories:
        print(f'  ID {cat["id"]:4d}: "{cat["name"]}"')
else:
    print(f'Failed: {response.status_code}')