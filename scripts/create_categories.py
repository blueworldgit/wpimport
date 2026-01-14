#!/usr/bin/env python3
"""
Oscar Category Creator
Extracts all categories from Oscar database and creates them in WooCommerce
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
import sys
from tqdm import tqdm
import time
import re

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

class CategoryCreator:
    def __init__(self, serial_filter=None):
        self.serial_filter = serial_filter
        self.conn = None
        self.importer = None
        self.error_log = []
        
    def connect(self):
        """Connect to Oscar database"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            print("✓ Connected to Oscar database")
            return True
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False
    
    def setup_woocommerce(self):
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
        checkpoint_dir = base_dir / 'data' / 'checkpoints_categories'
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
        name = re.sub(r'^[A-Z]{2}\d+[A-Z]?\d+\s*-\s*', '', name)
        
        # Replace problematic characters but keep full length
        sanitized = name.replace('&', 'and').replace('/', '-').replace('\\', '-')
        sanitized = sanitized.replace('(', '').replace(')', '').replace(',', '')
        
        # Clean up extra spaces and dashes
        sanitized = re.sub(r'\s+', ' ', sanitized)
        sanitized = re.sub(r'-+', '-', sanitized)
        
        return sanitized.strip(' -')
    
    def extract_category_hierarchy(self):
        """Extract all unique categories from database"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Build WHERE clause for serial filtering
        where_clause = ""
        params = []
        if self.serial_filter:
            where_clause = "WHERE sn.serial = %s"
            params.append(self.serial_filter)
        
        print(f"Extracting category hierarchy...")
        if self.serial_filter:
            print(f"  Filtering by serial: {self.serial_filter}")
        
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
        brands = set()
        serials = {}  # {serial: brand}
        parents = {}  # {parent: serial}
        children = {}  # {child: parent}
        
        for row in rows:
            brand = self.sanitize_category_name(row['vehicle_brand'])
            serial = self.sanitize_category_name(row['serial'])
            parent = self.sanitize_category_name(row['parent_category'])
            child = self.sanitize_category_name(row['child_category'])
            
            brands.add(brand)
            serials[serial] = brand
            parents[parent] = serial
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
    
    def create_categories(self, categories):
        """Create all categories in WooCommerce"""
        print(f"\n{'='*60}")
        print("Creating Category Hierarchy in WooCommerce")
        print(f"{'='*60}")
        
        created_categories = {}  # {name: id}
        
        # Level 1: Create brands (top level)
        print("\nLevel 1: Brand categories...")
        for brand in tqdm(categories['brands'], desc="Brands"):
            try:
                cat_id = self.importer.get_or_create_category(brand, parent_id=0)
                if cat_id:
                    created_categories[brand] = cat_id
                else:
                    self.error_log.append(f"Failed to create brand: {brand}")
                time.sleep(0.1)
            except Exception as e:
                error_msg = f"Error creating brand {brand}: {str(e)}"
                self.error_log.append(error_msg)
        
        # Level 2: Create serials under brands
        print("Level 2: Serial categories...")
        for serial, brand in tqdm(categories['serials'].items(), desc="Serials"):
            try:
                brand_id = created_categories.get(brand, 0)
                cat_id = self.importer.get_or_create_category(serial, parent_id=brand_id)
                if cat_id:
                    created_categories[serial] = cat_id
                else:
                    self.error_log.append(f"Failed to create serial: {serial}")
                time.sleep(0.1)
            except Exception as e:
                error_msg = f"Error creating serial {serial}: {str(e)}"
                self.error_log.append(error_msg)
        
        # Level 3: Create parent categories under serials
        print("Level 3: Parent categories...")
        for parent, serial in tqdm(categories['parents'].items(), desc="Parents"):
            try:
                serial_id = created_categories.get(serial, 0)
                cat_id = self.importer.get_or_create_category(parent, parent_id=serial_id)
                if cat_id:
                    created_categories[parent] = cat_id
                else:
                    self.error_log.append(f"Failed to create parent: {parent}")
                time.sleep(0.1)
            except Exception as e:
                error_msg = f"Error creating parent {parent}: {str(e)}"
                self.error_log.append(error_msg)
        
        # Level 4: Create child categories under parents
        print("Level 4: Child categories...")
        for child, parent in tqdm(categories['children'].items(), desc="Children"):
            try:
                parent_id = created_categories.get(parent, 0)
                cat_id = self.importer.get_or_create_category(child, parent_id=parent_id)
                if cat_id:
                    created_categories[child] = cat_id
                else:
                    self.error_log.append(f"Failed to create child: {child}")
                time.sleep(0.1)
            except Exception as e:
                error_msg = f"Error creating child {child}: {str(e)}"
                self.error_log.append(error_msg)
        
        return created_categories
    
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
    
    def run(self):
        """Run category creation"""
        if not self.connect():
            return False
        
        try:
            self.setup_woocommerce()
            categories = self.extract_category_hierarchy()
            created_categories = self.create_categories(categories)
            
            print(f"\n{'='*60}")
            print("CATEGORY CREATION SUMMARY")
            print(f"{'='*60}")
            print(f"Categories created: {len(created_categories)}")
            print(f"Errors: {len(self.error_log)}")
            
            self.print_error_summary()
            
            return len(self.error_log) == 0
            
        finally:
            self.close()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create categories from Oscar database in WooCommerce')
    parser.add_argument('--serial', help='Filter by specific serial number')
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print("Oscar Category Creator")
    print(f"{'='*60}")
    
    creator = CategoryCreator(serial_filter=args.serial)
    success = creator.run()
    
    if success:
        print("\n✅ Category creation completed successfully!")
        return 0
    else:
        print("\n❌ Category creation completed with errors")
        return 1

if __name__ == '__main__':
    exit(main())