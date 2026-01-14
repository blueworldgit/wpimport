#!/usr/bin/env python3
from pathlib import Path
import json
import sys
base_dir = Path(__file__).resolve().parent.parent
# load keys
keys_file = base_dir / 'keys.txt'
consumer_key = None
consumer_secret = None
with open(keys_file,'r',encoding='utf-8') as f:
    lines=[l.strip() for l in f.readlines() if l.strip()]
    for i,line in enumerate(lines):
        if 'Consumer key' in line and i+1<len(lines): consumer_key=lines[i+1]
        if 'Consumer secret' in line and i+1<len(lines): consumer_secret=lines[i+1]

sys.path.insert(0,str(base_dir))
from config import WORDPRESS_URL
from scripts.import_to_woocommerce import WooCommerceImporter
imp = WooCommerceImporter(WORDPRESS_URL, consumer_key, consumer_secret, base_dir / 'data' / 'checkpoints', base_dir / 'logs')
# Repairs list inferred from recent error logs
repairs = {
    11913: [720,721,722],
    11915: [720,721,722]
}
for pid, desired in repairs.items():
    try:
        resp = imp.wcapi.get(f'products/{pid}')
        if resp.status_code!=200:
            print(f'Could not fetch product {pid}:', getattr(resp,'status_code',None))
            continue
        prod = resp.json()
        existing = [c['id'] for c in prod.get('categories',[])]
        merged = list(dict.fromkeys(existing + desired))
        if set(merged)==set(existing):
            print(f'Product {pid} already has desired categories')
            continue
        upd = {'categories': [{'id':c} for c in merged]}
        put = imp.wcapi.put(f'products/{pid}', upd)
        print(f'Patched product {pid}:', put.status_code, put.text[:200])
    except Exception as e:
        print('Error repairing', pid, e)
