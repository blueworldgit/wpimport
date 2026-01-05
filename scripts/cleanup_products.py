"""
Cleanup Script - Delete all WooCommerce products
Use this to start fresh before a new import
"""
import sys
from pathlib import Path
from woocommerce import API

# Add parent directory to path for config
base_dir = Path(__file__).parent.parent
sys.path.insert(0, str(base_dir))

from config import WORDPRESS_URL

def delete_all_products():
    """Delete all products from WooCommerce"""
    
    # Load keys
    keys_file = base_dir / 'keys.txt'
    with open(keys_file, 'r') as f:
        content = f.read().strip()
        lines = content.split('\n')
        consumer_key = None
        consumer_secret = None
        
        for i, line in enumerate(lines):
            if 'ck_' in line:
                consumer_key = line.strip()
            elif 'cs_' in line:
                consumer_secret = line.strip()
    
    # Initialize API
    wcapi = API(
        url=WORDPRESS_URL,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        version="wc/v3",
        timeout=30
    )
    
    print("\n" + "="*60)
    print("WooCommerce Product Cleanup")
    print("="*60)
    print(f"WordPress URL: {WORDPRESS_URL}\n")
    
    # Get all products
    print("Fetching all products...")
    all_products = []
    page = 1
    
    while True:
        response = wcapi.get("products", params={"per_page": 100, "page": page})
        if response.status_code != 200:
            print(f"Error fetching products: {response.status_code}")
            break
        
        products = response.json()
        if not products:
            break
        
        all_products.extend(products)
        print(f"  Found {len(products)} products on page {page}")
        page += 1
    
    total = len(all_products)
    print(f"\n✓ Total products found: {total}")
    
    if total == 0:
        print("\nNo products to delete. Database is clean!")
        return
    
    # Confirm deletion
    print(f"\n⚠️  WARNING: This will DELETE ALL {total} products!")
    confirm = input("Type 'DELETE' to confirm: ")
    
    if confirm != 'DELETE':
        print("\n✗ Cancelled. No products were deleted.")
        return
    
    # Delete products in batches
    print(f"\nDeleting {total} products...")
    batch_size = 100
    deleted = 0
    errors = 0
    
    for i in range(0, total, batch_size):
        batch = all_products[i:i+batch_size]
        batch_ids = [{"id": p["id"]} for p in batch]
        
        # Use batch delete endpoint
        response = wcapi.post("products/batch", {
            "delete": batch_ids
        })
        
        if response.status_code == 200:
            result = response.json()
            deleted += len(result.get('delete', []))
            print(f"  Deleted batch {i//batch_size + 1}: {len(result.get('delete', []))} products")
        else:
            errors += len(batch_ids)
            print(f"  ✗ Error deleting batch {i//batch_size + 1}: {response.status_code}")
    
    print("\n" + "="*60)
    print("Cleanup Summary")
    print("="*60)
    print(f"Total products: {total}")
    print(f"Deleted: {deleted}")
    print(f"Errors: {errors}")
    print("="*60 + "\n")
    
    if errors == 0:
        print("✓ All products deleted successfully!")
        print("✓ Database is clean and ready for new import.\n")
    else:
        print(f"⚠️  {errors} products failed to delete. Please check manually.\n")

if __name__ == "__main__":
    delete_all_products()
