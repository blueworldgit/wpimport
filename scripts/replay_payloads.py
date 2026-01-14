#!/usr/bin/env python3
from pathlib import Path
import sys, json
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))
from config import WORDPRESS_URL
from scripts.import_to_woocommerce import WooCommerceImporter

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

log_dir = base_dir / 'logs'
checkpoint_dir = base_dir / 'data' / 'checkpoints_debug_replay'
checkpoint_dir.mkdir(parents=True, exist_ok=True)

importer = WooCommerceImporter(WORDPRESS_URL, consumer_key, consumer_secret, checkpoint_dir, log_dir)
# Make network calls fail faster during debugging if the API is slow
try:
    importer.wcapi.timeout = 5
except Exception:
    pass

# Prepopulate category cache to avoid extra GET calls during replay
try:
    spid = getattr(importer, 'shared_parent_id', 0) or 0
    # map our example category names to known IDs used earlier
    importer.category_cache[f"LSFAL11A4PA157987_{spid}"] = 517
    importer.category_cache[f"SomeParent_517"] = 720
    importer.category_cache[f"JE471A001_720"] = 721
except Exception:
    pass

# Avoid attempting to PATCH/repair existing products during replay (prevents long network hangs)
try:
    importer._repair_existing_product = lambda *a, **k: False
except Exception:
    pass

# Define payloads copied from error logs
payloads = [
    {
        "name": "JE471A001 - BOLT/SCREW-FRONT PASSENGER AIRBAG ASSEMBLY",
        "type": "simple",
        "sku": "B00004839",
        "regular_price": "0.00",
        "description": "",
        "short_description": "",
        "categories": ["LSFAL11A4PA157987","SomeParent","JE471A001"],
        "images": [{"id": 11848}],
        "manage_stock": True,
        "stock_quantity": 50,
        "stock_status": "instock",
        "meta_data": [
            {"key": "diagram_code", "value": "JE471A001"},
            {"key": "callout_number", "value": "7"},
            {"key": "diagram_file", "value": "airbag\\Steering Wheel and AirBag.html"},
            {"key": "orientation", "value": None},
            {"key": "quantity_per_vehicle", "value": "2.0"},
            {"key": "remark", "value": ""}
        ],
        # Fields expected by create_simple_product
        "diagram_code": "JE471A001",
        "callout": "7",
        "quantity": "2.0",
        "diagram_file": "airbag\\Steering Wheel and AirBag.html",
        "orientation": None,
        "remark": ""
    },
    {
        "name": "JE471A001 - BOLT-CURTAIN AIRBAG",
        "type": "simple",
        "sku": "B00004085",
        "regular_price": "0.00",
        "description": "",
        "short_description": "",
        "categories": ["LSFAL11A4PA157987","SomeParent","JE471A001"],
        "images": [{"id": 11848}],
        "manage_stock": True,
        "stock_quantity": 50,
        "stock_status": "instock",
        "meta_data": [
            {"key": "diagram_code", "value": "JE471A001"},
            {"key": "callout_number", "value": "8"},
            {"key": "diagram_file", "value": "airbag\\Steering Wheel and AirBag.html"},
            {"key": "orientation", "value": None},
            {"key": "quantity_per_vehicle", "value": "10.0"},
            {"key": "remark", "value": ""}
        ],
        "diagram_code": "JE471A001",
        "callout": "8",
        "quantity": "10.0",
        "diagram_file": "airbag\\Steering Wheel and AirBag.html",
        "orientation": None,
        "remark": ""
    }
]

print('Replaying payloads...')
for p in payloads:
    try:
        print(f"Creating SKU {p['sku']}")
        # Force the importer to behave as if SKU lookup returned nothing (to exercise POST path)
        original_find = importer._find_product_by_sku
        try:
            importer._find_product_by_sku = lambda sku, retries=3, per_page=100, backoff=0.5: []
            importer.create_simple_product(p)
        finally:
            importer._find_product_by_sku = original_find
    except Exception as e:
        print('Error replaying payload:', e)

print('Done. Check logs/prepost_debug.log and logs/import_errors_*.log')
