"""
Cleanup Test Products
Deletes test products from WooCommerce
"""
from woocommerce import API

# Load API keys
with open('keys.txt', 'r') as f:
    lines = f.readlines()
    consumer_key = lines[0].strip()
    consumer_secret = lines[1].strip()

# Initialize WooCommerce API
api = API(
    url='http://localhost/maxusparts/',
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    version='wc/v3'
)

# Test SKUs to delete
test_skus = [
    'C00041192', 'C00017370', 'C00074268', 'C00176662',
    'C00176661', 'C00176660', 'C00050803', 'B00005370', 'C00074269'
]

print("Fetching products...")
response = api.get('products', params={'per_page': 100})

if response.status_code != 200:
    print(f"Error fetching products: {response.status_code}")
    print(response.text)
    exit(1)

products = response.json()

deleted = 0
for product in products:
    if product.get('sku') in test_skus:
        print(f"Deleting {product['sku']}: {product['name']}")
        del_response = api.delete(f"products/{product['id']}", params={'force': True})
        if del_response.status_code == 200:
            deleted += 1
        else:
            print(f"  Failed: {del_response.status_code}")

print(f"\n✓ Deleted {deleted} test products")
