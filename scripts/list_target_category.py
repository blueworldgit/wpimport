"""
List categories matching a target name/slug (dry-run).

Usage:
  python scripts/list_target_category.py

This will print category id, name, slug, parent and count for matches.
"""
import sys
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


def normalize(s):
    return (s or '').strip().lower()


def main():
    base_dir = Path(__file__).parent.parent
    consumer_key, consumer_secret = load_keys(base_dir)
    if not consumer_key or not consumer_secret:
        print('Missing consumer key/secret in keys.txt')
        return

    sys.path.insert(0, str(base_dir))
    from config import WORDPRESS_URL

    wcapi = API(url=WORDPRESS_URL, consumer_key=consumer_key, consumer_secret=consumer_secret, version='wc/v3')

    target = 'LSFAL11A4PA157987'
    norm_target = normalize(target)

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
            if normalize(c.get('name')) == norm_target or normalize(c.get('slug')) == norm_target:
                matches.append(c)
        page += 1

    if not matches:
        print(f'No categories found matching "{target}"')
        return

    print(f'Found {len(matches)} matching categories:')
    for c in matches:
        print(f"- id={c['id']} name='{c.get('name')}' slug='{c.get('slug')}' parent={c.get('parent')} count={c.get('count')}")


if __name__ == '__main__':
    main()
