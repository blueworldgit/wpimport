import requests

ck = 'ck_f1afc5dfb58879e9f5cb2a00e2d0a80c3d72275c'
cs = 'cs_4d5dd541b8f50d4c562462bd4fc0c1c814c7c4b3'
url = 'https://shane.maxusvanparts.co.uk'

# Fetch all top-level VIN categories (children of Maxus = 3590)
print('Fetching all VIN categories under Maxus (3590)...\n')
r = requests.get(f'{url}/wp-json/wc/v3/products/categories',
    params={'parent': 3590, 'per_page': 100}, auth=(ck, cs))
vins = r.json()
print(f'Found {len(vins)} VIN categories\n')
print(f'{"VIN":<25} {"ID":>6} {"Products":>9} {"Children":>9} {"Status"}')
print('-' * 70)

for vin in sorted(vins, key=lambda x: x['name']):
    r2 = requests.get(f'{url}/wp-json/wc/v3/products/categories',
        params={'parent': vin['id'], 'per_page': 1}, auth=(ck, cs))
    child_count = int(r2.headers.get('X-WP-Total', len(r2.json())))
    status = 'OK' if child_count > 0 else '*** FLAT - NO SUBCATS ***'
    print(f'{vin["name"]:<25} {vin["id"]:>6} {vin["count"]:>9} {child_count:>9}   {status}')
