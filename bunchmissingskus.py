"""
Find first 500 products with no SKU using WooCommerce API and output their IDs to missingskus.txt
"""
from woocommerce import API

# API Credentials (reuse from test_api_connection.py)
WP_URL = "https://maxusvanparts.acstestweb.co.uk/"
CONSUMER_KEY = "ck_25e08d3d9ab1625648f25ccefa4080e8497f7c69"
CONSUMER_SECRET = "cs_d493ee9d22846bb489fd20e7a07b494199b3cfd2"

def find_first_500_products_no_sku():
    wcapi = API(
        url=WP_URL,
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET,
        version="wc/v3",
        timeout=30
    )
    print("Searching for products with no SKU...")
    missing_sku_ids = []
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
            sku = product.get("sku")
            if sku is None or sku == "":
                missing_sku_ids.append(str(product.get("id")))
                if len(missing_sku_ids) >= 500:
                    break
        print(f"Checked page {page}, found {len(missing_sku_ids)} products with no SKU so far...")
        if len(missing_sku_ids) >= 500:
            break
        page += 1
    # Write first 500 IDs to file (IDs only, one per line)
    with open("missingskus.txt", "w", encoding="utf-8") as f:
        for pid in missing_sku_ids[:500]:
            f.write(f"{pid}\n")
    print(f"\nTotal products with no SKU (up to 500): {min(len(missing_sku_ids), 500)}")

if __name__ == "__main__":
    find_first_500_products_no_sku()
