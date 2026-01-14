from woocommerce import API
import json

API_URL = 'https://maxusvanparts.co.uk/'
CONSUMER_KEY = 'ck_1be77215f05ca7f848ac0ec16a6b68e76ced9302'
CONSUMER_SECRET = 'cs_b2c2be6911c85fe9abc62b4ec5170b9ab746392e'

wcapi = API(url=API_URL, consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET, version='wc/v3')

meta_key = 'original_sku'
meta_value = 'B00003507'

print(f"Querying products with {meta_key}={meta_value}...\n")
resp = wcapi.get('products', params={'meta_key': meta_key, 'meta_value': meta_value, 'per_page': 100})
if resp.status_code != 200:
    print('API error', resp.status_code, resp.text)
    exit(1)
products = resp.json()
print(f"Found {len(products)} products:\n")
for p in products:
    sku = p.get('sku')
    pid = p.get('id')
    name = p.get('name')
    metas = p.get('meta_data', [])
    orig = None
    for m in metas:
        if m.get('key') == 'original_sku':
            orig = m.get('value')
    print(f"ID {pid} SKU {sku} Name: {name}\n  original_sku meta: {orig}\n  meta_data: {json.dumps(metas)}\n")
