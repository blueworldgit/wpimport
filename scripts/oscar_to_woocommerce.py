#!/usr/bin/env python3
"""
Oscar → WooCommerce ETL Script
Extracts products from Oscar PostgreSQL database and imports to WooCommerce
Handles SKU deduplication and merging automatically
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import tempfile
from pathlib import Path
from datetime import datetime
import sys
from tqdm import tqdm

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

class OscarExtractor:
    def __init__(self, serial_filter=None, limit=None):
        self.serial_filter = serial_filter
        self.limit = limit
        self.conn = None
        self.temp_dir = Path(tempfile.mkdtemp())
        print(f"Temp directory: {self.temp_dir}")
        
    def connect(self):
        """Connect to Oscar database"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            print("✓ Connected to Oscar database")
            return True
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False
    
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
    
    def extract_products_by_sku(self):
        """
        Extract products grouped by SKU to handle duplicates properly
        Returns dict mapping SKU -> product data with merged categories/diagrams
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
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
            query += f" LIMIT {self.limit * 5}"  # Get extra rows to ensure we have complete SKUs
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Group by SKU and merge data
        products_by_sku = {}
        
        for row in rows:
            sku = row['sku']
            
            if sku not in products_by_sku:
                # Create base product
                products_by_sku[sku] = {
                    'type': 'simple',
                    'name': row['usage_name'],
                    'sku': sku,
                    'orientation': None,
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
            
            # Merge categories (build hierarchy: Brand > Serial > Parent Category > Diagram)
            # Sanitize category names for WooCommerce
            brand = self.sanitize_category_name(row['vehicle_brand'])
            serial = self.sanitize_category_name(row['serial'])
            parent = self.sanitize_category_name(row['parent_category'])
            diagram = self.sanitize_category_name(row['diagram_name'])
            
            product['categories'].add(brand)        # Top level: Maxus
            product['categories'].add(serial)       # Serial level  
            product['categories'].add(parent)       # Parent category
            product['categories'].add(diagram)      # Diagram name
            
            # Track diagrams and serials for metadata
            product['diagrams'].add(row['diagram_name'])
            product['serials'].add(row['serial'])
            
            # Store SVG code (usually same across instances, but collect all)
            if row['svg_code']:
                product['svg_codes'].add(row['svg_code'])
            
            # Use first non-null price found
            if not product['price'] and row['list_price']:
                product['price'] = row['list_price']
        
        # Convert sets to lists and clean up
        for sku, product in products_by_sku.items():
            product['categories'] = list(product['categories'])
            product['diagrams'] = list(product['diagrams'])
            product['serials'] = list(product['serials'])
            product['svg_codes'] = list(product['svg_codes'])
            
            # Sort categories for consistent hierarchy
            categories = product['categories']
            brand = [c for c in categories if c in ['Maxus', 'Peugeot', 'Renault']]
            serials = [c for c in categories if len(c) == 17 and c.startswith('LS')]
            parents = [c for c in categories if c not in brand + serials and ' - ' not in c]
            diagrams = [c for c in categories if ' - ' in c or c not in brand + serials + parents]
            
            product['categories'] = brand + serials + parents + diagrams
            
            # Generate description with diagram info
            if len(product['diagrams']) > 1:
                product['description'] = f"Used in {len(product['diagrams'])} diagrams: {', '.join(product['diagrams'][:3])}"
                if len(product['diagrams']) > 3:
                    product['description'] += f" and {len(product['diagrams']) - 3} more"
            else:
                product['description'] = f"From diagram: {product['diagrams'][0] if product['diagrams'] else 'Unknown'}"
            
            if len(product['serials']) > 1:
                product['description'] += f" | Used in {len(product['serials'])} vehicle serials"
        
        cursor.close()
        
        # Apply limit after grouping if specified
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
            print(f"    SVG save error: {e}")
            return False
    
    def prepare_product_images(self, product):
        """Save SVG codes directly as SVG files and return image paths"""
        image_paths = []
        
        for i, svg_code in enumerate(product['svg_codes']):
            if not svg_code.strip():
                continue
                
            # Generate filename
            sku = product['sku'].replace('/', '_')
            filename = f"{sku}_diagram_{i+1}.svg"
            image_path = self.temp_dir / filename
            
            # Save SVG directly
            if self.save_svg_file(svg_code, image_path):
                image_paths.append(image_path)
            
        return image_paths
    
    def format_for_woocommerce(self, products_by_sku):
        """Format products for WooCommerce import"""
        woo_products = []
        
        print(f"\n{'='*60}")
        print(f"Converting {len(products_by_sku)} unique SKUs to WooCommerce format")
        print(f"{'='*60}")
        
        for sku, product in tqdm(products_by_sku.items(), desc="Preparing products"):
            # Prepare images
            image_paths = self.prepare_product_images(product)
            
            # Build WooCommerce product
            woo_product = {
                'type': 'simple',
                'diagram_file': product['diagrams'][0] if product['diagrams'] else 'oscar_database.svg',  # Add required field
                'name': product['name'],
                'sku': product['sku'],
                'description': product['description'],
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
                'serials_used': product['serials']
            }
            
            woo_products.append(woo_product)
        
        return woo_products
    
    def close(self):
        """Close database connection and cleanup"""
        if self.conn:
            self.conn.close()
        # Note: temp_dir cleanup handled by WooCommerce importer
    
    def extract_and_format(self):
        """Main extraction method"""
        if not self.connect():
            return None
        
        try:
            # Extract products grouped by SKU
            print(f"\nExtracting products from Oscar database...")
            if self.serial_filter:
                print(f"  Filtering by serial: {self.serial_filter}")
            if self.limit:
                print(f"  Limiting to first: {self.limit} unique SKUs")
            
            products_by_sku = self.extract_products_by_sku()
            print(f"  Found: {len(products_by_sku)} unique SKUs")
            
            # Show duplication stats
            total_instances = sum(p['sku_count'] for p in products_by_sku.values())
            duplicates = total_instances - len(products_by_sku)
            if duplicates > 0:
                print(f"  Merged: {duplicates} duplicate SKU instances")
            
            # Format for WooCommerce
            woo_products = self.format_for_woocommerce(products_by_sku)
            
            return {
                'serial_number': self.serial_filter or 'multiple',
                'vehicle_brand': 'Maxus',
                'extraction_date': datetime.now().isoformat(),
                'source': 'oscar_database',
                'products': woo_products,
                'stats': {
                    'total_sku_instances': total_instances,
                    'unique_skus': len(products_by_sku),
                    'duplicates_merged': duplicates,
                    'products_with_images': len([p for p in woo_products if p['image_paths']]),
                    'products_with_pricing': len([p for p in woo_products if p['price']])
                }
            }
        
        finally:
            self.close()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract products from Oscar database and import to WooCommerce')
    parser.add_argument('--serial', help='Filter by specific serial number')
    parser.add_argument('--limit', type=int, help='Limit number of unique SKUs to process')
    parser.add_argument('--extract-only', action='store_true', help='Only extract and show data, do not import')
    parser.add_argument('--checkpoint-dir', help='Checkpoint directory for import resumability')
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print("Oscar → WooCommerce ETL")
    print(f"{'='*60}")
    
    # Extract from Oscar
    extractor = OscarExtractor(serial_filter=args.serial, limit=args.limit)
    data = extractor.extract_and_format()
    
    if not data:
        print("❌ Extraction failed")
        return 1
    
    print(f"\n{'='*60}")
    print("Extraction Summary")
    print(f"{'='*60}")
    stats = data['stats']
    print(f"Total SKU instances: {stats['total_sku_instances']}")
    print(f"Unique SKUs:         {stats['unique_skus']}")
    print(f"Duplicates merged:   {stats['duplicates_merged']}")
    print(f"Products with images: {stats['products_with_images']}")
    print(f"Products with pricing: {stats['products_with_pricing']}")
    
    if args.extract_only:
        # Show sample products
        print(f"\nSample products:")
        for i, product in enumerate(data['products'][:5]):
            print(f"  {i+1}. {product['sku']}: {product['name']}")
            print(f"     Categories: {' > '.join(product['categories'][:4])}")
            print(f"     Images: {len(product['image_paths'])}, Price: £{product['price'] or 'N/A'}")
        print("✓ Extraction complete (import skipped)")
        return 0
    
    # Import to WooCommerce
    try:
        print(f"\n{'='*60}")
        print("Importing to WooCommerce")
        print(f"{'='*60}")
        
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
            print("❌ WooCommerce credentials not found in keys.txt")
            return 1
        
        # Setup checkpoint directory
        checkpoint_dir = base_dir / 'data' / (args.checkpoint_dir or 'checkpoints_oscar')
        log_dir = base_dir / 'logs'
        
        # Import products
        importer = WooCommerceImporter(
            WORDPRESS_URL, consumer_key, consumer_secret, 
            checkpoint_dir, log_dir
        )
        
        print(f"Starting import of {len(data['products'])} products...")
        importer.import_products(data['products'])
        importer.save_checkpoint()
        importer.print_summary()
        
        print("\n✅ Oscar → WooCommerce ETL complete!")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())