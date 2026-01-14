from woocommerce import API
from pathlib import Path

# Load WooCommerce API keys from keys.txt
with open('keys.txt', 'r') as f:
    content = f.read().strip()
    lines = content.split('\n')
    consumer_key = None
    consumer_secret = None
    
    for line in lines:
        if 'ck_' in line:
            consumer_key = line.strip()
        elif 'cs_' in line:
            consumer_secret = line.strip()

from config import WORDPRESS_URL
wcapi = API(url=WORDPRESS_URL, consumer_key=consumer_key, consumer_secret=consumer_secret, version='wc/v3')

# Get one product to see structure
response = wcapi.get('products', params={'per_page': 1})
print(f"Status: {response.status_code}")
products = response.json()

if isinstance(products, list) and len(products) > 0:
    product = products[0]
    print('Product Name:', product.get('name'))
    print('SKU:', product.get('sku'))
    print('Meta Data:')
    for meta in product.get('meta_data', []):
        print(f'  {meta.get("key")}: {meta.get("value")}')
else:
    print("No products found")