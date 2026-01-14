"""
Check presence of SKUs in WooCommerce and print product metadata.

Usage:
  python scripts/check_skus.py B00004839 B00004085
  or: python scripts/check_skus.py --file path/to/failed.txt

Reads API keys from `keys.txt` and `config.WORDPRESS_URL`.
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


def read_failed_file(path: Path):
    skus = []
    if not path.exists():
        return skus
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # try to extract SKU token (first token or bracketed)
            # failed.txt has lines like: 'Failed to create product B00004839: ...'
            parts = line.split()
            for p in parts:
                if p.isalnum() and len(p) >= 4:
                    skus.append(p.strip(':,'))
                    break
    return list(dict.fromkeys(skus))


def main():
    base_dir = Path(__file__).parent.parent
    consumer_key, consumer_secret = load_keys(base_dir)
    if not consumer_key or not consumer_secret:
        print('Missing consumer key/secret in keys.txt')
        return

    sys.path.insert(0, str(base_dir))
    from config import WORDPRESS_URL

    wcapi = API(url=WORDPRESS_URL, consumer_key=consumer_key, consumer_secret=consumer_secret, version='wc/v3')

    args = sys.argv[1:]
    skus = []
    if not args:
        print('Provide SKUs or --file path/to/failed.txt')
        return
    if args[0] == '--file' and len(args) > 1:
        skus = read_failed_file(Path(args[1]))
    else:
        skus = args

    for sku in skus:
        resp = wcapi.get('products', params={'sku': sku})
        if resp.status_code != 200:
            print(f'{sku}: API error {resp.status_code}')
            continue
        data = resp.json()
        if not data:
            print(f'{sku}: NOT FOUND')
            continue
        # may return multiple results — print summary
        for p in data:
            print(f"{sku}: id={p.get('id')} status={p.get('status')} sku={p.get('sku')} name={p.get('name')} slug={p.get('slug')} date_created={p.get('date_created')}")


if __name__ == '__main__':
    main()
