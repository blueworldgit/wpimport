#!/usr/bin/env python3
"""
Delete Empty Categories
Removes all WordPress categories that have:
  - No child categories
  - No products attached

Uses async fetching for speed and WooCommerce batch API for deletion
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

async def get_all_categories(session, auth):
    print(f"Fetching all categories...")
    url = f"{WORDPRESS_URL}/wp-json/wc/v3/products/categories"
    all_cats = await fetch_all_pages_async(session, url, {}, auth, concurrency=20)
    print(f"   Fetched {len(all_cats)} total categories")
    return all_cats

async def get_product_count_for_category(session, auth, category_id):
    """Get count of products in a category (fast check using per_page=1)"""
    url = f"{WORDPRESS_URL}/wp-json/wc/v3/products"
    params = {'category': category_id, 'status': 'any', 'per_page': 1, 'page': 1, '_fields': 'id'}
    try:
        async with session.get(url, params=params, auth=auth) as r:
            if r.status == 200:
                data = await r.json()
                # Check X-WP-Total header for accurate count
                total_header = r.headers.get('X-WP-Total')
                if total_header:
                    return int(total_header)
                # Fallback to counting results
                return len(data) if isinstance(data, list) else 0
    except Exception:
        pass
    return 0

async def find_empty_categories(session, auth, categories, concurrency=20):
    """Find categories with no children and no products"""
    print(f"\nAnalyzing categories for emptiness...")
    
    # Build map of parent -> children
    category_children = {}
    for cat in categories:
        parent_id = cat.get('parent', 0)
        if parent_id not in category_children:
            category_children[parent_id] = []
        category_children[parent_id].append(cat['id'])
    
    # Filter out categories that have children
    categories_without_children = [
        cat for cat in categories 
        if cat['id'] not in category_children or len(category_children[cat['id']]) == 0
    ]
    
    print(f"   {len(categories_without_children)} categories have no children")
    print(f"   Checking product counts for these categories...")
    
    # Check product counts concurrently
    sem = asyncio.Semaphore(concurrency)
    
    async def check_category(cat):
        async with sem:
            count = await get_product_count_for_category(session, auth, cat['id'])
            return cat, count
    
    empty_categories = []
    with tqdm(total=len(categories_without_children), desc="Checking", unit=" cats") as pbar:
        tasks = [check_category(cat) for cat in categories_without_children]
        results = await asyncio.gather(*tasks)
        for cat, count in results:
            pbar.update(1)
            if count == 0:
                empty_categories.append(cat)
    
    return empty_categories

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

async def run(args, ck, cs):
    concurrent_batches = 20
    max_connections = 100
    
    auth = aiohttp.BasicAuth(ck, cs)
    connector = aiohttp.TCPConnector(limit=max_connections, force_close=False, enable_cleanup_closed=True)
    timeout = aiohttp.ClientTimeout(total=600, connect=30, sock_read=120)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # Fetch all categories
        all_categories = await get_all_categories(session, auth)
        
        if not all_categories:
            print("No categories found")
            return 0
        
        # Find empty categories
        empty_categories = await find_empty_categories(session, auth, all_categories, concurrency=20)
        
        print(f"\n{'='*70}")
        print(f"EMPTY CATEGORIES FOUND")
        print(f"{'='*70}")
        print(f"  Total categories:     {len(all_categories)}")
        print(f"  Empty categories:     {len(empty_categories)}")
        print(f"{'='*70}\n")
        
        if not empty_categories:
            print("No empty categories to delete")
            return 0
        
        # Show sample of categories to be deleted
        if args.verbose and empty_categories:
            print("Sample of empty categories to delete:")
            for cat in empty_categories[:10]:
                print(f"  - {cat['name']} (ID: {cat['id']})")
            if len(empty_categories) > 10:
                print(f"  ... and {len(empty_categories) - 10} more")
            print()
        
        if args.dry_run:
            print("DRY RUN - nothing deleted")
            return 0

        if not args.yes:
            confirm = input(f"Type 'DELETE' to confirm deletion of {len(empty_categories)} empty categories: ")
            if confirm.strip() != 'DELETE':
                print("Cancelled")
                return 1

        start = time.time()

        # Delete empty categories
        deleted, failed = await batch_delete_categories(session, auth, empty_categories, concurrent_batches=concurrent_batches)
        
        elapsed = time.time() - start
        items_per_sec = deleted / elapsed if elapsed > 0 else 0
        
        print(f"\n{'='*70}")
        print(f"Cleanup complete  ({elapsed:.1f}s)")
        print(f"  Deleted:  {deleted}")
        print(f"  Failed:   {failed}")
        print(f"  Speed:    {items_per_sec:.0f} items/second")
        print(f"{'='*70}\n")

    return 0

def main():
    parser = argparse.ArgumentParser(description='Delete all empty categories (no children, no products)')
    parser.add_argument('--dry-run', action='store_true', help='Show plan without deleting')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt')
    parser.add_argument('--verbose', action='store_true', help='Show detailed list of categories')
    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"Empty Category Cleanup")
    print(f"Mode: AGGRESSIVE (20 concurrent batches, 100 connections)")
    print(f"{'='*70}\n")

    ck, cs = load_credentials()
    print(f"Credentials loaded  (key: {ck[:12]}...)")

    exit(asyncio.run(run(args, ck, cs)))

if __name__ == '__main__':
    main()
