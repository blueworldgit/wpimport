import requests
from config import WORDPRESS_URL

ck = 'ck_f1afc5dfb58879e9f5cb2a00e2d0a80c3d72275c'
cs = 'cs_4d5dd541b8f50d4c562462bd4fc0c1c814c7c4b3'
base = WORDPRESS_URL.rstrip('/') + '/wp-json/custom/v1/products-by-sku'
auth = {'consumer_key': ck, 'consumer_secret': cs}

for sku in ['C00021127', 'C00058223', 'C00074560', 'B00005870', 'B00004124']:
    r = requests.get(base, params={**auth, 'original_sku': sku}, timeout=15)
    d = r.json()
    print(f"{sku}: found={d.get('found', '?')}")
