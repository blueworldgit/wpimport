"""
Find all products with no SKU using WooCommerce API
"""
from woocommerce import API
import json

# API Credentials (reuse from test_api_connection.py)
WP_URL = "https://maxusvanparts.acstestweb.co.uk/"
CONSUMER_KEY = "ck_25e08d3d9ab1625648f25ccefa4080e8497f7c69"
CONSUMER_SECRET = "cs_d493ee9d22846bb489fd20e7a07b494199b3cfd2"

def find_products_no_sku():
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
                if len(missing_sku_ids) >= 4:
                    break
        print(f"Checked page {page}, found {len(missing_sku_ids)} products with no SKU so far...")
        if len(missing_sku_ids) >= 4:
            break
        page += 1
    # Write first 4 IDs to file
    with open("missingskus.txt", "w", encoding="utf-8") as f:
        for pid in missing_sku_ids[:4]:
            f.write(pid + "\n")
    print(f"\nTotal products with no SKU (up to 4): {min(len(missing_sku_ids), 4)}")

    # Test existence of each post ID
    print("\nTesting existence of each post ID:")
    for pid in missing_sku_ids[:4]:
        resp = wcapi.get(f"products/{pid}")
        if resp.status_code == 200:
            print(f"\nProduct ID {pid} exists. Full details:")
            try:
                details = resp.json()
                print(json.dumps(details, indent=2))
                # Print admin edit URL
                admin_url = f"{WP_URL.rstrip('/')}/wp-admin/post.php?post={pid}&action=edit"
                print(f"Admin edit URL: {admin_url}")
            except Exception as e:
                print(f"Error decoding JSON for product {pid}: {e}")
        else:
            print(f"Product ID {pid} does NOT exist. Status: {resp.status_code}")

if __name__ == "__main__":
    find_products_no_sku()