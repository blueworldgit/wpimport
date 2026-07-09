import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'dbname': 'parts_store',
    'user': 'postgres',
    'password': 'N0rwich!',
    'host': '80.95.207.42',
    'port': '5432'
}

serial = 'LSH14C4C5NA129710'

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=RealDictCursor)

# Check what Oscar has for this serial in the category tables
cur.execute("""
    SELECT DISTINCT
        sn.serial,
        pt.title as parent_category,
        ct.title as child_category,
        COUNT(*) OVER (PARTITION BY pt.title, ct.title) as combo_count
    FROM motorpartsdata_serialnumber sn
    JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
    JOIN motorpartsdata_childtitle ct ON ct.parent_id = pt.id
    WHERE sn.serial = %s
    ORDER BY pt.title, ct.title
""", (serial,))
rows = cur.fetchall()
print(f'Oscar category rows for {serial}: {len(rows)}\n')
print(f'{"parent_category":<45} {"child_category":<45}')
print('-' * 92)
for r in rows:
    print(f'{str(r["parent_category"]):<45} {str(r["child_category"]):<45}')

# Also check if the serial even exists
cur.execute("SELECT id, serial, vehicle_brand FROM motorpartsdata_serialnumber WHERE serial = %s", (serial,))
sn = cur.fetchone()
print(f'\nSerial record: {sn}')

# Check parent titles exist
cur.execute("""
    SELECT COUNT(*) as cnt FROM motorpartsdata_parenttitle pt
    JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
    WHERE sn.serial = %s
""", (serial,))
print(f'Parent title rows: {cur.fetchone()["cnt"]}')

# Check child titles exist
cur.execute("""
    SELECT COUNT(*) as cnt FROM motorpartsdata_childtitle ct
    JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id
    JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
    WHERE sn.serial = %s
""", (serial,))
print(f'Child title rows: {cur.fetchone()["cnt"]}')

cur.close()
conn.close()
