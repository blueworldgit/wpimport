import requests

ck = 'ck_f1afc5dfb58879e9f5cb2a00e2d0a80c3d72275c'
cs = 'cs_4d5dd541b8f50d4c562462bd4fc0c1c814c7c4b3'
url = 'https://shane.maxusvanparts.co.uk'

# IDs created in the bad second run (parent=0, IDs 7250+)
bad_ids = [
    7250,7251,7252,7253,7254,7255,7256,7257,7258,7259,
    7260,7261,7262,7263,7264,7265,7266,7267,7268,7269,
    7270,7271,7272,7273,7274,7275,7276,7277,7278,7279,
    7280,7281,7282,7283,7284,7285,7286,7287,7288,7289,7290
]

print(f'Checking {len(bad_ids)} suspected orphan categories...\n')
confirmed_bad = []
for cat_id in bad_ids:
    r = requests.get(f'{url}/wp-json/wc/v3/products/categories/{cat_id}', auth=(ck, cs))
    if r.status_code == 200:
        c = r.json()
        print(f'  ID={c["id"]:>5}  parent={c["parent"]:>5}  name={c["name"]}')
        if c['parent'] == 0:
            confirmed_bad.append(c['id'])
    else:
        print(f'  ID={cat_id} -> {r.status_code} (not found)')

print(f'\nConfirmed orphans (parent=0): {len(confirmed_bad)}')
print(f'IDs: {confirmed_bad}')
