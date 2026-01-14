#!/usr/bin/env python3
from pathlib import Path
import sys
import json
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))
from config import WORDPRESS_URL
from scripts.import_to_woocommerce import WooCommerceImporter

if len(sys.argv) < 2:
    print('Usage: debug_import_run.py <serial_folder> [max_products]')
    sys.exit(2)

serial = Path(sys.argv[1])
max_products = None
if len(sys.argv) >= 3:
    try:
        max_products = int(sys.argv[2])
    except Exception:
        print('Invalid max_products value; must be an integer')
        sys.exit(2)
if not serial.exists():
    print('Serial folder not found:', serial); sys.exit(2)

data_file = serial / 'extracted_data_full.json'
if not data_file.exists():
    print('Data file not found:', data_file); sys.exit(2)

with open(data_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Optionally limit number of products processed for quick tests
products_list = data.get('products', [])
if max_products is not None:
    products_list = products_list[:max_products]

# Use a fresh checkpoint dir for this debug run
checkpoint_dir = base_dir / 'data' / 'checkpoints_debug'
checkpoint_dir.mkdir(parents=True, exist_ok=True)
log_dir = base_dir / 'logs'

# Load keys
keys_file = base_dir / 'keys.txt'
consumer_key = None
consumer_secret = None
if keys_file.exists():
    with open(keys_file, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
        for i,line in enumerate(lines):
            if 'Consumer key' in line and i+1 < len(lines): consumer_key = lines[i+1]
            if 'Consumer secret' in line and i+1 < len(lines): consumer_secret = lines[i+1]

importer = WooCommerceImporter(WORDPRESS_URL, consumer_key, consumer_secret, checkpoint_dir, log_dir)
print('\nRunning debug import (fresh checkpoint)')
importer.import_products(products_list)
importer.save_checkpoint()
importer.print_summary()
print('\nDebug run complete. See logs/sku_debug.log for SKU lookup traces.')
