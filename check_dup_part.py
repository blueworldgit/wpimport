#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(dbname='parts_store', user='postgres', password='N0rwich!', host='80.95.207.42', port='5432')
cur = conn.cursor(cursor_factory=RealDictCursor)

cur.execute('''
    SELECT p.id as part_id, p.part_number, p.usage_name, p.call_out_order, p.lr, p.remark,
           ct.title as sub_category, pt.title as main_category, sn.serial
    FROM motorpartsdata_part p
    JOIN motorpartsdata_childtitle ct ON p.child_title_id = ct.id
    JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id
    JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
    WHERE p.part_number = %s
    ORDER BY sn.serial, p.id
''', ('C00186732',))

rows = cur.fetchall()
print(f'Total rows for C00186732: {len(rows)}')
for r in rows:
    print(f"  part_id={r['part_id']} serial={r['serial']} callout={r['call_out_order']} "
          f"usage={r['usage_name']} parent={r['main_category']} child={r['sub_category']} lr={r['lr']}")

print()

# Also show how many distinct part_numbers appear more than once per serial
cur.execute('''
    SELECT sn.serial, p.part_number, COUNT(p.id) as row_count,
           COUNT(DISTINCT ct.title) as distinct_children,
           COUNT(DISTINCT pt.title) as distinct_parents
    FROM motorpartsdata_part p
    JOIN motorpartsdata_childtitle ct ON p.child_title_id = ct.id
    JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id
    JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
    WHERE sn.serial = 'LSH14C4C5NA129710'
    GROUP BY sn.serial, p.part_number
    HAVING COUNT(p.id) > 1
    ORDER BY row_count DESC
    LIMIT 20
''')
dups = cur.fetchall()
print(f'\nParts appearing >1 time for LSH14C4C5NA129710: {len(dups)} (showing top 20)')
for d in dups:
    print(f"  {d['part_number']}: {d['row_count']} rows, {d['distinct_parents']} parents, {d['distinct_children']} children")

cur.close()
conn.close()
