#!/usr/bin/env python3
"""
Simple Product Creator - Skip category validation
Creates products without pre-validating categories
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import tempfile
from pathlib import Path
import sys
from tqdm import tqdm
import re
from datetime import datetime

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

class SimpleProductCreator:
    def __init__(self, consumer_key, consumer_secret, serial_filter=None, limit=None):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.serial_filter = serial_filter
        self.limit = limit
        self.conn = None
        self.importer = None
        self.temp_dir = None
        self.error_log = []
        
        # Statistics
        self.stats = {
            'skus_extracted': 0,
            'products_created': 0,
            'products_updated': 0,
            'errors': 0
        }
        
    def connect_db(self):
        """Connect to Oscar database"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            print("✓ Connected to Oscar database")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def setup_woocommerce(self):
        """Initialize WooCommerce importer"""
        try:
            self.importer = WooCommerceImporter(
                site_url=WORDPRESS_URL,
                consumer_key=self.consumer_key,
                consumer_secret=self.consumer_secret
            )
            print("✓ WooCommerce importer initialized")
            return True
        except Exception as e:
            print(f"❌ WooCommerce setup failed: {e}")
            return False
    
    def extract_products(self):
        """Extract unique SKUs from database"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Build WHERE clause
        where_clause = ""
        params = []
        
        if self.serial_filter:
            # Validate serial exists
            cursor.execute("SELECT COUNT(*) FROM motorpartsdata_serialnumber WHERE serial = %s", [self.serial_filter])
            result = cursor.fetchone()
            count = result['count'] if result else 0
            if count == 0:
                print(f"❌ Serial '{self.serial_filter}' not found in Oscar database")
                return {}
            
            where_clause = "WHERE sn.serial = %s"
            params.append(self.serial_filter)
        
        limit_clause = f"LIMIT {self.limit}" if self.limit else ""
        
        query = f"""
        SELECT DISTINCT 
            p.sku,
            p.model_name as title,
            p.price,
            p.upc as upc_code,
            d.diagram_name,
            s.svg_code,
            sn.serial
        FROM motorpartsdata_part p
        JOIN motorpartsdata_serialnumber sn ON p.serial_id = sn.id
        JOIN motorpartsdata_diagram d ON p.diagram_id = d.id  
        JOIN motorpartsdata_svgfile s ON d.svg_file_id = s.id
        {where_clause}
        ORDER BY p.sku
        {limit_clause}
        """
        
        print(f"🔍 Extracting products from database...")
        if self.serial_filter:
            print(f"   🎯 Serial filter: {self.serial_filter}")
        if self.limit:
            print(f"   📊 Limit: {self.limit}")
            
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        products_by_sku = {}
        for row in results:
            sku = row['sku']
            
            if sku not in products_by_sku:
                products_by_sku[sku] = {
                    'name': row['title'] or sku,
                    'sku': sku,
                    'price': float(row['price']) if row['price'] else 0.0,
                    'upc': row['upc_code'] or '',
                    'categories': [],
                    'svg_codes': [],
                    'serials': set()
                }
            
            # Add categories (diagram name and serial)
            categories = []
            if row['diagram_name']:
                # Clean diagram name - remove diagram codes like JE123A001
                cleaned_name = re.sub(r'^[A-Z]{2}\d+[A-Z]\d+ - ', '', row['diagram_name'])
                categories.append(cleaned_name.strip())
            
            if row['serial']:
                categories.append(row['serial'])
                products_by_sku[sku]['serials'].add(row['serial'])
                
            products_by_sku[sku]['categories'].extend(categories)
            
            # Add SVG code
            if row['svg_code']:
                products_by_sku[sku]['svg_codes'].append(row['svg_code'])
        
        # Remove duplicates from categories
        for product in products_by_sku.values():
            product['categories'] = list(set(product['categories']))
        
        print(f"✅ Extracted {len(products_by_sku)} unique products")
        self.stats['skus_extracted'] = len(products_by_sku)
        
        return products_by_sku
    
    def create_woocommerce_products(self, products_by_sku):
        """Create products in WooCommerce"""
        print(f"\n🚀 Creating {len(products_by_sku)} products in WooCommerce...")
        print("📝 Note: Categories will be created automatically as needed")
        
        self.temp_dir = tempfile.mkdtemp()
        temp_path = Path(self.temp_dir)
        
        woo_products = []
        
        for sku, product in tqdm(products_by_sku.items(), desc="Preparing products"):
            # Prepare images
            image_paths = []
            for i, svg_code in enumerate(product['svg_codes']):
                if svg_code.strip():
                    svg_filename = f"{sku}_{i+1}.svg"
                    svg_path = temp_path / svg_filename
                    
                    try:
                        with open(svg_path, 'w', encoding='utf-8') as f:
                            f.write(svg_code)
                        image_paths.append(str(svg_path))
                    except Exception as e:
                        print(f"⚠️ Failed to save SVG for {sku}: {e}")
            
            # Create WooCommerce product data
            woo_product = {
                'name': product['name'],
                'sku': product['sku'],
                'regular_price': str(product['price']),
                'categories': product['categories'],
                'meta_data': []
            }
            
            if product['upc']:
                woo_product['meta_data'].append({
                    'key': 'upc_code',
                    'value': product['upc']
                })
            
            if image_paths:
                woo_product['image_paths'] = image_paths
                
            woo_products.append(woo_product)
        
        # Import to WooCommerce
        try:
            results = self.importer.import_products(woo_products)
            
            # Update statistics
            for result in results:
                if result.get('created'):
                    self.stats['products_created'] += 1
                elif result.get('updated'):
                    self.stats['products_updated'] += 1
                if result.get('error'):
                    self.stats['errors'] += 1
                    self.error_log.append(result['error'])
                    
            return True
            
        except Exception as e:
            print(f"❌ Import failed: {e}")
            self.stats['errors'] += 1
            self.error_log.append(str(e))
            return False
    
    def run(self):
        """Run the complete process"""
        print("="*80)
        print("🏭 Simple Product Creator")
        print("="*80)
        
        # Setup
        if not self.connect_db():
            return False
            
        if not self.setup_woocommerce():
            return False
        
        # Extract products
        products = self.extract_products()
        if not products:
            print("❌ No products found")
            return False
        
        # Create products
        success = self.create_woocommerce_products(products)
        
        # Print final statistics
        print(f"\n📊 FINAL STATISTICS:")
        print(f"   SKUs extracted: {self.stats['skus_extracted']}")
        print(f"   Products created: {self.stats['products_created']}")
        print(f"   Products updated: {self.stats['products_updated']}")
        print(f"   Errors: {self.stats['errors']}")
        
        if self.error_log:
            print(f"\n❌ ERRORS:")
            for error in self.error_log[-10:]:  # Show last 10 errors
                print(f"   • {error}")
        
        # Cleanup
        if self.temp_dir:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            
        if self.conn:
            self.conn.close()
            
        return success

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Create products from Oscar database')
    parser.add_argument('--serial', help='Filter by serial number')
    parser.add_argument('--limit', type=int, help='Limit number of products')
    args = parser.parse_args()
    
    # Read credentials
    base_dir = Path(__file__).resolve().parent.parent
    keys_file = base_dir / 'keys.txt'
    
    consumer_key = None
    consumer_secret = None
    
    if keys_file.exists():
        with open(keys_file, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
            for i, line in enumerate(lines):
                if 'Consumer key' in line and i+1 < len(lines): 
                    consumer_key = lines[i+1]
                if 'Consumer secret' in line and i+1 < len(lines): 
                    consumer_secret = lines[i+1]
    
    if not consumer_key or not consumer_secret:
        print("❌ WooCommerce credentials not found in keys.txt")
        return 1
    
    # Create and run
    creator = SimpleProductCreator(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        serial_filter=args.serial,
        limit=args.limit
    )
    
    success = creator.run()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())