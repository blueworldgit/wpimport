import requests

ck = 'ck_f1afc5dfb58879e9f5cb2a00e2d0a80c3d72275c'
cs = 'cs_4d5dd541b8f50d4c562462bd4fc0c1c814c7c4b3'
url = 'https://shane.maxusvanparts.co.uk'

# 1. Site check
r = requests.get(f'{url}/wp-json/', timeout=5)
print(f'1. WP JSON root: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    print(f'   Site name: {data.get("name")}')
    namespaces = data.get('namespaces', [])
    print(f'   Namespaces: {namespaces}')
    wc_active = 'wc/v3' in namespaces
    print(f'   WC v3 active: {wc_active}')

print()
# 2. WC root without auth (just check it's there)
r2 = requests.get(f'{url}/wp-json/wc/v3', timeout=5)
print(f'2. WC v3 root (no auth): {r2.status_code}: {r2.text[:150]}')

print()
# 3. Basic auth
r3 = requests.get(f'{url}/wp-json/wc/v3/products', params={'per_page': 1}, auth=(ck, cs), timeout=5)
print(f'3. Basic Auth products: {r3.status_code}: {r3.text[:200]}')

print()
# 4. WC system status (requires auth)
r4 = requests.get(f'{url}/wp-json/wc/v3/system_status', auth=(ck, cs), timeout=5)
print(f'4. System status: {r4.status_code}: {r4.text[:200]}')
