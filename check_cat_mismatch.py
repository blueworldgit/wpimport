#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib

conn = psycopg2.connect(dbname='parts_store', user='postgres', password='N0rwich!', host='80.95.207.42', port='5432')
cur = conn.cursor(cursor_factory=RealDictCursor)

# Find all Oscar rows for this part number across all serials
cur.execute('''
    SELECT p.id as part_id, p.part_number, p.usage_name, p.call_out_order, p.lr,
           ct.title as sub_category, pt.title as main_category, sn.serial
    FROM motorpartsdata_part p
    JOIN motorpartsdata_childtitle ct ON p.child_title_id = ct.id
    JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id
    JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
    WHERE p.part_number = %s AND sn.serial = %s
    ORDER BY p.id
''', ('C00086415', 'LSH14J7CXMA114599'))

rows = cur.fetchall()
print(f'Oscar rows for C00086415 / LSH14J7CXMA114599: {len(rows)}')
for r in rows:
    hash_input = f"{r['part_number']}-{r['part_id']}"
    suffix = hashlib.md5(hash_input.encode()).hexdigest()[:4].upper()
    wp_sku = f"{r['part_number']}-{suffix}"
    print(f"  part_id={r['part_id']}  wp_sku={wp_sku}  main={r['main_category']}  child={r['sub_category']}  usage={r['usage_name']}  callout={r['call_out_order']}")

cur.close()
conn.close()
