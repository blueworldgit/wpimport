#!/usr/bin/env python3
"""Quick category count checker"""
import requests
from requests.auth import HTTPBasicAuth

# Load credentials  
with open('productioncreds.txt', 'r') as f:
    lines = f.readlines()
    woo_url = lines[0].strip()
    consumer_key = lines[1].strip()  
    consumer_secret = lines[2].strip()

# Get all categories
auth = HTTPBasicAuth(consumer_key, consumer_secret)
response = requests.get(f'{woo_url}/wp-json/wc/v3/products/categories', 
                       auth=auth, 
                       params={'per_page': 100, 'orderby': 'id', 'order': 'desc'})

if response.status_code == 200:
    categories = response.json()
    print(f'📊 Total categories returned: {len(categories)}')
    
    # Count by hierarchy level
    maxus_cats = [c for c in categories if 'Maxus' in c['name']]
    serial_cats = [c for c in categories if 'LSFAL11A4PA157987' in c['name']]
    
    print(f'🏢 Maxus brand categories: {len(maxus_cats)}')
    print(f'🚗 LSFAL11A4PA157987 serial categories: {len(serial_cats)}')
    
    # Check parent relationships
    maxus_id = maxus_cats[0]['id'] if maxus_cats else None
    serial_id = serial_cats[0]['id'] if serial_cats else None
    
    if maxus_id and serial_id:
        parent_cats = [c for c in categories if c.get('parent') == serial_id]
        child_cats = []
        for parent_cat in parent_cats:
            children = [c for c in categories if c.get('parent') == parent_cat['id']]
            child_cats.extend(children)
        
        print(f'📂 Parent categories under serial: {len(parent_cats)}')
        print(f'📄 Child categories under parents: {len(child_cats)}')
        print(f'🧮 Total hierarchy: 1 + 1 + {len(parent_cats)} + {len(child_cats)} = {2 + len(parent_cats) + len(child_cats)}')
        
        print(f'\n📋 Oscar DB Expected: 1 brand + 1 serial + 47 parents + 155 children = 204 total')
        print(f'📊 WordPress Actual: 1 brand + 1 serial + {len(parent_cats)} parents + {len(child_cats)} children = {2 + len(parent_cats) + len(child_cats)} total')
        
        if (2 + len(parent_cats) + len(child_cats)) != 204:
            print(f'❌ MISMATCH: Missing {204 - (2 + len(parent_cats) + len(child_cats))} categories')
        else:
            print(f'✅ PERFECT MATCH!')
    
    else:
        print(f'❌ Could not find Maxus or Serial categories')
        
else:
    print(f'❌ Error: {response.status_code}')