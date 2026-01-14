#!/usr/bin/env python3
"""
Quick script to connect to Oscar PostgreSQL database and inspect the data
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
import sys

base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))

# Database connection parameters
DB_CONFIG = {
    'dbname': 'parts_store',
    'user': 'postgres',
    'password': 'N0rwich!',
    'host': '80.95.207.42',
    'port': '5432'
}

def test_connection():
    """Test database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✓ Database connection successful\n")
        return conn
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return None

def check_tables(conn):
    """List all tables in the database"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    print("=" * 60)
    print("Available Tables")
    print("=" * 60)
    for table in tables:
        print(f"  - {table['table_name']}")
    cursor.close()
    return [t['table_name'] for t in tables]

def inspect_serial_numbers(conn):
    """Check SerialNumber table"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT COUNT(*) as count FROM motorpartsdata_serialnumber;")
    count = cursor.fetchone()['count']
    print(f"\n{'=' * 60}")
    print(f"SerialNumber Table: {count} records")
    print("=" * 60)
    
    if count > 0:
        cursor.execute("SELECT * FROM motorpartsdata_serialnumber LIMIT 5;")
        serials = cursor.fetchall()
        for serial in serials:
            print(f"  ID: {serial['id']}, Serial: {serial['serial']}, Brand: {serial['vehicle_brand']}")
    cursor.close()

def inspect_parts(conn, limit=5):
    """Check Parts table with related data"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get total count
    cursor.execute("SELECT COUNT(*) as count FROM motorpartsdata_part;")
    count = cursor.fetchone()['count']
    
    print(f"\n{'=' * 60}")
    print(f"Parts Table: {count} records")
    print("=" * 60)
    
    if count > 0:
        # Get sample parts with their relationships
        cursor.execute("""
            SELECT 
                p.id,
                p.part_number,
                p.usage_name,
                p.unit_qty,
                p.lr,
                p.call_out_order,
                ct.title as child_title,
                ct.svg_code,
                pt.title as parent_title,
                sn.serial,
                sn.vehicle_brand
            FROM motorpartsdata_part p
            JOIN motorpartsdata_childtitle ct ON p.child_title_id = ct.id
            JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id
            JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
            LIMIT %s;
        """, (limit,))
        
        parts = cursor.fetchall()
        print(f"\nSample of {len(parts)} parts:\n")
        for part in parts:
            print(f"Part #{part['id']}: {part['part_number']}")
            print(f"  Name: {part['usage_name']}")
            print(f"  Serial: {part['serial']} ({part['vehicle_brand']})")
            print(f"  Parent: {part['parent_title']}")
            print(f"  Child: {part['child_title']}")
            print(f"  SVG: {len(part['svg_code'])} chars")
            print(f"  Qty: {part['unit_qty']}, LR: {part['lr']}, Callout: {part['call_out_order']}")
            print()
    
    cursor.close()

def check_pricing(conn):
    """Check if pricing data exists"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT COUNT(*) as count FROM motorpartsdata_pricingdata;")
    count = cursor.fetchone()['count']
    print(f"\n{'=' * 60}")
    print(f"PricingData Table: {count} records")
    print("=" * 60)
    
    if count > 0:
        cursor.execute("""
            SELECT pd.*, p.part_number, p.usage_name
            FROM motorpartsdata_pricingdata pd
            JOIN motorpartsdata_part p ON pd.part_number_id = p.id
            WHERE pd.list_price IS NOT NULL
            LIMIT 5;
        """)
        prices = cursor.fetchall()
        print("\nSample pricing data:\n")
        for price in prices:
            print(f"  {price['part_number']}: £{price['list_price']} (Stock: {price['stock_available']})")
    cursor.close()

def get_serial_stats(conn, serial):
    """Get stats for a specific serial"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print(f"\n{'=' * 60}")
    print(f"Stats for Serial: {serial}")
    print("=" * 60)
    
    cursor.execute("""
        SELECT COUNT(DISTINCT p.id) as part_count,
               COUNT(DISTINCT ct.id) as diagram_count,
               COUNT(DISTINCT pt.id) as category_count
        FROM motorpartsdata_serialnumber sn
        JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
        JOIN motorpartsdata_childtitle ct ON ct.parent_id = pt.id
        JOIN motorpartsdata_part p ON p.child_title_id = ct.id
        WHERE sn.serial = %s;
    """, (serial,))
    
    stats = cursor.fetchone()
    if stats:
        print(f"  Parts: {stats['part_count']}")
        print(f"  Diagrams: {stats['diagram_count']}")
        print(f"  Categories: {stats['category_count']}")
    else:
        print(f"  Serial '{serial}' not found in database")
    
    cursor.close()

def main():
    print("\n" + "=" * 60)
    print("Oscar Database Inspector")
    print("=" * 60 + "\n")
    
    conn = test_connection()
    if not conn:
        return
    
    try:
        tables = check_tables(conn)
        inspect_serial_numbers(conn)
        inspect_parts(conn, limit=3)
        check_pricing(conn)
        
        # Check specific serial if provided
        if len(sys.argv) > 1:
            serial = sys.argv[1]
            get_serial_stats(conn, serial)
        else:
            # Check our test serial
            get_serial_stats(conn, 'LSH14J7C7MA114771')
        
    finally:
        conn.close()
        print("\n" + "=" * 60)
        print("Database connection closed")
        print("=" * 60 + "\n")

if __name__ == '__main__':
    main()
