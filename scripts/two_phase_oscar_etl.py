#!/usr/bin/env python3
"""
Oscar → WooCommerce ETL Script (Two-Phase)
Phase 1: Create all categories from all serials first
Phase 2: Import unique SKUs with references to existing categories
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import tempfile
from pathlib import Path
from datetime import datetime
import sys
from tqdm import tqdm
import time

# Add parent directory to path for imports
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))
from config import WORDPRESS_URL
from scripts.import_to_woocommerce import WooCommerceImporter

# Database connection parameters
DB_CONFIG = {
    'dbname': 'parts_store',
    'user': 'postgres',
    'password': 'N0rwich!',
    'host': '80.95.207.42',
    'port': '5432'
}

class TwoPhaseOscarETL:
    def __init__(self, serial_filter=None, limit=None):
        self.serial_filter = serial_filter
        self.limit = limit
        self.conn = None
        self.temp_dir = Path(tempfile.mkdtemp())
        self.importer = None
        self.error_log = []
        print(f"Temp directory: {self.temp_dir}")
        
    def connect(self):
        """Connect to Oscar database"""
        try:
            if self.conn:
                self.conn.close()  # Close any existing connection
            self.conn = psycopg2.connect(**DB_CONFIG)
            print("✓ Connected to Oscar database")
            return True
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False
    
    def ensure_connection(self):
        """Ensure database connection is alive"""
        try:
            if not self.conn or self.conn.closed:
                return self.connect()
            # Test connection with simple query
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except:
            print("⚠ Connection lost, reconnecting...")
            return self.connect()
    
    def setup_woocommerce(self, checkpoint_dir=None):
        """Setup WooCommerce importer"""
        # Load WooCommerce credentials
        keys_file = base_dir / 'keys.txt'
        consumer_key = consumer_secret = None
        if keys_file.exists():
            with open(keys_file, 'r', encoding='utf-8') as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
                for i, line in enumerate(lines):
                    if 'Consumer key' in line and i+1 < len(lines): 
                        consumer_key = lines[i+1]
                    if 'Consumer secret' in line and i+1 < len(lines): 
                        consumer_secret = lines[i+1]
        
        if not consumer_key or not consumer_secret:
            raise Exception("WooCommerce credentials not found in keys.txt")
        
        # Setup checkpoint directory
        checkpoint_dir = base_dir / 'data' / (checkpoint_dir or 'checkpoints_two_phase')
        log_dir = base_dir / 'logs'
        
        # Create importer
        self.importer = WooCommerceImporter(
            WORDPRESS_URL, consumer_key, consumer_secret, 
            checkpoint_dir, log_dir
        )
        print("✓ WooCommerce importer initialized")
    
    def sanitize_category_name(self, name):
        """Sanitize category names for WooCommerce compatibility"""
        if not name:
            return "Uncategorized"
        
        # Remove diagram codes (JE123A001 - ) from category names
        import re
        name = re.sub(r'^[A-Z]{2}\d+[A-Z]?\d+\s*-\s*', '', name)
        
        # Replace problematic characters but keep full length
        sanitized = name.replace('&', 'and').replace('/', '-').replace('\\', '-')
        sanitized = sanitized.replace('(', '').replace(')', '').replace(',', '')
        
        # Clean up extra spaces and dashes
        sanitized = re.sub(r'\s+', ' ', sanitized)  # Multiple spaces -> single space
        sanitized = re.sub(r'-+', '-', sanitized)   # Multiple dashes -> single dash
        
        return sanitized.strip(' -')
    
    def extract_all_categories(self):
        """Phase 1: Extract all unique categories across all serials"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Build WHERE clause for serial filtering
        where_clause = ""
        params = []
        if self.serial_filter:
            where_clause = "WHERE sn.serial = %s"
            params.append(self.serial_filter)
        
        print(f"\n{'='*60}")
        print("Phase 1: Extracting Category Hierarchy")
        print(f"{'='*60}")
        
        # Get all unique category combinations
        query = f"""
            SELECT DISTINCT
                sn.vehicle_brand,
                sn.serial,
                pt.title as parent_category,
                ct.title as child_category
            FROM motorpartsdata_serialnumber sn
            JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
            JOIN motorpartsdata_childtitle ct ON ct.parent_id = pt.id
            {where_clause}
            ORDER BY sn.vehicle_brand, sn.serial, pt.title, ct.title
        """
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Build category hierarchy
        categories_to_create = {}  # {name: parent_id}
        
        # Level 1: Vehicle brands (top level)
        brands = set()
        for row in rows:
            brands.add(self.sanitize_category_name(row['vehicle_brand']))
        
        # Level 2: Serial numbers under brands
        serials = {}  # {serial: brand}
        for row in rows:
            brand = self.sanitize_category_name(row['vehicle_brand'])
            serial = self.sanitize_category_name(row['serial'])
            serials[serial] = brand
        
        # Level 3: Parent categories under serials
        parents = {}  # {parent: serial}
        for row in rows:
            serial = self.sanitize_category_name(row['serial'])
            parent = self.sanitize_category_name(row['parent_category'])
            parents[parent] = serial
        
        # Level 4: Child categories under parents
        children = {}  # {child: parent}
        for row in rows:
            parent = self.sanitize_category_name(row['parent_category'])
            child = self.sanitize_category_name(row['child_category'])
            children[child] = parent
        
        cursor.close()
        
        print(f"Found:")
        print(f"  Brands: {len(brands)}")
        print(f"  Serials: {len(serials)}")
        print(f"  Parent categories: {len(parents)}")
        print(f"  Child categories: {len(children)}")
        
        return {
            'brands': brands,
            'serials': serials,
            'parents': parents,
            'children': children
        }
    
    def create_category_hierarchy(self, categories):
        """Phase 1: Create all categories in WooCommerce"""
        print(f"\n{'='*60}")
        print("Phase 1: Creating Category Hierarchy in WooCommerce")
        print(f"{'='*60}")
        
        created_categories = {}  # {name: id}
        
        # Level 1: Create brands (top level)
        print("\nCreating brand categories...")
        for brand in tqdm(categories['brands'], desc="Brands"):
            try:
                cat_id = self.importer.get_or_create_category(brand, parent_id=0)
                if cat_id:
                    created_categories[brand] = cat_id
                    print(f"  ✓ {brand}: {cat_id}")
                else:
                    self.error_log.append(f"Failed to create brand: {brand}")
                    print(f"  ❌ Failed: {brand}")
                time.sleep(0.1)  # Rate limiting
            except Exception as e:
                error_msg = f"Error creating brand {brand}: {str(e)}"
                self.error_log.append(error_msg)
                print(f"  ❌ Error: {brand} - {str(e)}")
        
        # Level 2: Create serials under brands
        print("\nCreating serial categories...")
        for serial, brand in tqdm(categories['serials'].items(), desc="Serials"):
            try:
                brand_id = created_categories.get(brand, 0)
                cat_id = self.importer.get_or_create_category(serial, parent_id=brand_id)
                if cat_id:
                    created_categories[serial] = cat_id
                    print(f"  ✓ {serial} under {brand}: {cat_id}")
                else:
                    self.error_log.append(f"Failed to create serial: {serial}")
                    print(f"  ❌ Failed: {serial}")
                time.sleep(0.1)
            except Exception as e:
                error_msg = f"Error creating serial {serial}: {str(e)}"
                self.error_log.append(error_msg)
                print(f"  ❌ Error: {serial} - {str(e)}")
        
        # Level 3: Create parent categories under serials
        print("\nCreating parent categories...")
        for parent, serial in tqdm(categories['parents'].items(), desc="Parents"):
            try:
                serial_id = created_categories.get(serial, 0)
                cat_id = self.importer.get_or_create_category(parent, parent_id=serial_id)
                if cat_id:
                    created_categories[parent] = cat_id
                    print(f"  ✓ {parent} under {serial}: {cat_id}")
                else:
                    self.error_log.append(f"Failed to create parent: {parent}")
                    print(f"  ❌ Failed: {parent}")
                time.sleep(0.1)
            except Exception as e:
                error_msg = f"Error creating parent {parent}: {str(e)}"
                self.error_log.append(error_msg)
                print(f"  ❌ Error: {parent} - {str(e)}")
        
        # Level 4: Create child categories under parents
        print("\nCreating child categories...")
        for child, parent in tqdm(categories['children'].items(), desc="Children"):
            try:
                parent_id = created_categories.get(parent, 0)
                cat_id = self.importer.get_or_create_category(child, parent_id=parent_id)
                if cat_id:
                    created_categories[child] = cat_id
                    print(f"  ✓ {child} under {parent}: {cat_id}")
                else:
                    self.error_log.append(f"Failed to create child: {child}")
                    print(f"  ❌ Failed: {child}")
                time.sleep(0.1)
            except Exception as e:
                error_msg = f"Error creating child {child}: {str(e)}"
                self.error_log.append(error_msg)
                print(f"  ❌ Error: {child} - {str(e)}")
        
        return created_categories
    
    def extract_unique_skus(self):
        """Phase 2: Extract unique SKUs with all their data"""
        # Ensure connection is alive
        if not self.ensure_connection():
            raise Exception("Failed to establish database connection for Phase 2")
            
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        print(f"\n{'='*60}")
        print("Phase 2: Extracting Unique SKUs")
        print(f"{'='*60}")
        
        # Build WHERE clause for serial filtering
        where_clause = ""
        params = []
        if self.serial_filter:
            where_clause = "WHERE sn.serial = %s"
            params.append(self.serial_filter)
        
        # Get all parts with their relationships, grouped by SKU
        query = f"""
            SELECT 
                p.part_number as sku,
                p.usage_name,
                p.unit_qty,
                p.lr,
                p.call_out_order,
                ct.title as diagram_name,
                ct.svg_code,
                pt.title as parent_category,
                sn.serial,
                sn.vehicle_brand,
                pd.list_price,
                pd.stock_available,
                COUNT(*) OVER (PARTITION BY p.part_number) as sku_count
            FROM motorpartsdata_part p
            JOIN motorpartsdata_childtitle ct ON p.child_title_id = ct.id
            JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id
            JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
            LEFT JOIN motorpartsdata_pricingdata pd ON pd.part_number_id = p.id
            {where_clause}
            ORDER BY p.part_number, sn.serial, pt.title
        """
        
        if self.limit:
            query += f" LIMIT {self.limit * 5}"  # Get extra rows for complete SKUs
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Group by SKU
        products_by_sku = {}
        
        for row in rows:
            sku = row['sku']
            
            if sku not in products_by_sku:
                products_by_sku[sku] = {
                    'sku': sku,
                    'name': row['usage_name'],
                    'categories': set(),
                    'diagrams': set(),
                    'svg_codes': set(),
                    'serials': set(),
                    'quantity': row['unit_qty'],
                    'lr_field': row['lr'],
                    'callout': row['call_out_order'],
                    'price': row['list_price'],
                    'stock': row['stock_available'],
                    'sku_count': row['sku_count']
                }
            
            product = products_by_sku[sku]
            
            # Build category path using sanitized names
            brand = self.sanitize_category_name(row['vehicle_brand'])
            serial = self.sanitize_category_name(row['serial'])
            parent = self.sanitize_category_name(row['parent_category'])
            child = self.sanitize_category_name(row['diagram_name'])
            
            product['categories'].update([brand, serial, parent, child])
            product['diagrams'].add(row['diagram_name'])
            product['serials'].add(row['serial'])
            
            if row['svg_code']:
                product['svg_codes'].add(row['svg_code'])
            
            if not product['price'] and row['list_price']:
                product['price'] = row['list_price']
        
        # Convert sets to lists and apply limit
        for product in products_by_sku.values():
            product['categories'] = list(product['categories'])
            product['diagrams'] = list(product['diagrams'])
            product['serials'] = list(product['serials'])
            product['svg_codes'] = list(product['svg_codes'])
        
        cursor.close()
        
        if self.limit:
            limited_products = dict(list(products_by_sku.items())[:self.limit])
            return limited_products
        
        return products_by_sku
    
    def save_svg_file(self, svg_code, output_path):
        """Save SVG code directly to file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(svg_code)
            return True
        except Exception as e:
            self.error_log.append(f"SVG save error for {output_path}: {str(e)}")
            return False
    
    def create_products(self, products_by_sku):
        """Phase 2: Create products in WooCommerce"""
        print(f"\n{'='*60}")
        print(f"Phase 2: Creating {len(products_by_sku)} Products")
        print(f"{'='*60}")
        
        woo_products = []
        
        for sku, product in tqdm(products_by_sku.items(), desc="Preparing products"):
            # Prepare images
            image_paths = []
            for i, svg_code in enumerate(product['svg_codes']):
                if not svg_code.strip():
                    continue
                    
                sku_clean = product['sku'].replace('/', '_')
                filename = f"{sku_clean}_diagram_{i+1}.svg"
                image_path = self.temp_dir / filename
                
                if self.save_svg_file(svg_code, image_path):
                    image_paths.append(image_path)
            
            # Build description
            if len(product['diagrams']) > 1:
                description = f"Used in {len(product['diagrams'])} diagrams: {', '.join(product['diagrams'][:3])}"
                if len(product['diagrams']) > 3:
                    description += f" and {len(product['diagrams']) - 3} more"
            else:
                description = f"From diagram: {product['diagrams'][0] if product['diagrams'] else 'Unknown'}"
            
            if len(product['serials']) > 1:
                description += f" | Used in {len(product['serials'])} vehicle serials"
            
            woo_product = {
                'type': 'simple',
                'name': product['name'],
                'sku': product['sku'],
                'description': description,
                'categories': product['categories'],
                'orientation': None,
                'callout': str(product['callout']) if product['callout'] else '',
                'quantity': str(product['quantity']) if product['quantity'] else '1',
                'lr_field': product['lr_field'] or '',
                'remark': f"Found in {product['sku_count']} diagram locations",
                'price': float(product['price']) if product['price'] else None,
                'stock_status': 'instock' if product['stock'] else 'outofstock',
                'image_paths': image_paths,
                'diagram_files': product['diagrams'],
                'diagram_file': product['diagrams'][0] if product['diagrams'] else 'oscar_database.svg',
                'serials_used': product['serials']
            }
            
            woo_products.append(woo_product)
        
        # Import to WooCommerce
        print(f"\nStarting import of {len(woo_products)} products...")
        try:
            self.importer.import_products(woo_products)
            self.importer.save_checkpoint()
            return True
        except Exception as e:
            error_msg = f"Product import failed: {str(e)}"
            self.error_log.append(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def print_error_summary(self):
        """Print all errors encountered"""
        if self.error_log:
            print(f"\n{'='*60}")
            print(f"ERROR SUMMARY ({len(self.error_log)} errors)")
            print(f"{'='*60}")
            for i, error in enumerate(self.error_log, 1):
                print(f"{i:3d}. {error}")
        else:
            print("\n✅ No errors encountered!")
    
    def close(self):
        """Cleanup"""
        if self.conn:
            self.conn.close()
    
    def run_two_phase_etl(self, checkpoint_dir=None):
        """Run the complete two-phase ETL process"""
        if not self.connect():
            return False
        
        try:print("Starting Phase 1: Category Creation")
            categories = self.extract_all_categories()
            created_categories = self.create_category_hierarchy(categories)
            
            # Reconnect for Phase 2 (fresh connection)
            print("\n🔄 Reconnecting to database for Phase 2...")
            if not self.ensure_connection():
                raise Exception("Failed to reconnect for Phase 2")
            
            # Phase 2: Products
            print("Starting Phase 2: Product Creation")
            products_by_sku = self.extract_unique_skus()
            success = self.create_products(products_by_sku)
            
            # Print summaries
            self.importer.print_summary()
            self.print_error_summary()
            
            return success
            
        except Exception as e:
            error_msg = f"ETL process failed: {str(e)}"
            self.error_log.append(error_msg)
            print(f"❌ {error_msg}")
            return Falseself.importer.print_summary()
            self.print_error_summary()
            
            return success
            
        finally:
            self.close()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Two-phase Oscar to WooCommerce ETL')
    parser.add_argument('--serial', help='Filter by specific serial number')
    parser.add_argument('--limit', type=int, help='Limit number of unique SKUs to process')
    parser.add_argument('--checkpoint-dir', help='Checkpoint directory for import resumability')
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print("Two-Phase Oscar → WooCommerce ETL")
    print(f"{'='*60}")
    
    etl = TwoPhaseOscarETL(serial_filter=args.serial, limit=args.limit)
    success = etl.run_two_phase_etl(args.checkpoint_dir)
    
    if success:
        print("\n✅ Two-phase ETL completed successfully!")
        return 0
    else:
        print("\n❌ ETL completed with errors")
        return 1

if __name__ == '__main__':
    exit(main())