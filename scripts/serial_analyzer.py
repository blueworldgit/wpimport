#!/usr/bin/env python3
"""
Oscar Serial Analyzer
Analyzes categories and parts for a specific serial number from Oscar database
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import argparse
import sys

# Database connection parameters
DB_CONFIG = {
    'dbname': 'parts_store',
    'user': 'postgres',
    'password': 'N0rwich!',
    'host': '80.95.207.42',
    'port': '5432'
}

def analyze_serial(serial_number):
    """Analyze a specific serial for categories and parts"""
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print(f"🔍 Analyzing serial: {serial_number}")
        
        # First, find the serial in the database
        cursor.execute("""
            SELECT id, serial, vehicle_brand 
            FROM motorpartsdata_serialnumber 
            WHERE serial = %s
        """, [serial_number])
        
        serial_record = cursor.fetchone()
        
        if not serial_record:
            print(f"❌ Serial '{serial_number}' not found in Oscar database")
            return False
        
        serial_id = serial_record['id']
        vehicle_brand = serial_record['vehicle_brand']
        
        print(f"✓ Found serial: {serial_number} ({vehicle_brand})")
        
        # Get main categories (parent titles) for this serial
        cursor.execute("""
            SELECT id, title 
            FROM motorpartsdata_parenttitle 
            WHERE serial_number_id = %s
            ORDER BY title
        """, [serial_id])
        
        parent_titles = cursor.fetchall()
        main_categories_count = len(parent_titles)
        
        print(f"📁 Main categories: {main_categories_count}")
        
        if main_categories_count == 0:
            print("❌ No categories found for this serial")
            return True
        
        # Get subcategories (child titles) for all parent titles
        parent_ids = [pt['id'] for pt in parent_titles]
        placeholders = ','.join(['%s'] * len(parent_ids))
        
        cursor.execute(f"""
            SELECT id, title, parent_title_id
            FROM motorpartsdata_childtitle 
            WHERE parent_title_id IN ({placeholders})
            ORDER BY parent_title_id, title
        """, parent_ids)
        
        child_titles = cursor.fetchall()
        sub_categories_count = len(child_titles)
        
        print(f"📂 Sub-categories: {sub_categories_count}")
        
        # Get total parts for all child titles
        child_ids = [ct['id'] for ct in child_titles]
        
        if child_ids:
            placeholders = ','.join(['%s'] * len(child_ids))
            
            cursor.execute(f"""
                SELECT COUNT(*) as total_parts
                FROM motorpartsdata_part 
                WHERE child_title_id IN ({placeholders})
            """, child_ids)
            
            parts_result = cursor.fetchone()
            total_parts = parts_result['total_parts'] if parts_result else 0
        else:
            total_parts = 0
        
        print(f"📦 Total parts: {total_parts}")
        
        # Show breakdown by main category
        print(f"\n📊 Breakdown by main category:")
        print("-" * 60)
        
        grand_total_parts = 0
        
        for parent in parent_titles:
            parent_id = parent['id']
            parent_title = parent['title']
            
            # Get child categories for this parent
            cursor.execute("""
                SELECT id, title 
                FROM motorpartsdata_childtitle 
                WHERE parent_title_id = %s
                ORDER BY title
            """, [parent_id])
            
            children = cursor.fetchall()
            
            # Get parts count for this parent category
            if children:
                child_ids_for_parent = [c['id'] for c in children]
                placeholders = ','.join(['%s'] * len(child_ids_for_parent))
                
                cursor.execute(f"""
                    SELECT COUNT(*) as parts_count
                    FROM motorpartsdata_part 
                    WHERE child_title_id IN ({placeholders})
                """, child_ids_for_parent)
                
                parent_parts_result = cursor.fetchone()
                parent_parts_count = parent_parts_result['parts_count'] if parent_parts_result else 0
            else:
                parent_parts_count = 0
            
            grand_total_parts += parent_parts_count
            
            print(f"📁 {parent_title}")
            print(f"   📂 Sub-categories: {len(children)}")
            print(f"   📦 Parts: {parent_parts_count}")
            
            # Show subcategories if requested (limit to avoid too much output)
            if len(children) <= 10:
                for child in children:
                    child_id = child['id']
                    child_title = child['title']
                    
                    cursor.execute("""
                        SELECT COUNT(*) as parts_count
                        FROM motorpartsdata_part 
                        WHERE child_title_id = %s
                    """, [child_id])
                    
                    child_parts_result = cursor.fetchone()
                    child_parts_count = child_parts_result['parts_count'] if child_parts_result else 0
                    
                    print(f"     📄 {child_title}: {child_parts_count} parts")
            elif len(children) > 10:
                print(f"     ... ({len(children)} subcategories - use detailed report for full list)")
            
            print()
        
        # Summary
        print("=" * 60)
        print(f"📋 SUMMARY FOR {serial_number}")
        print("=" * 60)
        print(f"🚗 Vehicle: {vehicle_brand}")
        print(f"📁 Main categories: {main_categories_count}")
        print(f"📂 Sub-categories: {sub_categories_count}")
        print(f"📦 Total parts: {grand_total_parts}")
        print(f"📊 Average parts per category: {grand_total_parts/main_categories_count:.1f}" if main_categories_count > 0 else "")
        print(f"📊 Average subcategories per main category: {sub_categories_count/main_categories_count:.1f}" if main_categories_count > 0 else "")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Analyze Oscar database for serial number statistics')
    parser.add_argument('--serial', required=True, help='Serial number to analyze (e.g., LSFAL11A4PA157987)')
    parser.add_argument('--detailed', action='store_true', help='Show detailed breakdown of all subcategories')
    
    args = parser.parse_args()
    
    print("="*80)
    print("🏭 OSCAR SERIAL ANALYZER")
    print("="*80)
    
    success = analyze_serial(args.serial)
    
    if not success:
        return 1
    
    print("\n✅ Analysis complete!")
    return 0

if __name__ == "__main__":
    exit(main())