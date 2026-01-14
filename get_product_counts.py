#!/usr/bin/env python3
"""
Get total product counts from Oscar database
"""
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection
DB_CONFIG = {
    'dbname': 'parts_store',
    'user': 'postgres',
    'password': 'N0rwich!',
    'host': '80.95.207.42',
    'port': '5432'
}

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor(cursor_factory=RealDictCursor)

print('📊 TOTAL PRODUCT COUNTS IN OSCAR DATABASE')
print('=' * 60)

# Total individual part instances (before any deduplication)
cursor.execute('SELECT COUNT(*) as total_parts FROM motorpartsdata_part')
total_parts = cursor.fetchone()['total_parts']
print(f'🔧 Total part instances (all): {total_parts:,}')

# Unique SKUs 
cursor.execute('SELECT COUNT(DISTINCT part_number) as unique_skus FROM motorpartsdata_part')
unique_skus = cursor.fetchone()['unique_skus']
print(f'📦 Unique SKUs (all): {unique_skus:,}')

# Total instances for specific serial
cursor.execute("""
    SELECT COUNT(*) as serial_parts 
    FROM motorpartsdata_part p
    JOIN motorpartsdata_childtitle ct ON p.child_title_id = ct.id
    JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id  
    JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
    WHERE sn.serial = 'LSFAL11A4PA157987'
""")
serial_parts = cursor.fetchone()['serial_parts']
print(f'🎯 Parts for LSFAL11A4PA157987: {serial_parts:,}')

# Unique SKUs for specific serial
cursor.execute("""
    SELECT COUNT(DISTINCT p.part_number) as serial_unique_skus
    FROM motorpartsdata_part p
    JOIN motorpartsdata_childtitle ct ON p.child_title_id = ct.id
    JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id
    JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
    WHERE sn.serial = 'LSFAL11A4PA157987'
""")
serial_unique_skus = cursor.fetchone()['serial_unique_skus']
print(f'📦 Unique SKUs for LSFAL11A4PA157987: {serial_unique_skus:,}')

# Total serials
cursor.execute('SELECT COUNT(*) as total_serials FROM motorpartsdata_serialnumber')
total_serials = cursor.fetchone()['total_serials']
print(f'🚗 Total vehicle serials: {total_serials:,}')

# Total diagrams/categories
cursor.execute('SELECT COUNT(*) as total_diagrams FROM motorpartsdata_childtitle')
total_diagrams = cursor.fetchone()['total_diagrams']
print(f'📋 Total diagrams/categories: {total_diagrams:,}')

print(f'\n📈 DEDUPLICATION IMPACT:')
print(f'   🌐 All serials: {total_parts:,} instances → {unique_skus:,} unique SKUs ({((total_parts - unique_skus) / total_parts * 100):.1f}% reduction)')
print(f'   🎯 LSFAL11A4PA157987: {serial_parts:,} instances → {serial_unique_skus:,} unique SKUs ({((serial_parts - serial_unique_skus) / serial_parts * 100):.1f}% reduction)')

print(f'\n📊 SCALE BREAKDOWN:')
print(f'   📱 Average parts per serial: {total_parts // total_serials:,}')
print(f'   📊 Average diagrams per serial: {total_diagrams // total_serials:,}')
print(f'   🔄 Average instances per unique SKU: {total_parts // unique_skus:.1f}')

cursor.close()
conn.close()