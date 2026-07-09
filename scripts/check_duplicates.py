#!/usr/bin/env python3
"""
Check for and optionally remove duplicate products in WooCommerce
"""
import requests
from pathlib import Path
import sys
from collections import defaultdict

# Add parent directory to path for imports
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))

from config import WORDPRESS_URL

def load_credentials():
    """Load WooCommerce credentials"""
    keys_file = base_dir / 'keys.txt'
    if not keys_file.exists():
        raise FileNotFoundError("keys.txt not found")
    
    with open(keys_file, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    
    consumer_key = None
    consumer_secret = None
    
    for i, line in enumerate(lines):
        if 'Consumer key' in line and i+1 < len(lines): 
            consumer_key = lines[i+1]
        if 'Consumer secret' in line and i+1 < len(lines): 
            consumer_secret = lines[i+1]
    
    if not consumer_key or not consumer_secret:
        raise Exception("WooCommerce credentials not found in keys.txt")
    
    return consumer_key, consumer_secret


def get_all_products(consumer_key, consumer_secret, serial_filter=None):
    """Get all products from WooCommerce"""
    print("📦 Fetching all products from WooCommerce...")
    
    session = requests.Session()
    session.auth = (consumer_key, consumer_secret)
    
    all_products = []
    page = 1
    
    while True:
        url = f"{WORDPRESS_URL}/wp-json/wc/v3/products"
        params = {'per_page': 100, 'page': page}
        
        if serial_filter:
            # Filter by serial in product name or meta
            params['search'] = serial_filter
        
        print(f"   Fetching page {page}...", end='\r')
        
        response = session.get(url, params=params)
        if response.status_code != 200:
            print(f"\n   ❌ Failed with status {response.status_code}")
            break
        
        products = response.json()
        if not products:
            print(f"\n   ✅ Completed at page {page}")
            break
        
        all_products.extend(products)
        page += 1
    
    session.close()
    
    print(f"\n✅ Found {len(all_products)} total products")
    return all_products


def find_duplicates(products):
    """Find duplicate products by SKU"""
    print("\n🔍 Analyzing for duplicates...")
    
    sku_groups = defaultdict(list)
    
    for product in products:
        sku = product.get('sku', '')
        if sku:
            sku_groups[sku].append(product)
    
    # Find SKUs with multiple products
    duplicates = {sku: prods for sku, prods in sku_groups.items() if len(prods) > 1}
    
    if duplicates:
        print(f"\n⚠️  DUPLICATES FOUND: {len(duplicates)} SKUs have duplicates")
        print(f"   Total duplicate products: {sum(len(prods) for prods in duplicates.values())}")
        
        # Show examples
        print("\n   Examples:")
        for i, (sku, prods) in enumerate(list(duplicates.items())[:5]):
            print(f"\n   {i+1}. SKU: {sku} ({len(prods)} instances)")
            for prod in prods:
                print(f"      - ID: {prod['id']}, Name: {prod['name'][:50]}")
        
        if len(duplicates) > 5:
            print(f"\n   ... and {len(duplicates)-5} more duplicate SKUs")
    else:
        print("\n✅ No duplicates found!")
    
    return duplicates


def remove_duplicate_products(duplicates, consumer_key, consumer_secret, dry_run=True):
    """Remove duplicate products, keeping only the first one for each SKU"""
    if not duplicates:
        print("\nℹ️  No duplicates to remove")
        return
    
    if dry_run:
        print("\n🔍 DRY RUN - No products will be deleted")
    else:
        print("\n⚠️  DELETING DUPLICATE PRODUCTS")
    
    session = requests.Session()
    session.auth = (consumer_key, consumer_secret)
    
    total_to_delete = 0
    for sku, prods in duplicates.items():
        # Keep the first product, delete the rest
        total_to_delete += len(prods) - 1
    
    print(f"   Products to delete: {total_to_delete}")
    
    if not dry_run:
        confirm = input("\n   Type 'DELETE' to confirm deletion: ")
        if confirm != 'DELETE':
            print("   ❌ Deletion cancelled")
            session.close()
            return
    
    deleted_count = 0
    
    for sku, prods in duplicates.items():
        # Sort by ID to keep the oldest one
        prods_sorted = sorted(prods, key=lambda p: p['id'])
        
        # Keep first, delete rest
        keep_product = prods_sorted[0]
        delete_products = prods_sorted[1:]
        
        print(f"\n   SKU: {sku}")
        print(f"      Keeping: ID {keep_product['id']}")
        
        for prod in delete_products:
            product_id = prod['id']
            print(f"      Deleting: ID {product_id}...", end='')
            
            if not dry_run:
                url = f"{WORDPRESS_URL}/wp-json/wc/v3/products/{product_id}"
                params = {'force': True}  # Permanently delete
                
                response = session.delete(url, params=params)
                if response.status_code == 200:
                    print(" ✅")
                    deleted_count += 1
                else:
                    print(f" ❌ (Status {response.status_code})")
            else:
                print(" [DRY RUN]")
    
    session.close()
    
    if dry_run:
        print(f"\n✅ Dry run complete. Would delete {total_to_delete} duplicate products")
    else:
        print(f"\n✅ Deleted {deleted_count} duplicate products")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Check for and remove duplicate WooCommerce products')
    parser.add_argument('--serial', help='Filter by vehicle serial')
    parser.add_argument('--delete', action='store_true', help='Actually delete duplicates (default is dry-run)')
    
    args = parser.parse_args()
    
    print("🔧 WooCommerce Duplicate Checker")
    print("=" * 60)
    
    # Load credentials
    consumer_key, consumer_secret = load_credentials()
    print("✅ Credentials loaded")
    
    # Get all products
    products = get_all_products(consumer_key, consumer_secret, serial_filter=args.serial)
    
    # Find duplicates
    duplicates = find_duplicates(products)
    
    # Remove duplicates if requested
    if duplicates:
        remove_duplicate_products(duplicates, consumer_key, consumer_secret, dry_run=not args.delete)


if __name__ == "__main__":
    main()
