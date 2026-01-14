"""
Find categories by slug or name.

Usage:
  python scripts/find_category_by_slug.py --slug maxus-deliver-9-rwd-lux
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
    parser.add_argument('--slug', help='Slug to search for')
    parser.add_argument('--name', help='Name to search for')
    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent
    consumer_key, consumer_secret = load_keys(base_dir)
    if not consumer_key or not consumer_secret:
        print('Missing consumer key/secret in keys.txt')
        return

    sys.path.insert(0, str(base_dir))
    from config import WORDPRESS_URL

    wcapi = API(url=WORDPRESS_URL, consumer_key=consumer_key, consumer_secret=consumer_secret, version='wc/v3')

    target_slug = args.slug
    target_name = args.name

    matches = []
    page = 1
    while True:
        resp = wcapi.get('products/categories', params={'per_page': 100, 'page': page})
        if resp.status_code != 200:
            print(f'Failed to fetch categories: {resp.status_code}')
            return
        data = resp.json()
        if not data:
            break
        for c in data:
            if target_slug and c.get('slug') == target_slug:
                matches.append(c)
            elif target_name and c.get('name') == target_name:
                matches.append(c)
        page += 1

    if not matches:
        print('No matches found')
        return

    for c in matches:
        print(f"id={c['id']} name='{c.get('name')}' slug='{c.get('slug')}' parent={c.get('parent')} count={c.get('count')}")


if __name__ == '__main__':
    main()
