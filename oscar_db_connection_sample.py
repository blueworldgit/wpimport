#!/usr/bin/env python3
"""
Sample script to connect to Oscar database
Shows two common connection patterns used in this project
"""
import psycopg2
from psycopg2.extras import RealDictCursor

# ============================================================================
# METHOD 1: Direct connection with hardcoded credentials
# ============================================================================
def connect_direct():
    """Connect using hardcoded database credentials"""
    DB_CONFIG = {
        'dbname': 'parts_store',
        'user': 'postgres',
        'password': 'N0rwich!',
        'host': '80.95.207.42',
        'port': '5432'
    }
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected to Oscar database (direct method)")
        return conn
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None


# ============================================================================
# METHOD 2: Load credentials from productioncreds.txt file
# ============================================================================
def load_db_credentials():
    """
    Load database credentials from productioncreds.txt
    Expected file format (lines 3-7):
        Line 3: host
        Line 4: database name
        Line 5: username
        Line 6: password
        Line 7: port
    """
    try:
        with open('productioncreds.txt', 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            host = lines[3]
            database = lines[4]
            user = lines[5]
            password = lines[6]
            port = lines[7]
            return host, database, user, password, port
    except FileNotFoundError:
        print("❌ productioncreds.txt not found")
        return None, None, None, None, None
    except IndexError:
        print("❌ productioncreds.txt does not have enough lines")
        return None, None, None, None, None


def connect_from_file():
    """Connect using credentials from productioncreds.txt"""
    host, database, user, password, port = load_db_credentials()
    
    if not all([host, database, user, password, port]):
        print("❌ Missing credentials")
        return None
    
    try:
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        print("✅ Connected to Oscar database (file method)")
        return conn
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None


# ============================================================================
# SAMPLE USAGE
# ============================================================================
def main():
    """Demonstrate both connection methods and run a test query"""
    
    print("=" * 70)
    print("OSCAR DATABASE CONNECTION SAMPLE")
    print("=" * 70)
    
    # Try Method 1: Direct connection
    print("\n🔌 Method 1: Direct connection...")
    conn = connect_direct()
    
    if conn:
        # Test the connection with a simple query
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get table list
        cursor.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
            LIMIT 5
        """)
        
        print("\n📊 Sample tables in database:")
        for row in cursor.fetchall():
            print(f"   • {row['tablename']}")
        
        # Get parts count
        cursor.execute("SELECT COUNT(*) as count FROM motorpartsdata_part")
        count = cursor.fetchone()['count']
        print(f"\n🔧 Total parts in motorpartsdata_part: {count:,}")
        
        cursor.close()
        conn.close()
        print("\n✅ Connection closed")
    
    print("\n" + "=" * 70)
    
    # Try Method 2: From file (if available)
    print("\n🔌 Method 2: Connection from productioncreds.txt...")
    conn2 = connect_from_file()
    
    if conn2:
        cursor = conn2.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"\n🐘 PostgreSQL version: {version}")
        
        cursor.close()
        conn2.close()
        print("✅ Connection closed")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
