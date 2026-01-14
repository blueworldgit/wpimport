"""
Extract from a serial folder and run a quick import test (first N products).

Usage:
  python scripts/extract_and_import_test.py --source LSH14J7C7MA114771 --limit 20
"""
import sys
from pathlib import Path

base_dir = Path(__file__).parent.parent
sys.path.insert(0, str(base_dir))

from scripts.extract_data import EPCDataExtractor
from scripts.import_to_woocommerce import WooCommerceImporter
from config import WORDPRESS_URL


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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', '-s', required=True, help='Serial folder to extract')
    parser.add_argument('--limit', '-l', type=int, default=20, help='Number of products to extract for testing')
    args = parser.parse_args()

    serial_dir = base_dir / args.source
    if not serial_dir.exists():
        print(f"Source folder not found: {serial_dir}")
        return

    output_dir = serial_dir  # write extracted_data_full.json into the serial folder
    log_dir = base_dir / 'logs'

    extractor = EPCDataExtractor(serial_dir, output_dir, log_dir)
    data = extractor.extract_category_data(serial_dir, test_limit=args.limit)
    extractor.save_extracted_data(data, filename='extracted_data_full.json')
    extractor.print_summary()

    # Now run importer on this small set
    consumer_key, consumer_secret = load_keys(base_dir)
    checkpoint_dir = base_dir / 'data' / 'checkpoints'
    importer = WooCommerceImporter(WORDPRESS_URL, consumer_key, consumer_secret, checkpoint_dir, log_dir)

    products = data.get('products', [])
    if not products:
        print('No products extracted; aborting import test')
        return

    print(f"\nRunning import test for {len(products)} products (limit used: {args.limit})")
    importer.import_products(products)
    importer.save_checkpoint()
    importer.print_summary()


if __name__ == '__main__':
    main()
