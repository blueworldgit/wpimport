#!/usr/bin/env python3
"""
Complete Serial Cleanup - Ultra-Fast Async Edition
Deletes all products and categories for a specific serial from WordPress
Uses fully async fetching + WooCommerce batch API for maximum speed

AGGRESSIVE MODE (Default):
  - 20 concurrent batch deletions
  - 100 TCP connections
  - 15-20x concurrent page fetching

TYPICAL SPEEDS (on fast servers):
  ~1000-2000 products/second
"""
import asyncio
import aiohttp
import time
from pathlib import Path
import sys
import argparse
from tqdm import tqdm

sys.stdout.reconfigure(encoding='utf-8')

# aiohttp on Windows requires SelectorEventLoop (ProactorEventLoop causes CancelledError)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

base_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(base_dir))
from config import WORDPRESS_URL

WC_BATCH_SIZE = 100  # WooCommerce batch API limit

def load_credentials():
    keys_file = base_dir / 'keys.txt'
    with open(keys_file, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    ck = cs = None
    for i, line in enumerate(lines):
        if 'Consumer key' in line and i + 1 < len(lines):
            ck = lines[i + 1]
        if 'Consumer secret' in line and i + 1 < len(lines):
            cs = lines[i + 1]
    if not ck or not cs:
        raise RuntimeError("Could not load WooCommerce credentials from keys.txt")
    return ck, cs

async def fetch_page(session, url, params, auth):
    try:
        async with session.get(url, params=params, auth=auth) as r:
            if r.status == 200:
                data = await r.json()
                return data if isinstance(data, list) else []
    except Exception:
        pass
    return []

async def fetch_all_pages_async(session, url, extra_params, auth, concurrency=15):
    params1 = {'per_page': WC_BATCH_SIZE, 'page': 1, **extra_params}
    first = await fetch_page(session, url, params1, auth)
    if not first:
        return []
    if len(first) < WC_BATCH_SIZE:
        return first
    all_items = list(first)
    page = 2
    sem = asyncio.Semaphore(concurrency)

    async def bounded_fetch(p):
        async with sem:
            return await fetch_page(session, url, {'per_page': WC_BATCH_SIZE, 'page': p, **extra_params}, auth)

    while True:
        pages_to_fetch = list(range(page, page + concurrency))
        results = await asyncio.gather(*[bounded_fetch(p) for p in pages_to_fetch])
        got_any = False
        for items in results:
            if items:
                all_items.extend(items)
                got_any = True
        if not got_any:
            break
        if any(len(r) < WC_BATCH_SIZE for r in results if r):
            break
        page += concurrency
    return all_items

async def get_category_tree(session, auth, serial_number, override_cat_id=None):
    print(f"Fetching all categories...")
    url = f"{WORDPRESS_URL}/wp-json/wc/v3/products/categories"
    all_cats = await fetch_all_pages_async(session, url, {}, auth, concurrency=20)
    print(f"   Fetched {len(all_cats)} total categories")

    serial_cat_id = override_cat_id
    if not serial_cat_id:
        for cat in all_cats:
            if cat['name'] == serial_number:
                serial_cat_id = cat['id']
                break

    if not serial_cat_id:
        print(f"   Serial category '{serial_number}' not found in WordPress")
        return None, []

    print(f"   Serial category ID: {serial_cat_id}")
    parent_cats = [c for c in all_cats if c.get('parent') == serial_cat_id]
    parent_ids  = {c['id'] for c in parent_cats}
    child_cats  = [c for c in all_cats if c.get('parent') in parent_ids]
    to_delete = child_cats + parent_cats + [{'id': serial_cat_id, 'name': serial_number}]
    print(f"   {len(parent_cats)} parent categories, {len(child_cats)} child categories")
    return serial_cat_id, to_delete

async def get_products_for_category(session, auth, category_id):
    print(f"Fetching products for category {category_id}...")
    url = f"{WORDPRESS_URL}/wp-json/wc/v3/products"
    items = await fetch_all_pages_async(session, url,
        {'category': category_id, 'status': 'any', '_fields': 'id'}, auth, concurrency=15)
    ids = [p['id'] for p in items]
    print(f"   Found {len(ids)} products")
    return ids

async def batch_delete_products(session, auth, product_ids, concurrent_batches=20):
    if not product_ids:
        return 0, 0
    batches = [product_ids[i:i+WC_BATCH_SIZE] for i in range(0, len(product_ids), WC_BATCH_SIZE)]
    url = f"{WORDPRESS_URL}/wp-json/wc/v3/products/batch"
    sem = asyncio.Semaphore(concurrent_batches)
    deleted = failed = 0

    async def do_batch(batch):
        async with sem:
            try:
                async with session.post(url, json={'delete': batch}, auth=auth) as r:
                    if r.status == 200:
                        data = await r.json()
                        return len(data.get('delete', [])), 0
                    return 0, len(batch)
            except Exception:
                return 0, len(batch)

    print(f"\nDeleting {len(product_ids)} products in {len(batches)} batches...")
    with tqdm(total=len(product_ids), desc="Products", unit=" items") as pbar:
        for i in range(0, len(batches), concurrent_batches):
            chunk = batches[i:i + concurrent_batches]
            results = await asyncio.gather(*[do_batch(b) for b in chunk])
            for d, f in results:
                deleted += d
                failed += f
                pbar.update(d + f)
    return deleted, failed

async def batch_delete_categories(session, auth, categories, concurrent_batches=20):
    if not categories:
        return 0, 0
    cat_ids = [c['id'] for c in categories]
    batches = [cat_ids[i:i+WC_BATCH_SIZE] for i in range(0, len(cat_ids), WC_BATCH_SIZE)]
    url = f"{WORDPRESS_URL}/wp-json/wc/v3/products/categories/batch"
    sem = asyncio.Semaphore(concurrent_batches)
    deleted = failed = 0

    async def do_batch(batch):
        async with sem:
            try:
                async with session.post(url, json={'delete': batch}, auth=auth) as r:
                    if r.status == 200:
                        data = await r.json()
                        return len(data.get('delete', [])), 0
                    return 0, len(batch)
            except Exception:
                return 0, len(batch)

    print(f"\nDeleting {len(cat_ids)} categories in {len(batches)} batches...")
    with tqdm(total=len(cat_ids), desc="Categories", unit=" items") as pbar:
        for i in range(0, len(batches), concurrent_batches):
            chunk = batches[i:i + concurrent_batches]
            results = await asyncio.gather(*[do_batch(b) for b in chunk])
            for d, f in results:
                deleted += d
                failed += f
                pbar.update(d + f)
    return deleted, failed

async def empty_trash(session, auth, concurrent_batches=20):
    print(f"\nScanning trash...")
    url = f"{WORDPRESS_URL}/wp-json/wc/v3/products"
    trashed = await fetch_all_pages_async(session, url,
        {'status': 'trash', '_fields': 'id'}, auth, concurrency=15)
    if not trashed:
        print("   Trash is empty")
        return 0
    ids = [p['id'] for p in trashed]
    print(f"   Found {len(ids)} trashed items")
    deleted, _ = await batch_delete_products(session, auth, ids, concurrent_batches=concurrent_batches)
    print(f"   Emptied {deleted} items from trash")
    return deleted

async def run(args, ck, cs):
    # Aggressive settings are now default
    concurrent_batches = 20
    max_connections = 100
    
    auth = aiohttp.BasicAuth(ck, cs)
    connector = aiohttp.TCPConnector(limit=max_connections, force_close=False, enable_cleanup_closed=True)
    timeout = aiohttp.ClientTimeout(total=600, connect=30, sock_read=120)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        serial_cat_id, categories = await get_category_tree(
            session, auth, args.serial, override_cat_id=args.category_id)

        if not serial_cat_id:
            print(f"\nCannot find serial category. Use --category-id to specify it directly.")
            return 1

        product_ids = await get_products_for_category(session, auth, serial_cat_id)

        print(f"\n{'='*70}")
        print(f"DELETION PLAN for {args.serial}")
        print(f"{'='*70}")
        print(f"  Products:   {len(product_ids)}")
        print(f"  Categories: {len(categories)}")
        print(f"{'='*70}\n")

        if args.dry_run:
            print("DRY RUN - nothing deleted")
            return 0

        if not args.yes:
            confirm = input("Type 'DELETE' to confirm: ")
            if confirm.strip() != 'DELETE':
                print("Cancelled")
                return 1

        start = time.time()

        if not args.categories_only:
            pd, pf = await batch_delete_products(session, auth, product_ids, concurrent_batches=concurrent_batches)
            print(f"   Products deleted: {pd}  failed: {pf}")

        if not args.products_only:
            cd, cf = await batch_delete_categories(session, auth, categories, concurrent_batches=concurrent_batches)
            print(f"   Categories deleted: {cd}  failed: {cf}")

        await empty_trash(session, auth, concurrent_batches=concurrent_batches)

        elapsed = time.time() - start
        total_items = len(product_ids) + len(categories)
        items_per_sec = total_items / elapsed if elapsed > 0 else 0
        
        print(f"\n{'='*70}")
        print(f"Cleanup complete for {args.serial}  ({elapsed:.1f}s)")
        print(f"Performance: {items_per_sec:.0f} items/second")
        print(f"{'='*70}\n")

    return 0

def main():
    parser = argparse.ArgumentParser(description='Delete all products & categories for a serial (AGGRESSIVE mode by default)')
    parser.add_argument('--serial', required=True, help='Serial number')
    parser.add_argument('--category-id', type=int, default=None,
                        help='Use this WP category ID directly (bypass name lookup)')
    parser.add_argument('--products-only', action='store_true', help='Delete products only, keep categories')
    parser.add_argument('--categories-only', action='store_true', help='Delete categories only')
    parser.add_argument('--dry-run', action='store_true', help='Show plan without deleting')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"Serial Cleanup: {args.serial}")
    print(f"Mode: AGGRESSIVE (20 concurrent batches, 100 connections)")
    print(f"{'='*70}\n")

    ck, cs = load_credentials()
    print(f"Credentials loaded  (key: {ck[:12]}...)")

    exit(asyncio.run(run(args, ck, cs)))

if __name__ == '__main__':
    main()
