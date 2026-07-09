#!/usr/bin/env python3
"""
Check part counts for a specific serial in both database and WordPress
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg2
from config import WORDPRESS_URL
from woocommerce import API

# Database connection parameters
DB_CONFIG = {
    'dbname': 'parts_store',
    'user': 'postgres',
    'password': 'N0rwich!',
    'host': '80.95.207.42',
    'port': '5432'
}

def load_credentials():
    """Load WooCommerce credentials from keys.txt"""
    base_dir = Path(__file__).resolve().parent.parent
    keys_file = base_dir / 'keys.txt'
    
    with open(keys_file, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    
    consumer_key = None
    consumer_secret = None
    
    for i, line in enumerate(lines):
        if 'Consumer key' in line and i+1 < len(lines):
            consumer_key = lines[i+1]
        if 'Consumer secret' in line and i+1 < len(lines):
            consumer_secret = lines[i+1]
    
    return consumer_key, consumer_secret

def check_database_count(serial):
    """Check how many unique parts exist in database for this serial"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Count unique part_ids
    cursor.execute('''
        SELECT COUNT(DISTINCT p.id) as unique_parts
        FROM motorpartsdata_part p
        JOIN motorpartsdata_childtitle ct ON p.child_title_id = ct.id
        JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id
        JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
        WHERE sn.serial = %s
    ''', (serial,))
    
    unique_parts = cursor.fetchone()[0]
    
    # Check if there are any duplicate part_ids in the query results
    cursor.execute('''
        SELECT p.id, COUNT(*) as count
        FROM motorpartsdata_part p
        JOIN motorpartsdata_childtitle ct ON p.child_title_id = ct.id
        JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id
        JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
        WHERE sn.serial = %s
        GROUP BY p.id
        HAVING COUNT(*) > 1
    ''', (serial,))
    
    duplicates = cursor.fetchall()
    
    conn.close()
    
    return unique_parts, duplicates

def check_wordpress_count(serial, consumer_key, consumer_secret):
    """Check how many products exist in WordPress for this serial"""
    wcapi = API(
        url=WORDPRESS_URL,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        version="wc/v3",
        timeout=30
    )
    
    # Get all products with this serial's meta_data
    page = 1
    all_products = []
    
    while True:
        response = wcapi.get("products", params={
            "per_page": 100,
            "page": page,
            "meta_key": "vehicle_serial",
            "meta_value": serial
        })
        
        if response.status_code != 200:
            break
            
        products = response.json()
        if not products:
            break
            
        all_products.extend(products)
        page += 1
    
    # Group by original_sku (oscar_part_id)
    by_part_id = {}
    by_original_sku = {}
    
    for product in all_products:
        part_id = None
        original_sku = None
        
        for meta in product.get('meta_data', []):
            if meta['key'] == 'oscar_part_id':
                part_id = meta['value']
            elif meta['key'] == 'original_sku':
                original_sku = meta['value']
        
        if part_id:
            if part_id not in by_part_id:
                by_part_id[part_id] = []
            by_part_id[part_id].append(product['sku'])
        
        if original_sku:
            if original_sku not in by_original_sku:
                by_original_sku[original_sku] = []
            by_original_sku[original_sku].append(product['sku'])
    
    # Find duplicates
    duplicate_part_ids = {k: v for k, v in by_part_id.items() if len(v) > 1}
    duplicate_original_skus = {k: v for k, v in by_original_sku.items() if len(v) > 1}
    
    return len(all_products), len(by_part_id), len(by_original_sku), duplicate_part_ids, duplicate_original_skus

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_serial_count.py SERIAL")
        sys.exit(1)
    
    serial = sys.argv[1]
    
    # Load credentials
    consumer_key, consumer_secret = load_credentials()
    
    print(f"\n{'='*70}")
    print(f"CHECKING COUNTS FOR SERIAL: {serial}")
    print(f"{'='*70}\n")
    
    # Check database
    print("📊 DATABASE CHECK:")
    db_unique, db_dupes = check_database_count(serial)
    print(f"   Unique part_ids in database: {db_unique}")
    
    if db_dupes:
        print(f"   ⚠️  WARNING: {len(db_dupes)} part_ids appear multiple times in query results!")
        print(f"   This suggests the JOIN is creating duplicates.")
        for part_id, count in db_dupes[:5]:
            print(f"      - part_id {part_id}: appears {count} times")
    else:
        print(f"   ✅ No duplicate part_ids in database query")
    
    # Check WordPress
    print(f"\n📦 WORDPRESS CHECK:")
    wp_total, wp_unique_parts, wp_unique_originals, wp_dup_parts, wp_dup_originals = check_wordpress_count(serial, consumer_key, consumer_secret)
    print(f"   Total products in WordPress: {wp_total}")
    print(f"   Unique oscar_part_ids: {wp_unique_parts}")
    print(f"   Unique original_skus: {wp_unique_originals}")
    
    if wp_dup_parts:
        print(f"\n   ⚠️  DUPLICATES BY PART_ID: {len(wp_dup_parts)} part_ids have multiple products!")
        for part_id, skus in list(wp_dup_parts.items())[:5]:
            print(f"      - part_id {part_id}: {len(skus)} products with SKUs: {', '.join(skus[:3])}")
    else:
        print(f"   ✅ No duplicate oscar_part_ids in WordPress")
    
    if wp_dup_originals:
        print(f"\n   ⚠️  DUPLICATES BY ORIGINAL_SKU: {len(wp_dup_originals)} original SKUs have multiple products!")
        for orig_sku, skus in list(wp_dup_originals.items())[:5]:
            print(f"      - original_sku {orig_sku}: {len(skus)} products")
    else:
        print(f"   ✅ No duplicate original_skus in WordPress")
    
    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY:")
    print(f"{'='*70}")
    print(f"   Database should have: {db_unique} unique parts")
    print(f"   WordPress has: {wp_total} products ({wp_unique_parts} unique part_ids)")
    
    if db_unique == wp_unique_parts:
        print(f"   ✅ MATCH! WordPress part count matches database")
    else:
        diff = wp_total - db_unique
        print(f"   ⚠️  MISMATCH! Difference: {diff:+d} products")
        
        if wp_total > db_unique:
            print(f"      → WordPress has {diff} MORE products than expected")
            if wp_dup_parts:
                print(f"      → {len(wp_dup_parts)} duplicate part_ids account for extra products")
        else:
            print(f"      → WordPress has {abs(diff)} FEWER products than expected")
    
    print()
