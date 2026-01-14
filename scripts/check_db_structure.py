import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection
conn = psycopg2.connect(
    dbname='parts_store', 
    user='postgres', 
    password='N0rwich!', 
    host='80.95.207.42', 
    port='5432'
)

cursor = conn.cursor()

# Get all motorpartsdata tables
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE 'motorpartsdata%' 
    ORDER BY table_name
""")

tables = cursor.fetchall()
print("🗃️  Available Tables:")
for table in tables:
    print(f"  📋 {table[0]}")

print("\n" + "="*60)

# Check structure of each table
for table in tables:
    table_name = table[0]
    print(f"\n📊 Table: {table_name}")
    
    # Get column info
    cursor.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position
    """)
    
    columns = cursor.fetchall()
    print("   Columns:")
    for col in columns:
        print(f"     • {col[0]} ({col[1]})")
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"   Rows: {count:,}")
    
    # Show sample data
    cursor_dict = conn.cursor(cursor_factory=RealDictCursor)
    cursor_dict.execute(f"SELECT * FROM {table_name} LIMIT 3")
    samples = cursor_dict.fetchall()
    
    if samples:
        print("   Sample data:")
        for i, sample in enumerate(samples, 1):
            print(f"     Row {i}: {dict(sample)}")
    
    cursor_dict.close()

conn.close()