"""
Check products with missing, invalid, or stale date_updated values.
Uses the custom REST endpoint: /wp-json/custom/v1/products-by-date-updated
"""

import requests
import sys
from pathlib import Path

# Load site URL and credentials from config.py / keys.txt
_base_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_base_dir))
from config import WORDPRESS_URL

_keys_file = _base_dir / 'keys.txt'
WP_CONSUMER_KEY = WP_CONSUMER_SECRET = None
with open(_keys_file, 'r', encoding='utf-8') as _f:
    _lines = [l.strip() for l in _f if l.strip()]
for _i, _line in enumerate(_lines):
    if 'Consumer key' in _line and _i + 1 < len(_lines):
        WP_CONSUMER_KEY = _lines[_i + 1]
    if 'Consumer secret' in _line and _i + 1 < len(_lines):
        WP_CONSUMER_SECRET = _lines[_i + 1]
if not WP_CONSUMER_KEY or not WP_CONSUMER_SECRET:
    raise RuntimeError("Could not load WooCommerce credentials from keys.txt")

WP_URL = WORDPRESS_URL

def check_date_updated(status='all', days=7, show_all=False, unique_original_sku=False):
    """
    Check products by date_updated status.

    Args:
        status: 'empty', 'invalid', 'stale', or 'all'
        days: Number of days threshold for stale check
        show_all: If True, fetch all pages; if False, show only first page
        unique_original_sku: If True, endpoint returns only one product per unique original_sku
    """
    endpoint = f"{WP_URL}/wp-json/custom/v1/products-by-date-updated"

    page = 1
    all_products = []

    while True:
        params = {
            'status': status,
            'days': days,
            'page': page,
            'per_page': 100,
            'unique_original_sku': 1 if unique_original_sku else 0
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
                print(f"  Unique original_sku: {data.get('unique_original_sku', False)}")
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
    unique_original_sku = '--unique' in sys.argv

    print(f"\nChecking products with status='{status}', days={days}, "
          f"show_all={show_all}, unique_original_sku={unique_original_sku}...")
    print()

    products = check_date_updated(
        status=status,
        days=days,
        show_all=show_all,
        unique_original_sku=unique_original_sku
    )

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
                suffix = '_unique_sku' if unique_original_sku else ''
                filename = f"date_updated_{status}_{days}days{suffix}.csv"
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['id', 'title', 'sku', 'original_sku', 'date_updated', 'edit_link'])
                    writer.writeheader()
                    writer.writerows(products)
                print(f"Exported {len(products)} products to {filename}")

if __name__ == "__main__":
    main()