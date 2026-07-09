#!/usr/bin/env python3
"""
Analyze WordPress products to find duplicates and issues
"""
import requests
from pathlib import Path
import sys
from collections import Counter, defaultdict

# Add parent directory to path for imports
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))

from config import WORDPRESS_URL

def load_credentials():
    """Load WooCommerce credentials"""
    keys_file = base_dir / 'keys.txt'
    with open(keys_file, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    
    consumer_key = None
    consumer_secret = None
    
    for i, line in enumerate(lines):
        if 'Consumer key' in line and i+1 < len(lines): 
            consumer_key = lines[i+1]
        if 'Consumer secret' in line and i+1 < len(lines): 
            consumer_secret = lines[i+1]
    
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


def analyze_products(products, serial_filter=None):
    """Analyze products for duplicates and anomalies"""
    print("\n📊 ANALYZING PRODUCTS")
    print("=" * 60)
    
    # Count by SKU
    sku_counter = Counter()
    sku_to_products = defaultdict(list)
    original_sku_counter = Counter()
    products_without_sku = []
    
    for product in products:
        sku = product.get('sku', '')
        if sku:
            sku_counter[sku] += 1
            sku_to_products[sku].append(product)
            
            # Extract original SKU
            if '-' in sku:
                original_sku = sku.rsplit('-', 1)[0]
                original_sku_counter[original_sku] += 1
        else:
            products_without_sku.append(product)
    
    print(f"\n📋 SUMMARY:")
    print(f"   Total products: {len(products)}")
    print(f"   Unique SKUs: {len(sku_counter)}")
    print(f"   Products without SKU: {len(products_without_sku)}")
    print(f"   Unique original part numbers: {len(original_sku_counter)}")
    
    # Find duplicate SKUs
    duplicate_skus = {sku: count for sku, count in sku_counter.items() if count > 1}
    if duplicate_skus:
        print(f"\n⚠️  DUPLICATE SKUs: {len(duplicate_skus)} SKUs appear multiple times")
        print(f"   Total duplicate products: {sum(duplicate_skus.values())}")
        for sku, count in list(duplicate_skus.items())[:10]:
            print(f"      {sku}: {count} instances")
            for prod in sku_to_products[sku][:3]:
                print(f"         - ID {prod['id']}: {prod['name'][:50]}")
    else:
        print(f"\n✅ No duplicate SKUs found")
    
    # Analyze original part numbers with many variations
    high_variation_parts = {sku: count for sku, count in original_sku_counter.items() if count > 20}
    if high_variation_parts:
        print(f"\n📈 HIGH VARIATION PARTS (>20 variations):")
        for original_sku, count in sorted(high_variation_parts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {original_sku}: {count} variations")
            # Show some examples
            matching_products = [p for p in products if p.get('sku', '').startswith(original_sku + '-')]
            for prod in matching_products[:3]:
                print(f"      - {prod['sku']}: {prod['name'][:40]}")
    
    # Check for expected count
    if serial_filter:
        print(f"\n🔍 Serial filter: {serial_filter}")
    
    return {
        'total': len(products),
        'unique_skus': len(sku_counter),
        'duplicate_skus': len(duplicate_skus),
        'original_parts': len(original_sku_counter)
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze WordPress products for duplicates')
    parser.add_argument('--serial', help='Filter by vehicle serial')
    
    args = parser.parse_args()
    
    print("🔧 WordPress Product Analyzer")
    print("=" * 60)
    
    # Load credentials
    consumer_key, consumer_secret = load_credentials()
    print("✅ Credentials loaded")
    
    # Get all products
    products = get_all_products(consumer_key, consumer_secret, serial_filter=args.serial)
    
    # Analyze products
    stats = analyze_products(products, serial_filter=args.serial)
    
    print(f"\n💡 RECOMMENDATIONS:")
    if stats['duplicate_skus'] > 0:
        print(f"   ⚠️  You have {stats['duplicate_skus']} duplicate SKUs")
        print(f"   Run: python scripts\\check_duplicates.py --serial {args.serial or ''} --delete")
    else:
        print(f"   ✅ No duplicates found")
    
    if stats['total'] > stats['original_parts'] * 1.5:
        print(f"   ⚠️  Product count ({stats['total']}) is unusually high")
        print(f"       Expected around {stats['original_parts']} based on unique part numbers")


if __name__ == "__main__":
    main()
