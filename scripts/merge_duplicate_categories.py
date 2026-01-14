"""
Merge duplicate WooCommerce product categories by normalized name and parent.

Usage:
  python merge_duplicate_categories.py [--apply]

By default the script performs a dry-run and prints planned actions. Use
`--apply` to actually reassign products and delete duplicate categories.
"""
import sys
import time
import json
from pathlib import Path
from woocommerce import API


def load_keys(base_dir):
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


def normalize_name(name):
    return (name or '').strip().lower()


def main():
    base_dir = Path(__file__).parent.parent
    consumer_key, consumer_secret = load_keys(base_dir)
    if not consumer_key or not consumer_secret:
        print("Missing consumer key/secret in keys.txt")
        return

    # Load WP URL from config
    sys.path.insert(0, str(base_dir))
    from config import WORDPRESS_URL

    wcapi = API(url=WORDPRESS_URL, consumer_key=consumer_key, consumer_secret=consumer_secret, version='wc/v3')

    apply_changes = '--apply' in sys.argv

    print(f"Connecting to: {WORDPRESS_URL} (dry-run={not apply_changes})")

    # Load all categories
    cats = []
    page = 1
    while True:
        resp = wcapi.get('products/categories', params={'per_page': 100, 'page': page})
        if resp.status_code != 200:
            print(f"Failed to fetch categories: {resp.status_code}")
            return
        data = resp.json()
        if not data:
            break
        cats.extend(data)
        page += 1

    # Group by normalized name + parent
    groups = {}
    for c in cats:
        key = f"{normalize_name(c.get('name'))}_{c.get('parent', 0) or 0}"
        groups.setdefault(key, []).append(c)

    duplicates = {k: v for k, v in groups.items() if len(v) > 1}

    if not duplicates:
        print("No duplicate categories detected.")
        return

    print(f"Found {len(duplicates)} duplicate category groups.")

    # Fetch all products once to speed reassignment
    products = []
    page = 1
    while True:
        resp = wcapi.get('products', params={'per_page': 100, 'page': page})
        if resp.status_code != 200:
            print(f"Failed to fetch products: {resp.status_code}")
            return
        data = resp.json()
        if not data:
            break
        products.extend(data)
        page += 1

    actions = []

    for key, group in duplicates.items():
        group_sorted = sorted(group, key=lambda x: x['id'])
        master = group_sorted[0]
        duplicates_ids = [g['id'] for g in group_sorted[1:]]
        print(f"Group: '{group_sorted[0]['name']}' parent={master.get('parent',0)} -> master={master['id']} duplicates={duplicates_ids}")

        # Find products that reference any duplicate ID
        affected = []
        for p in products:
            cat_ids = [c.get('id') for c in p.get('categories', [])]
            intersect = set(cat_ids) & set(duplicates_ids)
            if intersect:
                affected.append((p, cat_ids))

        print(f"  Affected products: {len(affected)}")

        for p, cat_ids in affected:
            new_cat_ids = []
            changed = False
            for cid in cat_ids:
                if cid in duplicates_ids:
                    if master['id'] not in new_cat_ids:
                        new_cat_ids.append(master['id'])
                    changed = True
                else:
                    if cid not in new_cat_ids:
                        new_cat_ids.append(cid)

            if changed:
                actions.append({'product_id': p['id'], 'old_categories': cat_ids, 'new_categories': new_cat_ids, 'master': master['id'], 'remove': duplicates_ids})

    if not actions:
        print("No product updates required.")
    else:
        print(f"Planned product updates: {len(actions)}")

    # Dry-run: print summary
    for act in actions[:20]:
        print(f"  Product {act['product_id']}: {act['old_categories']} -> {act['new_categories']}")

    if not apply_changes:
        print("\nDry-run complete. To apply changes run with --apply")
        return

    # Apply reassignment and delete duplicates
    for act in actions:
        pid = act['product_id']
        new_cats = [{'id': cid} for cid in act['new_categories']]
        resp = wcapi.put(f"products/{pid}", {'categories': new_cats})
        if resp.status_code in (200, 201):
            print(f"Updated product {pid}")
        else:
            print(f"Failed to update product {pid}: {resp.status_code}")
        time.sleep(0.2)

    # Delete duplicate categories
    for key, group in duplicates.items():
        group_sorted = sorted(group, key=lambda x: x['id'])
        duplicates_ids = [g['id'] for g in group_sorted[1:]]
        for cid in duplicates_ids:
            resp = wcapi.delete(f"products/categories/{cid}", params={'force': True})
            if resp.status_code in (200, 201):
                print(f"Deleted category {cid}")
            else:
                print(f"Failed to delete category {cid}: {resp.status_code}")
            time.sleep(0.2)

    print("Done applying changes.")


if __name__ == '__main__':
    main()
