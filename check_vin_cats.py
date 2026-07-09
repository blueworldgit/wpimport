import requests

ck = 'ck_f1afc5dfb58879e9f5cb2a00e2d0a80c3d72275c'
cs = 'cs_4d5dd541b8f50d4c562462bd4fc0c1c814c7c4b3'
url = 'https://shane.maxusvanparts.co.uk'

# Find the VIN category
r = requests.get(f'{url}/wp-json/wc/v3/products/categories',
    params={'search': 'LSH14C4C5NA129710', 'per_page': 10}, auth=(ck, cs))
cats = r.json()
print('VIN category search results:')
for c in cats:
    print(f'  ID={c["id"]}  name={c["name"]}  parent={c["parent"]}  count={c["count"]}')

if cats:
    vin_id = cats[0]['id']
    r2 = requests.get(f'{url}/wp-json/wc/v3/products/categories',
        params={'parent': vin_id, 'per_page': 100}, auth=(ck, cs))
    children = r2.json()
    print(f'\nChild categories of VIN {vin_id}: {len(children)}')
    for c in children:
        print(f'  ID={c["id"]}  name={c["name"]}  count={c["count"]}')
    if not children:
        print('  >>> CONFIRMED: Zero child categories - products are flat under VIN <<<')
