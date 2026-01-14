"""
Test runner to exercise error logging by attempting to create a product
that should conflict (existing SKU). This will trigger `log_error` and
write the full product payload to the log file for inspection.
"""
from pathlib import Path
import sys
base_dir = Path(__file__).parent.parent
sys.path.insert(0, str(base_dir))

from scripts.import_to_woocommerce import WooCommerceImporter
from config import WORDPRESS_URL

def load_keys(base_dir: Path):
    keys_file = base_dir / 'keys.txt'
    consumer_key = None
    consumer_secret = None
    with open(keys_file, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
        for i, line in enumerate(lines):
            if 'Consumer key' in line and i + 1 < len(lines):
                consumer_key = lines[i+1]
            elif 'Consumer secret' in line and i + 1 < len(lines):
                consumer_secret = lines[i+1]
    return consumer_key, consumer_secret


def main():
    consumer_key, consumer_secret = load_keys(base_dir)
    importer = WooCommerceImporter(WORDPRESS_URL, consumer_key, consumer_secret, base_dir / 'data' / 'checkpoints', base_dir / 'logs')

    # Minimal product that will conflict with existing SKU B00004839
    product = {
        'sku': 'B00004839',
        'name': 'TEST - BOLT',
        'type': 'simple',
        'diagram_code': 'TESTCODE',
        'callout': '7',
        'quantity': 1,
        'remark': 'test error logging',
        'categories': [],
        'diagram_file': ''
    }

    print('Attempting to create test product (expected to fail)')
    importer.create_simple_product(product)

if __name__ == '__main__':
    main()
