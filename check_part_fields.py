#!/usr/bin/env python3
"""Check available fields in motorpartsdata_part table"""
import sys
import os
sys.path.append('scripts')
from fast_create_categories import FastCategoryCreator

def check_part_fields():
    creator = FastCategoryCreator()
    if not creator.connect():
        print("❌ Failed to connect to database")
        return
    
    cursor = creator.conn.cursor()
    
    # Get table schema
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'motorpartsdata_part'
        ORDER BY ordinal_position
    """)
    
    columns = cursor.fetchall()
    print("📊 motorpartsdata_part table columns:")
    for col_name, data_type in columns:
        print(f"   • {col_name}: {data_type}")
    
    # Check a sample record to see actual data
    cursor.execute("SELECT * FROM motorpartsdata_part LIMIT 1")
    sample = cursor.fetchone()
    
    if sample:
        print(f"\n📋 Sample record:")
        for i, (col_name, _) in enumerate(columns):
            value = sample[i] if i < len(sample) else 'NULL'
            print(f"   • {col_name}: {value}")
    
    cursor.close()
    creator.conn.close()

if __name__ == "__main__":
    check_part_fields()