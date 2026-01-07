from woocommerce import API

api = API(
    url='https://maxusvanparts.co.uk/',
    consumer_key='ck_1be77215f05ca7f848ac0ec16a6b68e76ced9302',
    consumer_secret='cs_b2c2be6911c85fe9abc62b4ec5170b9ab746392e',
    version='wc/v3'
)

r = api.get('products', params={'per_page': 20})
products = r.json()

print(f'\nTotal products on site: {len(products)}\n')
for p in products:
    images = len(p.get('images', []))
    print(f"  ID {p['id']}: {p['sku']} - {p['name'][:50]} ({images} image{'s' if images != 1 else ''})")
