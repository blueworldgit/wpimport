#!/usr/bin/env python3
"""
Quick script to check current category count in WooCommerce
"""
from pathlib import Path
import sys
import argparse
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

parser = argparse.ArgumentParser()
parser.add_argument('--serial', default=None, help='Serial/VIN to inspect category tree for')
args = parser.parse_args()

print("WooCommerce Category Status Check")
print("="*50)

# Fetch all categories (paginated)
all_cats = []
page = 1
while True:
    r = wcapi.get('products/categories', params={'per_page': 100, 'page': page})
    if r.status_code != 200:
        print(f"Failed to fetch categories: {r.status_code}")
        exit(1)
    batch = r.json()
    if not batch:
        break
    all_cats.extend(batch)
    if len(batch) < 100:
        break
    page += 1

print(f"Total categories: {len(all_cats)}")

if args.serial:
    # Find VIN category
    vin_cat = next((c for c in all_cats if c['name'] == args.serial), None)
    if not vin_cat:
        print(f"\nNo category found with name '{args.serial}'")
        exit(1)

    vin_id = vin_cat['id']
    print(f"\nVIN category: {vin_cat['name']}  (ID {vin_id}, parent={vin_cat['parent']})")

    parents = [c for c in all_cats if c['parent'] == vin_id]
    parent_ids = {c['id'] for c in parents}
    children = [c for c in all_cats if c['parent'] in parent_ids]

    print(f"Parent categories ({len(parents)}):")
    for p in sorted(parents, key=lambda x: x['id']):
        kids = [c for c in children if c['parent'] == p['id']]
        print(f"   {p['id']:5d}: {p['name']}  ({len(kids)} children)")
        for k in sorted(kids, key=lambda x: x['id']):
            print(f"          {k['id']:5d}: {k['name']}")

    print(f"\nSummary: 1 VIN + {len(parents)} parents + {len(children)} children = {1 + len(parents) + len(children)} total")

else:
    # Show 10 most recent
    recent = sorted(all_cats, key=lambda x: x['id'], reverse=True)[:10]
    print(f"\nMost recently created categories (last 10):")
    for cat in recent:
        print(f"   {cat['id']:5d}: {cat['name']}  (parent={cat['parent']})")