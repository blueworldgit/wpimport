#!/usr/bin/env python3
"""
Oscar <-> WordPress Category Sync Checker
Compares the full category hierarchy for a serial in Oscar DB vs WooCommerce.
Reports missing, extra, and mismatched categories.
"""
import sys
import argparse
import re
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

base_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(base_dir))
from config import WORDPRESS_URL

DB_CONFIG = {
    'dbname': 'parts_store',
    'user': 'postgres',
    'password': 'N0rwich!',
    'host': '80.95.207.42',
    'port': '5432'
}

def load_credentials():
    keys_file = base_dir / 'keys.txt'
    ck = cs = None
    with open(keys_file, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f if l.strip()]
    for i, line in enumerate(lines):
        if 'Consumer key' in line and i + 1 < len(lines):
            ck = lines[i + 1]
        if 'Consumer secret' in line and i + 1 < len(lines):
            cs = lines[i + 1]
    if not ck or not cs:
        raise RuntimeError("Could not load WooCommerce credentials from keys.txt")
    return ck, cs

def sanitize(name):
    """Mirror the sanitize_category_name() logic in fast_create_categories.py exactly."""
    if not name:
        return ""
    # Strip diagram codes e.g. 'FE471A001 - AirBag' -> 'AirBag'
    name = re.sub(r'^[A-Z]{2}\d+[A-Z]?\d+\s*-\s*', '', name)
    s = name.replace('&', 'and').replace('/', '-').replace('\\', '-')
    s = s.replace('(', '').replace(')', '').replace(',', ' ')
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'-+', '-', s)
    return s.strip(' -')

# ── Oscar ──────────────────────────────────────────────────────────────────────

def get_oscar_categories(serial):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT id, serial, vehicle_brand FROM motorpartsdata_serialnumber WHERE serial = %s", (serial,))
    sn = cur.fetchone()
    if not sn:
        print(f"ERROR: Serial '{serial}' not found in Oscar DB")
        sys.exit(1)

    cur.execute("""
        SELECT id, title FROM motorpartsdata_parenttitle
        WHERE serial_number_id = %s ORDER BY title
    """, (sn['id'],))
    parents = cur.fetchall()

    parent_ids = [p['id'] for p in parents]
    children = []
    if parent_ids:
        placeholders = ','.join(['%s'] * len(parent_ids))
        cur.execute(f"""
            SELECT id, title, parent_id FROM motorpartsdata_childtitle
            WHERE parent_id IN ({placeholders}) ORDER BY title
        """, parent_ids)
        children = cur.fetchall()

    cur.close()
    conn.close()

    # Build structured hierarchy: { sanitized_parent: set(sanitized_children) }
    parent_map = {p['id']: sanitize(p['title']) for p in parents}
    hierarchy = {name: set() for name in parent_map.values()}
    for child in children:
        parent_name = parent_map[child['parent_id']]
        hierarchy[parent_name].add(sanitize(child['title']))

    return sn['vehicle_brand'], hierarchy

# ── WordPress ──────────────────────────────────────────────────────────────────

def get_wp_categories(serial, ck, cs):
    auth = (ck, cs)
    base = f"{WORDPRESS_URL}/wp-json/wc/v3/products/categories"
    all_cats = []
    page = 1
    while True:
        r = requests.get(base, params={'per_page': 100, 'page': page}, auth=auth, timeout=30)
        if r.status_code != 200:
            print(f"ERROR: WP categories fetch failed ({r.status_code})")
            sys.exit(1)
        batch = r.json()
        if not batch:
            break
        all_cats.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    # Find VIN category
    vin_cat = next((c for c in all_cats if c['name'] == serial), None)
    if not vin_cat:
        print(f"ERROR: VIN category '{serial}' not found in WordPress")
        sys.exit(1)

    vin_id = vin_cat['id']
    wp_parents = [c for c in all_cats if c['parent'] == vin_id]
    wp_parent_ids = {c['id']: sanitize(c['name']) for c in wp_parents}
    wp_children = [c for c in all_cats if c['parent'] in wp_parent_ids]

    # Build same structure: { sanitized_parent: set(sanitized_children) }
    hierarchy = {name: set() for name in wp_parent_ids.values()}
    for child in wp_children:
        parent_name = wp_parent_ids[child['parent']]
        hierarchy[parent_name].add(sanitize(child['name']))

    return vin_id, hierarchy

# ── Compare ────────────────────────────────────────────────────────────────────

def compare(oscar_h, wp_h):
    oscar_parents = set(oscar_h.keys())
    wp_parents    = set(wp_h.keys())

    missing_parents = oscar_parents - wp_parents
    extra_parents   = wp_parents - oscar_parents
    common_parents  = oscar_parents & wp_parents

    parent_ok    = 0
    child_issues = []

    for parent in sorted(common_parents):
        oscar_kids = oscar_h[parent]
        wp_kids    = wp_h[parent]
        missing_kids = oscar_kids - wp_kids
        extra_kids   = wp_kids - oscar_kids
        if not missing_kids and not extra_kids:
            parent_ok += 1
        else:
            child_issues.append((parent, missing_kids, extra_kids))

    return missing_parents, extra_parents, parent_ok, child_issues

def main():
    parser = argparse.ArgumentParser(description='Compare Oscar vs WP categories for a serial')
    parser.add_argument('--serial', required=True, help='Serial/VIN number')
    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"Oscar <-> WordPress Category Sync Check: {args.serial}")
    print(f"{'='*70}\n")

    ck, cs = load_credentials()

    print("Fetching Oscar categories...")
    brand, oscar_h = get_oscar_categories(args.serial)
    oscar_total_parents  = len(oscar_h)
    oscar_total_children = sum(len(v) for v in oscar_h.values())
    print(f"  Oscar: {oscar_total_parents} parent categories, {oscar_total_children} child categories\n")

    print("Fetching WordPress categories...")
    vin_id, wp_h = get_wp_categories(args.serial, ck, cs)
    wp_total_parents  = len(wp_h)
    wp_total_children = sum(len(v) for v in wp_h.values())
    print(f"  WP:    {wp_total_parents} parent categories, {wp_total_children} child categories  (VIN ID={vin_id})\n")

    missing_parents, extra_parents, parent_ok, child_issues = compare(oscar_h, wp_h)

    # ── Report ────────────────────────────────────────────────────────────────
    all_ok = not missing_parents and not extra_parents and not child_issues

    print(f"{'='*70}")
    print(f"RESULTS")
    print(f"{'='*70}")
    print(f"  Parent categories matched OK : {parent_ok}")
    print(f"  Parent categories missing WP : {len(missing_parents)}")
    print(f"  Parent categories extra in WP: {len(extra_parents)}")
    print(f"  Parent categories with child issues: {len(child_issues)}")
    print()

    if missing_parents:
        print(f"MISSING PARENTS (in Oscar, not in WP) [{len(missing_parents)}]:")
        for p in sorted(missing_parents):
            print(f"  - {p}  ({len(oscar_h[p])} children in Oscar)")
        print()

    if extra_parents:
        print(f"EXTRA PARENTS (in WP, not in Oscar) [{len(extra_parents)}]:")
        for p in sorted(extra_parents):
            print(f"  + {p}  ({len(wp_h[p])} children in WP)")
        print()

    if child_issues:
        print(f"CHILD CATEGORY ISSUES [{len(child_issues)} parent(s) affected]:")
        for parent, missing_kids, extra_kids in sorted(child_issues):
            print(f"  [{parent}]")
            for k in sorted(missing_kids):
                print(f"    MISSING: {k}")
            for k in sorted(extra_kids):
                print(f"    EXTRA:   {k}")
        print()

    if all_ok:
        total = 1 + oscar_total_parents + oscar_total_children
        print(f"PERFECT MATCH - all {oscar_total_parents} parents and {oscar_total_children} children are present in WP")
        print(f"Full hierarchy: 1 VIN + {oscar_total_parents} parents + {oscar_total_children} children = {total} categories")
    else:
        print(f"SYNC INCOMPLETE - issues found above need resolving")

    print(f"{'='*70}\n")
    return 0 if all_ok else 1

if __name__ == '__main__':
    sys.exit(main())
