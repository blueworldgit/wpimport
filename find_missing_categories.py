#!/usr/bin/env python3
"""Find missing categories by comparing expected vs actual"""
import psycopg2
import requests
from requests.auth import HTTPBasicAuth

def load_woo_credentials():
    with open('keys.txt', 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
        consumer_key = consumer_secret = None
        for i, line in enumerate(lines):
            if 'Consumer key' in line and i+1 < len(lines):
                consumer_key = lines[i+1]
            elif 'Consumer secret' in line and i+1 < len(lines):
                consumer_secret = lines[i+1]
        return "https://maxusvanparts.co.uk/", consumer_key, consumer_secret

def load_db_credentials():
    with open('productioncreds.txt', 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
        return lines[3], lines[4], lines[5], lines[6], lines[7]  # host, db, user, password, port

def sanitize_category_name(name):
    if not name:
        return ""
    return name.replace('&', 'and').replace('/', '').replace('\\', '').strip()

print("🔍 Finding Missing Categories...")

# Connect to Oscar database
host, database, user, password, port = load_db_credentials()
conn = psycopg2.connect(
    host=host, database=database, user=user, password=password, port=port
)

# Get expected categories from Oscar
cursor = conn.cursor()
query = """
SELECT DISTINCT
    p.vehicle_brand,
    p.serial,
    p.parent_category,
    p.child_category
FROM parts p
WHERE p.serial = 'LSFAL11A4PA157987'
ORDER BY p.parent_category, p.child_category
"""

cursor.execute(query)
rows = cursor.fetchall()

# Build expected hierarchy
expected_categories = set()
expected_categories.add("Maxus")  # Brand
expected_categories.add("LSFAL11A4PA157987")  # Serial

for row in rows:
    parent = sanitize_category_name(row[2])
    child = sanitize_category_name(row[3])
    expected_categories.add(parent)
    expected_categories.add(child)

cursor.close()
conn.close()

print(f"📊 Expected categories from Oscar DB: {len(expected_categories)}")

# Get actual categories from WordPress
woo_url, consumer_key, consumer_secret = load_woo_credentials()
auth = HTTPBasicAuth(consumer_key, consumer_secret)

actual_categories = set()
page = 1

while True:
    url = f"{woo_url}/wp-json/wc/v3/products/categories"
    params = {'per_page': 100, 'page': page}
    
    response = requests.get(url, params=params, auth=auth)
    if response.status_code != 200:
        break
    
    categories = response.json()
    if not categories:
        break
    
    for cat in categories:
        if cat['name'] != 'Uncategorized':  # Skip default WordPress category
            actual_categories.add(cat['name'])
    
    page += 1

print(f"📊 Actual categories in WordPress: {len(actual_categories)}")

# Find missing categories
missing = expected_categories - actual_categories
extra = actual_categories - expected_categories

print(f"\n❌ MISSING CATEGORIES ({len(missing)}):")
for i, cat in enumerate(sorted(missing), 1):
    print(f"   {i:2d}. {cat}")

if extra:
    print(f"\n➕ EXTRA CATEGORIES ({len(extra)}):")
    for i, cat in enumerate(sorted(extra), 1):
        print(f"   {i:2d}. {cat}")

if len(missing) == 4:
    print(f"\n💡 These 4 missing categories are likely the ones that triggered")
    print(f"   'SEARCH FOUND EXISTING' messages during script execution.")
    print(f"\n🔧 Possible causes:")
    print(f"   • Special characters causing API conflicts")
    print(f"   • Names too long for WordPress")
    print(f"   • Name collisions with existing categories")
    print(f"   • Race conditions in async creation")
elif len(missing) == 0:
    print(f"\n✅ All expected categories found!")
else:
    print(f"\n⚠️  Expected 4 missing categories, found {len(missing)}")