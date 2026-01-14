#!/usr/bin/env python3
"""
Oscar Database Reporting Script
Connects to Oscar database and provides detailed reports on serials, categories, and product counts
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from collections import defaultdict, Counter
from pathlib import Path
import sys
import argparse
from datetime import datetime

# Database connection parameters
DB_CONFIG = {
    'dbname': 'parts_store',
    'user': 'postgres',
    'password': 'N0rwich!',
    'host': '80.95.207.42',
    'port': '5432'
}

class OscarReporter:
    def __init__(self):
        self.conn = None
        
    def connect_db(self):
        """Connect to Oscar database"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            print("✓ Connected to Oscar database")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def get_serials_overview(self):
        """Get overview of all serials and their part counts"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Get serial overview with corrected category counts (using same table structure as fast_create_categories)
        cursor.execute("""
            WITH category_data AS (
                SELECT DISTINCT
                    sn.serial,
                    sn.vehicle_brand,
                    pt.title as parent_category,
                    ct.title as child_category
                FROM motorpartsdata_serialnumber sn
                JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
                JOIN motorpartsdata_childtitle ct ON ct.parent_id = pt.id
                -- Filter out self-referencing categories after sanitization
                WHERE REGEXP_REPLACE(
                    REGEXP_REPLACE(
                        REGEXP_REPLACE(pt.title, '^[A-Z]{2}[0-9]+[A-Z]?[0-9]+\s*-\s*', ''),
                        '[&]', 'and', 'g'
                    ), 
                    '[/\\(),]', '', 'g'
                ) != REGEXP_REPLACE(
                    REGEXP_REPLACE(
                        REGEXP_REPLACE(ct.title, '^[A-Z]{2}[0-9]+[A-Z]?[0-9]+\s*-\s*', ''),
                        '[&]', 'and', 'g'
                    ), 
                    '[/\\(),]', '', 'g'
                )
            ),
            part_counts AS (
                SELECT 
                    sn.serial,
                    COUNT(DISTINCT p.id) as total_parts,
                    COUNT(DISTINCT p.part_number) as unique_skus
                FROM motorpartsdata_serialnumber sn
                JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
                JOIN motorpartsdata_childtitle ct ON ct.parent_id = pt.id
                JOIN motorpartsdata_part p ON p.child_title_id = ct.id
                GROUP BY sn.serial
            )
            SELECT 
                cd.serial,
                cd.vehicle_brand,
                COUNT(DISTINCT cd.parent_category) as parent_categories,
                COUNT(DISTINCT cd.child_category) as child_categories,
                COALESCE(pc.total_parts, 0) as total_parts,
                COALESCE(pc.unique_skus, 0) as unique_skus
            FROM category_data cd
            LEFT JOIN part_counts pc ON cd.serial = pc.serial
            GROUP BY cd.serial, cd.vehicle_brand, pc.total_parts, pc.unique_skus
            ORDER BY cd.serial
        """)
        
        serials = cursor.fetchall()
        
        print("\n" + "="*120)
        print("📊 SERIALS OVERVIEW")
        print("="*120)
        print(f"{'Serial':<25} {'Brand':<10} {'Main Cat':<10} {'Sub Cat':<10} {'Total Parts':<12} {'Unique SKUs':<12}")
        print("-" * 100)
        
        total_parts = 0
        total_skus = 0
        
        for serial in serials:
            print(f"{serial['serial']:<25} {serial['vehicle_brand']:<10} {serial['parent_categories']:<10} {serial['child_categories']:<10} {serial['total_parts']:<12} {serial['unique_skus']:<12}")
            total_parts += serial['total_parts'] or 0
            total_skus += serial['unique_skus'] or 0
        
        print("-" * 100)
        print(f"{'TOTALS:':<25} {'':<10} {'':<10} {'':<10} {total_parts:<12} {total_skus:<12}")
        
        cursor.close()
        return serials

    def get_categories_hierarchy(self, serial_filter=None):
        """Get complete category hierarchy with product counts"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Build query with optional serial filter
        where_clause = ""
        params = []
        if serial_filter:
            where_clause = "WHERE sn.serial = %s"
            params = [serial_filter]
        
        # Get complete hierarchy with actual database structure
        query = f"""
            SELECT 
                sn.serial,
                sn.vehicle_brand,
                pt.title as parent_category,
                ct.title as child_category,
                p.part_number,
                p.usage_name,
                p.call_out_order,
                p.unit_qty,
                pd.list_price,
                pd.description as pricing_description,
                pd.active as is_active
            FROM motorpartsdata_serialnumber sn
            LEFT JOIN motorpartsdata_parenttitle pt ON sn.id = pt.serial_number_id
            LEFT JOIN motorpartsdata_childtitle ct ON pt.id = ct.parent_id
            LEFT JOIN motorpartsdata_part p ON ct.id = p.child_title_id
            LEFT JOIN motorpartsdata_pricingdata pd ON p.id = pd.part_number_id
            {where_clause}
            ORDER BY sn.serial, pt.title, ct.title, p.call_out_order
        """
        
        cursor.execute(query, params)
        parts = cursor.fetchall()
        
        # Organize data by serial -> parent -> child
        hierarchy = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        
        for part in parts:
            if not part['parent_category']:  # Skip if no categories
                continue
                
            serial = part['serial']
            parent = part['parent_category']
            child = part['child_category'] or 'Uncategorized'
            
            hierarchy[serial][parent][child].append({
                'sku': part['part_number'],
                'name': part['usage_name'],
                'call_out': part['call_out_order'],
                'qty': part['unit_qty'],
                'price': part['list_price'],
                'pricing_desc': part['pricing_description'],
                'active': part['is_active']
            })
        
        cursor.close()
        return hierarchy

    def print_categories_report(self, serial_filter=None):
        """Print detailed categories report"""
        hierarchy = self.get_categories_hierarchy(serial_filter)
        
        title = f"📂 CATEGORIES HIERARCHY"
        if serial_filter:
            title += f" - Serial: {serial_filter}"
        
        print("\n" + "="*130)
        print(title)
        print("="*130)
        
        total_parts = 0
        
        for serial, parents in hierarchy.items():
            if serial_filter and serial != serial_filter:
                continue
                
            print(f"\n🚗 Serial: {serial}")
            print("-" * 120)
            
            serial_parts = 0
            for parent, children in parents.items():
                parent_parts = sum(len(parts) for parts in children.values())
                serial_parts += parent_parts
                
                print(f"  📁 {parent} ({parent_parts} parts)")
                
                for child, parts in children.items():
                    if len(parts) > 0:
                        print(f"    📂 {child} ({len(parts)} parts)")
                        
                        # Show sample parts (first 5)
                        sample_parts = parts[:5]
                        for part in sample_parts:
                            price_info = f"£{part['price']}" if part['price'] else "No price"
                            active_status = "✓" if part['active'] == 'A' else "✗"
                            print(f"      • [{part['call_out']:>2}] {part['sku']} - {part['name'][:40]}{'...' if len(part['name']) > 40 else '':<3} | {price_info:<8} {active_status}")
                        
                        if len(parts) > 5:
                            print(f"      ... and {len(parts) - 5} more parts")
            
            print(f"  📊 Serial Total: {serial_parts} parts")
            total_parts += serial_parts
        
        print(f"\n🎯 Grand Total: {total_parts} parts")

    def get_sku_distribution(self, serial_filter=None):
        """Get SKU distribution across serials"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        where_clause = ""
        params = []
        if serial_filter:
            where_clause = "WHERE sn.serial = %s"
            params = [serial_filter]
        
        # Get SKU counts across serials with proper joins
        query = f"""
            SELECT 
                p.part_number as sku,
                COUNT(*) as appearances,
                COUNT(DISTINCT sn.serial) as serial_count,
                STRING_AGG(DISTINCT sn.serial, ', ' ORDER BY sn.serial) as serials,
                MIN(p.usage_name) as sample_name,
                COUNT(DISTINCT CASE WHEN pd.id IS NOT NULL THEN pd.id END) as with_pricing
            FROM motorpartsdata_part p
            JOIN motorpartsdata_childtitle ct ON p.child_title_id = ct.id
            JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id
            JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
            LEFT JOIN motorpartsdata_pricingdata pd ON p.id = pd.part_number_id
            {where_clause}
            GROUP BY p.part_number
            ORDER BY appearances DESC, p.part_number
        """
        
        cursor.execute(query, params)
        skus = cursor.fetchall()
        
        print("\n" + "="*140)
        print("🔍 SKU DISTRIBUTION ANALYSIS")
        if serial_filter:
            print(f"Serial Filter: {serial_filter}")
        print("="*140)
        print(f"{'SKU':<20} {'Sample Name':<35} {'Count':<8} {'Serials':<8} {'Pricing':<8} {'Serial List':<50}")
        print("-" * 140)
        
        # Show top duplicated SKUs first
        duplicated = [sku for sku in skus if sku['appearances'] > 1]
        unique = [sku for sku in skus if sku['appearances'] == 1]
        
        if duplicated:
            print("🔸 DUPLICATED SKUs:")
            for sku in duplicated[:20]:  # Top 20 duplicated
                serials_display = sku['serials'][:45] + "..." if len(sku['serials']) > 45 else sku['serials']
                sample_name = (sku['sample_name'] or '')[:30] + "..." if len(sku['sample_name'] or '') > 30 else (sku['sample_name'] or '')
                pricing_status = "✓" if sku['with_pricing'] > 0 else "✗"
                print(f"{sku['sku']:<20} {sample_name:<35} {sku['appearances']:<8} {sku['serial_count']:<8} {pricing_status:<8} {serials_display}")
        
        print(f"\n📊 Summary:")
        print(f"   Total unique SKUs: {len(skus)}")
        print(f"   Duplicated SKUs: {len(duplicated)}")
        print(f"   Unique SKUs: {len(unique)}")
        if duplicated:
            total_duplicated_parts = sum(sku['appearances'] for sku in duplicated)
            total_with_pricing = sum(1 for sku in skus if sku['with_pricing'] > 0)
            print(f"   Total parts from duplicated SKUs: {total_duplicated_parts}")
            print(f"   SKUs with pricing data: {total_with_pricing}")
        
        cursor.close()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    parser = argparse.ArgumentParser(description='Oscar Database Reporting')
    parser.add_argument('--serial', help='Filter by specific serial number')
    parser.add_argument('--report', choices=['overview', 'categories', 'skus', 'all'], 
                       default='all', help='Type of report to generate')
    parser.add_argument('--output', help='Output file path (default: report.txt)')
    
    args = parser.parse_args()
    
    # Set up output
    output_file = args.output or 'report.txt'
    
    reporter = OscarReporter()
    
    try:
        if not reporter.connect_db():
            return 1
        
        # Redirect print to file
        import sys
        original_stdout = sys.stdout
        
        with open(output_file, 'w', encoding='utf-8') as f:
            sys.stdout = f
            
            print(f"OSCAR DATABASE COMPREHENSIVE REPORT")
            print(f"Generated on: {datetime.now()}")
            print("="*150)
            
            if args.report in ['overview', 'all']:
                reporter.get_serials_overview()
            
            if args.report in ['categories', 'all']:
                reporter.print_categories_report(args.serial)
            
            if args.report in ['skus', 'all']:
                reporter.get_sku_distribution(args.serial)
                
        sys.stdout = original_stdout
        print(f"✅ Report saved to: {output_file}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    finally:
        reporter.close()
    
    return 0

if __name__ == "__main__":
    exit(main())