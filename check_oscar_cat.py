#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib

conn = psycopg2.connect(dbname='parts_store', user='postgres', password='N0rwich!', host='80.95.207.42', port='5432')
cur = conn.cursor(cursor_factory=RealDictCursor)

# Look up what parent 39 and child 4_1674 are for LSFAL11A4PA157891
print("=== Parent 39 for LSFAL11A4PA157891 ===")
cur.execute('''
    SELECT pt.id, pt.title, sn.serial
    FROM motorpartsdata_parenttitle pt
    JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
    WHERE sn.serial = %s AND pt.id = 39
''', ('LSFAL11A4PA157891',))
for r in cur.fetchall():
    print(f"  parent id={r['id']} title={r['title']}")

print()
print("=== Child 4_1674 (id=1674) for LSFAL11A4PA157891 ===")
cur.execute('''
    SELECT ct.id, ct.title, pt.title as parent_title
    FROM motorpartsdata_childtitle ct
    JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id
    JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
    WHERE sn.serial = %s AND ct.id = 1674
''', ('LSFAL11A4PA157891',))
for r in cur.fetchall():
    print(f"  child id={r['id']} title={r['title']} under parent={r['parent_title']}")

print()
print("=== All parts in child 1674 for LSFAL11A4PA157891 ===")
cur.execute('''
    SELECT p.id as part_id, p.part_number, p.usage_name, p.call_out_order
    FROM motorpartsdata_part p
    JOIN motorpartsdata_childtitle ct ON p.child_title_id = ct.id
    JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id
    JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
    WHERE sn.serial = %s AND ct.id = 1674
    ORDER BY p.call_out_order
''', ('LSFAL11A4PA157891',))
rows = cur.fetchall()
print(f"Total parts: {len(rows)}")
for r in rows:
    hash_input = f"{r['part_number']}-{r['part_id']}"
    suffix = hashlib.md5(hash_input.encode()).hexdigest()[:4].upper()
    wp_sku = f"{r['part_number']}-{suffix}"
    print(f"  part_id={r['part_id']}  wp_sku={wp_sku}  callout={r['call_out_order']}  usage={r['usage_name']}")

print()
print("=== C00086415 in LSFAL11A4PA157891 ===")
cur.execute('''
    SELECT p.id as part_id, p.part_number, p.usage_name, p.call_out_order,
           ct.id as child_id, ct.title as sub_category, pt.id as parent_id, pt.title as main_category
    FROM motorpartsdata_part p
    JOIN motorpartsdata_childtitle ct ON p.child_title_id = ct.id
    JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id
    JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
    WHERE sn.serial = %s AND p.part_number = %s
''', ('LSFAL11A4PA157891', 'C00086415'))
rows = cur.fetchall()
print(f"Rows: {len(rows)}")
for r in rows:
    hash_input = f"{r['part_number']}-{r['part_id']}"
    suffix = hashlib.md5(hash_input.encode()).hexdigest()[:4].upper()
    wp_sku = f"{r['part_number']}-{suffix}"
    print(f"  part_id={r['part_id']}  wp_sku={wp_sku}  parent_id={r['parent_id']}  main={r['main_category']}  child_id={r['child_id']}  child={r['sub_category']}  usage={r['usage_name']}")

cur.close()
conn.close()
