"""
Remove all products with no SKU using WooCommerce API
Permanently deletes products (bypasses trash)
"""
from woocommerce import API
import time

# API Credentials
WP_URL = "https://maxusvanparts.acstestweb.co.uk/"
CONSUMER_KEY = "ck_25e08d3d9ab1625648f25ccefa4080e8497f7c69"
CONSUMER_SECRET = "cs_d493ee9d22846bb489fd20e7a07b494199b3cfd2"

def remove_products_no_sku():
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
    total_pages = None
    
    # First, collect all product IDs with missing SKUs
    while True:
        response = wcapi.get("products", params={"per_page": 100, "page": page})
        if response.status_code != 200:
            print(f"Failed to fetch products on page {page}: {response.status_code}")
            break
        
        # Get total pages from headers on first request
        if total_pages is None and 'X-WP-TotalPages' in response.headers:
            total_pages = int(response.headers['X-WP-TotalPages'])
            total_products = response.headers.get('X-WP-Total', 'unknown')
            print(f"Total products: {total_products}, Total pages: {total_pages}")
        
        products = response.json()
        if not products:
            break
        
        for product in products:
            sku = product.get("sku")
            if sku is None or sku == "":
                missing_sku_ids.append(product.get("id"))
        
        # Show progress with page info
        page_info = f"/{total_pages}" if total_pages else ""
        print(f"Checked page {page}{page_info}, found {len(missing_sku_ids)} products with no SKU so far...")
        
        # Stop if we've reached the last page
        if total_pages and page >= total_pages:
            break
        
        page += 1
    
    print(f"\nTotal products with no SKU: {len(missing_sku_ids)}")
    
    if not missing_sku_ids:
        print("No products to delete.")
        return
    
    # Confirm before deleting
    confirm = input(f"\nAre you sure you want to PERMANENTLY DELETE {len(missing_sku_ids)} products? (yes/no): ")
    if confirm.lower() != "yes":
        print("Deletion cancelled.")
        return
    
    # Delete products permanently using batch API (up to 100 per request)
    print("\nDeleting products in batches...")
    deleted_count = 0
    failed_count = 0
    batch_size = 100
    
    for i in range(0, len(missing_sku_ids), batch_size):
        batch = missing_sku_ids[i:i + batch_size]
        batch_data = {
            "delete": [{"id": product_id} for product_id in batch]
        }
        
        try:
            response = wcapi.post("products/batch", data=batch_data, params={"force": True})
            if response.status_code == 200:
                result = response.json()
                deleted = result.get("delete", [])
                deleted_count += len(deleted)
                print(f"Batch {i//batch_size + 1}: Deleted {len(deleted)} products (Total: {deleted_count}/{len(missing_sku_ids)})")
            else:
                failed_count += len(batch)
                print(f"Batch {i//batch_size + 1}: Failed with status {response.status_code}")
        except Exception as e:
            failed_count += len(batch)
            print(f"Batch {i//batch_size + 1}: Error - {e}")
        
        # Small delay between batches
        if i + batch_size < len(missing_sku_ids):
            time.sleep(0.5)
    
    print(f"\n=== Deletion Summary ===")
    print(f"Successfully deleted: {deleted_count}")
    print(f"Failed to delete: {failed_count}")
    print(f"Total processed: {len(missing_sku_ids)}")

if __name__ == "__main__":
    remove_products_no_sku()
