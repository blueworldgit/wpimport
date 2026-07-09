import psycopg2

conn = psycopg2.connect(host='80.95.207.42', port=5432, dbname='parts_store',
                         user='postgres', password='N0rwich!')
cur = conn.cursor()

skus = ['C00021127', 'C00058223', 'C00074560', 'B00005870', 'B00004124']
for sku in skus:
    cur.execute("SELECT part_number, usage_name FROM motorpartsdata_part WHERE TRIM(part_number) = %s LIMIT 1", (sku,))
    row = cur.fetchone()
    if row:
        print(f"{sku}: EXISTS in Oscar - {row[1]}")
    else:
        print(f"{sku}: NOT FOUND in Oscar motorpartsdata_part")

cur.close()
conn.close()
