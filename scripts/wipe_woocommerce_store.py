"""
Safe wipe utility for WooCommerce store.

Usage:
  python wipe_woocommerce_store.py        # dry-run (no deletions)
  python wipe_woocommerce_store.py --apply  # actually delete products & categories

This script is conservative: it lists counts and planned deletions on dry-run
and only performs destructive actions when run with `--apply`.
"""
import sys
import time
from pathlib import Path
from woocommerce import API


def load_keys(base_dir: Path):
    keys_file = base_dir / 'keys.txt'
    consumer_key = None
    consumer_secret = None
    if keys_file.exists():
        with open(keys_file, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
            for i, line in enumerate(lines):
                if 'Consumer key' in line and i + 1 < len(lines):
                    consumer_key = lines[i+1]
                elif 'Consumer secret' in line and i + 1 < len(lines):
                    consumer_secret = lines[i+1]
    return consumer_key, consumer_secret


def main():
    base_dir = Path(__file__).parent.parent
    consumer_key, consumer_secret = load_keys(base_dir)
    if not consumer_key or not consumer_secret:
        print('Missing consumer key/secret in keys.txt')
        return

    sys.path.insert(0, str(base_dir))
    from config import WORDPRESS_URL

    wcapi = API(url=WORDPRESS_URL, consumer_key=consumer_key, consumer_secret=consumer_secret, version='wc/v3', timeout=30)

    apply_changes = '--apply' in sys.argv

    print(f"Connecting to {WORDPRESS_URL} (apply={apply_changes})")

    # Gather all products
    products = []
    page = 1
    while True:
        resp = wcapi.get('products', params={'per_page': 100, 'page': page})
        if resp.status_code != 200:
            print(f"Failed to fetch products: {resp.status_code}")
            return
        data = resp.json()
        if not data:
            break
        products.extend(data)
        page += 1

    print(f"Found {len(products)} products")

    # Gather all product categories
    categories = []
    page = 1
    while True:
        resp = wcapi.get('products/categories', params={'per_page': 100, 'page': page})
        if resp.status_code != 200:
            print(f"Failed to fetch categories: {resp.status_code}")
            return
        data = resp.json()
        if not data:
            break
        categories.extend(data)
        page += 1

    print(f"Found {len(categories)} product categories")

    # Show sample of what would be deleted
    if products:
        print('\nSample product IDs to delete:')
        print(', '.join(str(p['id']) for p in products[:20]))

    if categories:
        print('\nSample category IDs to delete:')
        print(', '.join(str(c['id']) for c in categories[:20]))

    if not apply_changes:
        print('\nDry-run complete. To delete these items run with --apply')
        return

    # Apply deletions: products first
    for p in products:
        pid = p['id']
        resp = wcapi.delete(f'products/{pid}', params={'force': True})
        if resp.status_code in (200, 201):
            print(f"Deleted product {pid}")
        else:
            print(f"Failed to delete product {pid}: {resp.status_code}")
        time.sleep(0.1)

    # Then delete categories
    for c in categories:
        cid = c['id']
        # Skip WooCommerce default category if any edge case; delete all present
        resp = wcapi.delete(f'products/categories/{cid}', params={'force': True})
        if resp.status_code in (200, 201):
            print(f"Deleted category {cid}")
        else:
            print(f"Failed to delete category {cid}: {resp.status_code}")
        time.sleep(0.1)

    print('\nWipe complete.')


if __name__ == '__main__':
    main()
