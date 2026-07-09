import requests

ck = 'ck_f1afc5dfb58879e9f5cb2a00e2d0a80c3d72275c'
cs = 'cs_4d5dd541b8f50d4c562462bd4fc0c1c814c7c4b3'
url = 'https://shane.maxusvanparts.co.uk'

# All 41 confirmed orphans from the bad second run (parent=0)
orphan_ids = list(range(7250, 7291))

print(f'Batch deleting {len(orphan_ids)} orphan categories in one API call...')
r = requests.post(
    f'{url}/wp-json/wc/v3/products/categories/batch',
    json={'delete': orphan_ids},
    auth=(ck, cs),
    timeout=60
)
print(f'Status: {r.status_code}')
if r.status_code == 200:
    deleted = r.json().get('delete', [])
    print(f'Deleted: {len(deleted)} categories')
else:
    print(f'Error: {r.text[:300]}')

# Quick verify: check a few good ones are still intact
print('\nVerifying good categories still present...')
for cat_id, expected_parent in [(7114, 3590), (7115, 7114), (7121, 7114), (7150, 7114)]:
    r2 = requests.get(f'{url}/wp-json/wc/v3/products/categories/{cat_id}', auth=(ck, cs), timeout=15)
    if r2.status_code == 200:
        c = r2.json()
        status = 'OK' if c['parent'] == expected_parent else f'WRONG PARENT {c["parent"]}'
        print(f'  {status}: ID={cat_id}  name={c["name"]}  parent={c["parent"]}')
    else:
        print(f'  MISSING: ID={cat_id} !!!')
