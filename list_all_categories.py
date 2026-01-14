#!/usr/bin/env python3
"""List all categories in detail"""
import requests
from requests.auth import HTTPBasicAuth

def load_credentials():
    # Try keys.txt first (same as check_categories.py)
    try:
        with open('keys.txt', 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            # Find consumer key and secret
            consumer_key = consumer_secret = None
            for i, line in enumerate(lines):
                if 'Consumer key' in line and i+1 < len(lines):
                    consumer_key = lines[i+1]
                elif 'Consumer secret' in line and i+1 < len(lines):
                    consumer_secret = lines[i+1]
            
            if consumer_key and consumer_secret:
                return "https://maxusvanparts.co.uk/", consumer_key, consumer_secret
    except FileNotFoundError:
        pass
    
    # Fall back to productioncreds.txt
    with open('productioncreds.txt', 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
        return lines[0], lines[1], lines[2]

woo_url, consumer_key, consumer_secret = load_credentials()
auth = HTTPBasicAuth(consumer_key, consumer_secret)

print("🔍 Fetching ALL categories from WordPress...")

page = 1
all_categories = []

while True:
    url = f"{woo_url}/wp-json/wc/v3/products/categories"
    params = {'per_page': 100, 'page': page, 'orderby': 'id', 'order': 'asc'}
    
    response = requests.get(url, params=params, auth=auth)
    if response.status_code != 200:
        print(f"❌ Error {response.status_code}: {response.text}")
        break
    
    categories = response.json()
    if not categories:
        break
    
    all_categories.extend(categories)
    page += 1
    print(f"   📄 Loaded page {page-1} with {len(categories)} categories...")

print(f"\n📊 TOTAL CATEGORIES FOUND: {len(all_categories)}")

if len(all_categories) == 0:
    print("✅ All categories successfully deleted!")
elif len(all_categories) == 1 and all_categories[0]['name'] == 'Uncategorized':
    print("✅ Only 'Uncategorized' remains (this is correct!)")
    print(f"   📝 Uncategorized: ID={all_categories[0]['id']}, Parent={all_categories[0].get('parent', 0)}")
else:
    print(f"❌ Found {len(all_categories)} categories - expected 0 or 1 (Uncategorized)")
    print("\n📋 ALL CATEGORIES:")
    for i, cat in enumerate(all_categories[:20]):  # Show first 20
        print(f"   {i+1:3d}. {cat['name']} (ID: {cat['id']}, Parent: {cat.get('parent', 0)})")
    
    if len(all_categories) > 20:
        print(f"   ... and {len(all_categories) - 20} more categories")
    
    # Check for our test categories
    maxus_cats = [c for c in all_categories if 'Maxus' in c['name']]
    serial_cats = [c for c in all_categories if 'LSFAL11A4PA157987' in c['name']]
    
    if maxus_cats or serial_cats:
        print(f"\n🚗 Vehicle categories found:")
        print(f"   📦 Maxus brand categories: {len(maxus_cats)}")
        print(f"   🚗 LSFAL11A4PA157987 serial categories: {len(serial_cats)}")
        
        if maxus_cats:
            print(f"   📝 Maxus: {maxus_cats[0]['name']} (ID: {maxus_cats[0]['id']})")
        if serial_cats:
            print(f"   📝 Serial: {serial_cats[0]['name']} (ID: {serial_cats[0]['id']})")