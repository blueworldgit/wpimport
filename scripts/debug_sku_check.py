#!/usr/bin/env python3
import sys
import json
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent

# load keys
keys_file = base_dir / 'keys.txt'
consumer_key = None
consumer_secret = None
with open(keys_file, 'r', encoding='utf-8') as f:
    lines = [l.strip() for l in f.readlines() if l.strip()]
    for i, line in enumerate(lines):
        if 'Consumer key' in line and i + 1 < len(lines):
            consumer_key = lines[i+1]
        elif 'Consumer secret' in line and i + 1 < len(lines):
            consumer_secret = lines[i+1]

import sys
sys.path.insert(0, str(base_dir))
from config import WORDPRESS_URL
from scripts.import_to_woocommerce import WooCommerceImporter

imp = WooCommerceImporter(WORDPRESS_URL, consumer_key, consumer_secret, base_dir / 'data' / 'checkpoints', base_dir / 'logs')

if len(sys.argv) < 2:
    print('Usage: debug_sku_check.py SKU [SKU ...]')
    sys.exit(2)

for sku in sys.argv[1:]:
    resp = None
    try:
        resp = imp.wcapi.get('products', params={'sku': sku})
    except Exception as e:
        print(f"SKU {sku}: GET request failed: {e}")
        continue

    code = getattr(resp, 'status_code', None)
    print(f"\nSKU: {sku} | status_code: {code}")
    text = ''
    try:
        text = resp.text
        parsed = resp.json()
        print('Response JSON length:', len(parsed) if isinstance(parsed, list) else 'obj')
        if isinstance(parsed, list) and parsed:
            print('First item id,sku:', parsed[0].get('id'), parsed[0].get('sku'))
        else:
            print('Response body:', parsed)
    except Exception:
        print('Raw response text:', text[:1000])

print('\nDone.')
