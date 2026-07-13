"""
Check products with missing, invalid, or stale date_updated values.
Uses the custom REST endpoint: /wp-json/custom/v1/products-by-date-updated
"""

import requests
from config import WP_URL, WP_CONSUMER_KEY, WP_CONSUMER_SECRET
import sys

def check_date_updated(status='all', days=7, show_all=False):
    """
    Check products by date_updated status.
    
    Args:
        status: 'empty', 'invalid', 'stale', or 'all'
        days: Number of days threshold for stale check
        show_all: If True, fetch all pages; if False, show only first page
    """
    endpoint = f"{WP_URL}/wp-json/custom/v1/products-by-date-updated"
    
    page = 1
    all_products = []
    
    while True:
        params = {
            'status': status,
            'days': days,
            'page': page,
            'per_page': 100
        }
        
        print(f"Fetching page {page}...", end=' ')
        
        try:
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            print(f"Got {len(data['products'])} products")
            
            if page == 1:
                print(f"\nQuery Results:")
                print(f"  Status filter: {data['status']}")
                print(f"  Days threshold: {data['days']}")
                print(f"  Date threshold: {data['date_threshold']}")
                print(f"  Total products: {data['total']}")
                print(f"  Total pages: {data['total_pages']}")
                print()
            
            all_products.extend(data['products'])
            
            # Break if no more pages or if not fetching all
            if page >= data['total_pages'] or (not show_all and page >= 1):
                break
                
            page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"\nError fetching data: {e}")
            return None
    
    return all_products

def display_products(products, limit=50):
    """Display products in a formatted table."""
    if not products:
        print("No products found matching criteria.")
        return
    
    print(f"\n{'ID':<8} {'SKU':<20} {'Original SKU':<20} {'Date Updated':<15} {'Title'}")
    print("-" * 120)
    
    for i, product in enumerate(products):
        if limit and i >= limit:
            print(f"\n... and {len(products) - limit} more products")
            break
            
        print(f"{product['id']:<8} "
              f"{(product['sku'] or 'N/A'):<20} "
              f"{(product['original_sku'] or 'N/A'):<20} "
              f"{(product['date_updated'] or 'EMPTY'):<15} "
              f"{product['title'][:50]}")

def main():
    print("=" * 120)
    print("Date Updated Status Check")
    print("=" * 120)
    
    if len(sys.argv) > 1:
        status = sys.argv[1]
    else:
        print("\nAvailable status filters:")
        print("  empty   - Products with no date_updated meta field")
        print("  invalid - Products with invalid date format")
        print("  stale   - Products with dates older than 7 days")
        print("  all     - All products with any issue (default)")
        print()
        status = input("Enter status filter (or press Enter for 'all'): ").strip() or 'all'
    
    if status not in ['empty', 'invalid', 'stale', 'all']:
        print(f"Invalid status: {status}")
        return
    
    days = 7
    if len(sys.argv) > 2:
        try:
            days = int(sys.argv[2])
        except ValueError:
            print(f"Invalid days value: {sys.argv[2]}, using default 7")
    
    show_all = '--all' in sys.argv
    
    print(f"\nChecking products with status='{status}', days={days}...")
    print()
    
    products = check_date_updated(status=status, days=days, show_all=show_all)
    
    if products is not None:
        if show_all:
            display_products(products, limit=None)
            print(f"\nTotal products found: {len(products)}")
        else:
            display_products(products, limit=50)
            if len(products) > 50:
                print(f"\nShowing first 50 of {len(products)} products on page 1")
                print("Use --all flag to fetch all pages")
        
        # Export option
        if products and len(products) > 0:
            export = input("\nExport to CSV? (y/n): ").strip().lower()
            if export == 'y':
                import csv
                filename = f"date_updated_{status}_{days}days.csv"
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['id', 'title', 'sku', 'original_sku', 'date_updated', 'edit_link'])
                    writer.writeheader()
                    writer.writerows(products)
                print(f"Exported {len(products)} products to {filename}")

if __name__ == "__main__":
    main()
