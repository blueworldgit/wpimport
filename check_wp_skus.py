"""
Check if C-prefix SKUs exist in WP at all, regardless of original_sku meta.
Searches by WC SKU prefix using the REST API.
"""
import requests
from config import WORDPRESS_URL

ck = 'ck_f1afc5dfb58879e9f5cb2a00e2d0a80c3d72275c'
cs = 'cs_4d5dd541b8f50d4c562462bd4fc0c1c814c7c4b3'
auth = (ck, cs)
base = WORDPRESS_URL.rstrip('/')

skus = ['C00021127', 'C00058223', 'C00074560', 'B00005870']

for sku in skus:
    # Exact WC sku match
    r = requests.get(f"{base}/wp-json/wc/v3/products",
                     params={'sku': sku, 'per_page': 5},
                     auth=auth, timeout=15)
    products = r.json() if r.status_code == 200 else []
    if products:
        for p in products:
            print(f"{sku}: WC product found - ID={p['id']} sku={p['sku']} name={p['name'][:50]}")
        continue

    # Try SKU with suffix pattern via search
    r2 = requests.get(f"{base}/wp-json/wc/v3/products",
                      params={'sku': f"{sku}-", 'per_page': 5},
                      auth=auth, timeout=15)
    products2 = r2.json() if r2.status_code == 200 else []
    if products2:
        for p in products2:
            print(f"{sku}: WC product (suffix) - ID={p['id']} sku={p['sku']}")
    else:
        print(f"{sku}: NOT FOUND in WP at all (no WC product with this SKU)")
