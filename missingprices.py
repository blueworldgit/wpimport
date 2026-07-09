"""
Find all SKUs with no price using WooCommerce API
"""
from woocommerce import API
import json

# API Credentials (reuse from test_api_connection.py)
WP_URL = "https://maxusvanparts.acstestweb.co.uk/"
CONSUMER_KEY = "ck_25e08d3d9ab1625648f25ccefa4080e8497f7c69"
CONSUMER_SECRET = "cs_d493ee9d22846bb489fd20e7a07b494199b3cfd2"

def find_skus_no_price():
    wcapi = API(
        url=WP_URL,
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET,
        version="wc/v3",
        timeout=30
    )
    print("Searching for products with no price...")
    skus_no_price = set()
    page = 1
    while True:
        response = wcapi.get("products", params={"per_page": 100, "page": page})
        if response.status_code != 200:
            print(f"Failed to fetch products on page {page}: {response.status_code}")
            break
        products = response.json()
        if not products:
            break
        for product in products:
            price = product.get("price")
            sku = product.get("sku")
            if (price is None or price == "" or price == "0" or price == 0) and sku:
                skus_no_price.add(sku)
                if len(skus_no_price) >= 300:
                    break
        print(f"Checked page {page}, found {len(skus_no_price)} unique SKUs with no price so far...")
        if len(skus_no_price) >= 300:
            break
        page += 1
    print(f"\nTotal unique SKUs with no price (up to 300): {min(len(skus_no_price), 300)}")
    print("\nFirst 300 unique SKUs with no price as array:")
    sku_list = list(skus_no_price)[:300]
    print(f"codes = {sku_list}")

if __name__ == "__main__":
    find_skus_no_price()
