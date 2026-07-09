#!/usr/bin/env python3
import requests

WORDPRESS_URL = "https://maxusvanparts.co.uk"
CK = "ck_031fe577565b3791987f7ac730289c812ce45792"
CS = "cs_16beafbb037f53bce1a6308afd15b75a6caa5edb"

# Search by partial serial
r = requests.get(
    f'{WORDPRESS_URL}/wp-json/wc/v3/products/categories',
    params={'per_page': 100, 'search': 'LSH14C4'},
    auth=(CK, CS)
)
print(f'HTTP {r.status_code}')
cats = r.json()
if isinstance(cats, list):
    print(f'Search "LSH14C4" returned {len(cats)} results:')
    for c in cats:
        print(f'  ID:{c["id"]}  parent:{c["parent"]}  name: "{c["name"]}"')
else:
    print(f'Error response: {cats}')
