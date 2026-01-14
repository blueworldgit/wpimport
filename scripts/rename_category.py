"""
Rename a WooCommerce product category by ID.

Usage:
  python scripts/rename_category.py --id 517 --name "MAXUS DELIVER 9 RWD LUX" --slug maxus-deliver-9-rwd-lux --apply

Without `--apply` the script will perform a dry-run and show the planned payload.
"""
import sys
import argparse
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', type=int, required=True, help='Category ID to rename')
    parser.add_argument('--name', required=True, help='New category name')
    parser.add_argument('--slug', required=True, help='New category slug')
    parser.add_argument('--apply', action='store_true', help='Actually apply the change')
    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent
    consumer_key, consumer_secret = load_keys(base_dir)
    if not consumer_key or not consumer_secret:
        print('Missing consumer key/secret in keys.txt')
        return

    sys.path.insert(0, str(base_dir))
    from config import WORDPRESS_URL

    wcapi = API(url=WORDPRESS_URL, consumer_key=consumer_key, consumer_secret=consumer_secret, version='wc/v3')

    cat_id = args.id
    payload = {'name': args.name, 'slug': args.slug}

    print(f"Category ID: {cat_id}")
    print(f"Planned payload: {payload}")

    if not args.apply:
        print('Dry-run only. Add --apply to perform the update.')
        return

    resp = wcapi.put(f'products/categories/{cat_id}', payload)
    if resp.status_code in (200, 201):
        print('Rename successful:')
        print(resp.json())
    else:
        print(f'Failed to rename category: {resp.status_code} - {resp.text}')


if __name__ == '__main__':
    main()
