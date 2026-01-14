#!/usr/bin/env python3
"""
Oscar Product Creator  
Extracts unique SKUs from Oscar database and creates products in WooCommerce
Assumes categories already exist from create_categories.py
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import tempfile
from pathlib import Path
import sys
import signal
import json
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

class ProductCreator:
    def __init__(self, serial_filter=None, limit=None, checkpoint_dir=None):
        self.serial_filter = serial_filter
        self.limit = limit
        self.conn = None
        self.importer = None
        self.temp_dir = Path(tempfile.mkdtemp())
        self.error_log = []
        self.category_map = {}  # Track category name -> ID mapping
        self.interrupted = False
        
        # Setup checkpoint directory
        self.checkpoint_dir = base_dir / 'data' / (checkpoint_dir or 'checkpoints_products')
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.checkpoint_dir / 'product_creator_checkpoint.json'
        
        self.stats = {
            'extracted_skus': 0,
            'created_products': 0,
            'updated_products': 0,
            'skipped_products': 0,
            'category_resolutions': 0,
            'missing_categories': 0,
            'errors': 0
        }
        
        # Setup interrupt handler
        signal.signal(signal.SIGINT, self._signal_handler)
        
        print(f"Temp directory: {self.temp_dir}")
        print(f"Checkpoint directory: {self.checkpoint_dir}")
        if self.serial_filter:
            print(f"Serial filter: {self.serial_filter}")
        
    def _signal_handler(self, signum, frame):
        """Handle keyboard interrupt gracefully"""
        print(f"\n\n⚠️  Keyboard interrupt received! Saving progress...")
        self.interrupted = True
        self.save_checkpoint()
        print(f"✅ Progress saved to: {self.checkpoint_file}")
        print(f"🔄 Run the script again with the same parameters to resume")
        sys.exit(0)
    
    def save_checkpoint(self):
        """Save current progress to checkpoint file"""
        try:
            checkpoint_data = {
                'serial_filter': self.serial_filter,
                'limit': self.limit,
                'stats': self.stats,
                'error_log': self.error_log,
                'category_map': self.category_map,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2)
            return True
        except Exception as e:
            print(f"⚠️  Failed to save checkpoint: {e}")
            return False
    
    def load_checkpoint(self):
        """Load previous progress from checkpoint file"""
        if not self.checkpoint_file.exists():
            return None
            
        try:
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            # Validate checkpoint matches current parameters
            if (checkpoint_data.get('serial_filter') != self.serial_filter or 
                checkpoint_data.get('limit') != self.limit):
                print(f"⚠️  Checkpoint found but parameters don't match:")
                print(f"   Checkpoint: serial={checkpoint_data.get('serial_filter')}, limit={checkpoint_data.get('limit')}")
                print(f"   Current:    serial={self.serial_filter}, limit={self.limit}")
                print(f"   Starting fresh...")
                return None
                
            print(f"📂 Found checkpoint from {checkpoint_data.get('timestamp')}")
            return checkpoint_data
            
        except Exception as e:
            print(f"⚠️  Failed to load checkpoint: {e}")
            return None
    
    def clear_checkpoint(self):
        """Clear checkpoint file after successful completion"""
        try:
            if self.checkpoint_file.exists():
                self.checkpoint_file.unlink()
                print(f"🗑️  Checkpoint cleared")
        except Exception as e:
            print(f"⚠️  Failed to clear checkpoint: {e}")
    
    def connect(self):
        """Connect to Oscar database"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            print("✓ Connected to Oscar database")
            return True
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False
    
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
        checkpoint_dir = base_dir / 'data' / (checkpoint_dir or 'checkpoints_products')
        log_dir = base_dir / 'logs'
        
        # Create importer
        self.importer = WooCommerceImporter(
            WORDPRESS_URL, consumer_key, consumer_secret, 
            checkpoint_dir, log_dir
        )
        
        # Pass pre-validated category mappings to avoid redundant API calls
        if hasattr(self, 'category_map') and self.category_map:
            self.importer.set_category_mappings(self.category_map)
            
        print("✓ WooCommerce importer initialized")
    
    def sanitize_category_name(self, name):
        """Sanitize category names for WooCommerce compatibility"""
        if not name:
            return "Uncategorized"
        
        # Remove diagram codes (JE123A001 - ) from category names
        name = re.sub(r'^[A-Z]{2}\d+[A-Z]?\d+\s*-\s*', '', name)
        
        # Handle special characters that cause issues
        sanitized = name.replace('、', '-')  # Japanese comma
        sanitized = sanitized.replace('，', '-')  # Chinese comma  
        sanitized = sanitized.replace('＆', 'and')  # Full-width ampersand
        sanitized = sanitized.replace('&', 'and').replace('/', '-').replace('\\', '-')
        sanitized = sanitized.replace('(', '').replace(')', '').replace(',', '')
        sanitized = sanitized.replace('：', '-').replace(':', '-')
        
        # Clean up extra spaces and dashes
        sanitized = re.sub(r'\s+', ' ', sanitized)
        sanitized = re.sub(r'-+', '-', sanitized)
        
        return sanitized.strip(' -')
    
    def normalize_category_name(self, name):
        """Strip punctuation and normalize for comparison"""
        import string
        import unicodedata
        
        # Convert to lowercase
        normalized = name.lower()
        
        # Remove all punctuation (including Unicode punctuation like Japanese comma)
        # This handles both ASCII and Unicode punctuation
        normalized = ''.join(char for char in normalized 
                           if unicodedata.category(char)[0] != 'P')
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def validate_category_exists(self, category_name):
        """Check if category exists in WooCommerce and return its ID"""
        if category_name in self.category_map:
            return self.category_map[category_name]
        
        try:
            # Search for category by name with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Extract key words for search (WooCommerce search doesn't work well with full sanitized names)
                    search_words = category_name.replace('-', ' ').replace('、', ' ').split()
                    
                    # Smart search strategy: for diagram codes (starting with letters+numbers), use just the code
                    if search_words and re.match(r'^[A-Z]+\d+', search_words[0]):
                        search_term = search_words[0]  # Just the diagram code: "JE11CQ001"
                    else:
                        search_term = ' '.join(search_words[:2])  # Use first 2 words for other categories
                    
                    print(f"   🔍 Searching for category: '{category_name}'")
                    print(f"       Search term: '{search_term}'")
                    print(f"       Normalized target: '{self.normalize_category_name(category_name)}'")
                    
                    response = self.importer.wcapi.get('products/categories', params={
                        'search': search_term,
                        'per_page': 100
                    })
                    
                    if response.status_code == 200:
                        categories = response.json()
                        print(f"       API returned {len(categories)} categories")
                        normalized_search = self.normalize_category_name(category_name)
                        
                        for cat in categories:
                            # Compare normalized versions (no punctuation, lowercase)
                            normalized_existing = self.normalize_category_name(cat['name'])
                            print(f"       - Checking ID {cat['id']}: '{cat['name']}' (normalized: '{normalized_existing}')")
                            if normalized_existing == normalized_search:
                                print(f"   ✓ Found category match: '{cat['name']}' (ID: {cat['id']}) → '{category_name}'")
                                self.category_map[category_name] = cat['id']
                                self.stats['category_resolutions'] += 1
                                return cat['id']
                        
                        print(f"   ❌ No exact match found after checking {len(categories)} categories")
                        break  # Found response but no matching category
                    else:
                        print(f"⚠️  API error for category '{category_name}': {response.status_code}")
                        if attempt < max_retries - 1:
                            print(f"   Retrying... (attempt {attempt + 2}/{max_retries})")
                            continue
                        break
                except (ConnectionError, TimeoutError, Exception) as e:
                    if attempt < max_retries - 1:
                        print(f"⚠️  Connection error for category '{category_name}': {type(e).__name__}: {e}")
                        print(f"   Retrying... (attempt {attempt + 2}/{max_retries})")
                        import time
                        time.sleep(2)  # Wait 2 seconds before retry
                        continue
                    else:
                        print(f"❌ Failed to validate category '{category_name}' after {max_retries} attempts: {type(e).__name__}: {e}")
                        self.error_log.append(f"API error validating category '{category_name}': {e}")
                        return None
            
            # Category not found
            self.error_log.append(f"Category '{category_name}' not found in WooCommerce")
            return None
            
        except Exception as e:
            error_msg = f"Error validating category '{category_name}': {str(e)}"
            self.error_log.append(error_msg)
            print(f"⚠ {error_msg}")
            return None
    
    def extract_unique_skus(self, checkpoint_data=None):
        """Extract unique SKUs with all their data"""
        
        # Check if we can resume from checkpoint
        if checkpoint_data and 'products_by_sku' in checkpoint_data:
            print(f"\n{'='*60}")
            print("Resuming from checkpoint - SKU extraction already completed")
            print(f"{'='*60}")
            products_by_sku = checkpoint_data['products_by_sku']
            self.stats.update(checkpoint_data.get('stats', {}))
            self.error_log.extend(checkpoint_data.get('error_log', []))
            self.category_map.update(checkpoint_data.get('category_map', {}))
            print(f"📦 Loaded {len(products_by_sku)} unique SKUs from checkpoint")
            return products_by_sku
        
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        print(f"\n{'='*60}")
        print("Extracting unique SKUs from Oscar database...")
        print(f"{'='*60}")
        if self.serial_filter:
            print(f"  🎯 Filtering by serial: {self.serial_filter}")
        else:
            print(f"  🌐 Processing ALL serials")
        if self.limit:
            print(f"  📊 Limiting to first: {self.limit} unique SKUs")
        
        # Validate serial exists if filtering
        if self.serial_filter:
            cursor.execute("SELECT COUNT(*) FROM motorpartsdata_serialnumber WHERE serial = %s", [self.serial_filter])
            result = cursor.fetchone()
            count = result['count'] if result else 0
            if count == 0:
                error_msg = f"Serial '{self.serial_filter}' not found in Oscar database"
                self.error_log.append(error_msg)
                print(f"❌ {error_msg}")
                return {}
        
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
            query += f" LIMIT {self.limit * 10}"  # Get extra rows for complete SKUs
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        print(f"  📦 Raw query returned: {len(rows)} part records")
        
        # Group by SKU
        products_by_sku = {}
        
        print(f"  🔄 Processing and grouping by SKU...")
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
        
        # Calculate statistics
        total_instances = sum(p['sku_count'] for p in products_by_sku.values())
        duplicates_merged = total_instances - len(products_by_sku)
        
        # Apply limit if specified
        if self.limit:
            original_count = len(products_by_sku)
            limited_products = dict(list(products_by_sku.items())[:self.limit])
            print(f"  ✂️ Limited from {original_count} to {len(limited_products)} unique SKUs")
            products_by_sku = limited_products
            total_instances = sum(p['sku_count'] for p in products_by_sku.values())
            duplicates_merged = total_instances - len(products_by_sku)
        
        self.stats['extracted_skus'] = len(products_by_sku)
        
        print(f"\n  📊 EXTRACTION SUMMARY:")
        print(f"      Unique SKUs: {len(products_by_sku)}")
        print(f"      Total part instances: {total_instances}")
        print(f"      Duplicates merged: {duplicates_merged}")
        if self.serial_filter:
            serials_found = set()
            for p in products_by_sku.values():
                serials_found.update(p['serials'])
            print(f"      Serial(s) involved: {', '.join(sorted(serials_found))}")
        print(f"\n")
        
        # Save checkpoint after extraction
        print(f"💾 Saving extraction checkpoint...")
        checkpoint_data = {
            'serial_filter': self.serial_filter,
            'limit': self.limit,
            'stats': self.stats,
            'error_log': self.error_log,
            'category_map': self.category_map,
            'products_by_sku': products_by_sku,
            'timestamp': datetime.now().isoformat(),
            'phase': 'extraction_complete'
        }
        
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2)
        print(f"✅ Checkpoint saved")
        
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
        """Create products in WooCommerce"""
        print(f"\n{'='*60}")
        print(f"Creating {len(products_by_sku)} Products in WooCommerce")
        print(f"{'='*60}")
        
        # Validate all categories exist before creating products
        print("🔍 Validating all categories exist in WooCommerce...")
        all_categories = set()
        for product in products_by_sku.values():
            all_categories.update(product['categories'])
        print(f"📋 Found {len(all_categories)} unique categories to validate")
        
        # Validate each category
        missing_categories = set()
        for category in all_categories:
            if not self.validate_category_exists(category):
                missing_categories.add(category)
                
        if missing_categories:
            print(f"❌ Found {len(missing_categories)} missing categories:")
            for cat in sorted(missing_categories):
                print(f"   • {cat}")
            print(f"\n⚠️  Products using missing categories will be skipped")
        else:
            # Pass validated category mappings to importer to avoid redundant creation attempts
            self.importer.set_category_mappings(self.category_map)
            print(f"✅ All categories validated - mappings passed to importer")
        
        woo_products = []
        skipped_products = []
        
        print("Preparing product data...")
        processed_count = 0
        for sku, product in tqdm(products_by_sku.items(), desc="Preparing products"):
            
            # Check for interrupt
            if self.interrupted:
                print(f"\n⚠️  Interrupted during product preparation")
                break
            
            # Check if product has any missing categories
            product_missing_categories = [cat for cat in product['categories'] if cat in missing_categories]
            if product_missing_categories:
                skip_reason = f"Missing categories: {', '.join(product_missing_categories)}"
                skipped_products.append({
                    'sku': sku,
                    'name': product['name'],
                    'reason': skip_reason
                })
                self.error_log.append(f"Skipped product {sku} ({product['name']}): {skip_reason}")
                continue
            
            processed_count += 1
            
            # Save checkpoint every 50 products
            if processed_count % 50 == 0:
                self.save_checkpoint()
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
            
            # Use only existing categories (already validated above)
            validated_categories = product['categories']
            
            woo_product = {
                'type': 'simple',
                'name': product['name'],
                'sku': product['sku'],
                'description': description,
                'categories': validated_categories,
                'orientation': None,
                'callout': str(product['callout']) if product['callout'] else '',
                'quantity': str(product['quantity']) if product['quantity'] else '1',
                'lr_field': product['lr_field'] or '',
                'remark': f"Found in {product['sku_count']} diagram locations across {len(product['serials'])} serial(s)",
                'price': float(product['price']) if product['price'] else None,
                'stock_status': 'instock' if product['stock'] else 'outofstock',
                'image_paths': image_paths,
                'diagram_files': product['diagrams'],
                'diagram_file': product['diagrams'][0] if product['diagrams'] else 'oscar_database.svg',
                'serials_used': product['serials'],
                'oscar_data': {
                    'extracted_from': 'oscar_database',
                    'serial_filter': self.serial_filter,
                    'total_instances': product['sku_count'],
                    'extraction_date': datetime.now().isoformat()
                }
            }
            
            woo_products.append(woo_product)
        
        # Report skipped products
        if skipped_products:
            print(f"\n⚠️  Skipped {len(skipped_products)} products due to missing categories:")
            for skipped in skipped_products[:5]:  # Show first 5
                print(f"   • {skipped['sku']} - {skipped['reason']}")
            if len(skipped_products) > 5:
                print(f"   ... and {len(skipped_products) - 5} more (see error log for full list)")
        
        # Import to WooCommerce
        print(f"\n🚀 Starting import of {len(woo_products)} products to WooCommerce...")
        print(f"📝 Note: WooCommerce importer will:")
        print(f"   • Check for existing products by SKU")
        print(f"   • Update existing products with new categories/data")
        print(f"   • Create new products if SKU doesn't exist")
        print(f"   • Only assign existing categories (no new categories will be created)")
        
        try:
            # Check for interrupt before starting import
            if self.interrupted:
                print(f"\n⚠️  Import interrupted before starting")
                return False
                
            initial_created = self.importer.stats.get('products_created', 0)
            initial_updated = self.importer.stats.get('products_updated', 0)
            
            self.importer.import_products(woo_products)
            self.importer.save_checkpoint()
            
            # Update our stats
            self.stats['created_products'] = self.importer.stats.get('products_created', 0) - initial_created
            self.stats['updated_products'] = self.importer.stats.get('products_updated', 0) - initial_updated
            self.stats['skipped_products'] = len(skipped_products)
            self.stats['missing_categories'] = len(missing_categories)
            
            print(f"\n✅ Import completed successfully!")
            print(f"   Products created: {self.stats['created_products']}")
            print(f"   Products updated: {self.stats['updated_products']}")
            
            return True
        except Exception as e:
            error_msg = f"Product import failed: {str(e)}"
            self.error_log.append(error_msg)
            self.stats['errors'] += 1
            print(f"❌ {error_msg}")
            return False
    
    def print_error_summary(self):
        """Print all errors encountered and final statistics"""
        print(f"\n{'='*60}")
        print(f"FINAL SUMMARY")
        print(f"{'='*60}")
        print(f"📊 Statistics:")
        print(f"   SKUs extracted: {self.stats['extracted_skus']}")
        print(f"   Products created: {self.stats['created_products']}")
        print(f"   Products updated: {self.stats['updated_products']}")
        print(f"   Products skipped: {self.stats['skipped_products']}")
        print(f"   Categories resolved: {self.stats['category_resolutions']}")
        print(f"   Missing categories: {self.stats['missing_categories']}")
        print(f"   Errors encountered: {len(self.error_log)}")
        
        if self.serial_filter:
            print(f"   Serial processed: {self.serial_filter}")
        
        if self.error_log:
            print(f"\n❌ ERRORS ({len(self.error_log)}):")
            for i, error in enumerate(self.error_log, 1):
                print(f"   {i:2d}. {error}")
        else:
            print(f"\n✅ No errors encountered!")
            
        if self.stats['created_products'] + self.stats['updated_products'] > 0:
            print(f"\n🎉 Successfully processed {self.stats['created_products'] + self.stats['updated_products']} products!")
    
    def close(self):
        """Cleanup"""
        if self.conn:
            self.conn.close()
    
    def run(self):
        """Run product creation with resume capability"""
        
        # Check for existing checkpoint
        checkpoint_data = self.load_checkpoint()
        if checkpoint_data:
            print(f"🔄 Resuming from previous session...")
            
        if not self.connect():
            return False
        
        try:
            self.setup_woocommerce()
            
            # Extract or resume SKUs
            products_by_sku = self.extract_unique_skus(checkpoint_data)
            
            if self.interrupted:
                return False
                
            success = self.create_products(products_by_sku)
            
            if success and not self.interrupted:
                print(f"\n🎉 Import completed successfully! Cleaning up checkpoint...")
                self.clear_checkpoint()
            
            # Print summaries
            self.importer.print_summary()
            self.print_error_summary()
            
            return success
            
        finally:
            self.close()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Create products from Oscar database in WooCommerce',
        epilog="""Examples:
  python create_products.py --serial LSH14J7C7MA114771 --limit 10
  python create_products.py --serial LSH14J7C7MA114771
  python create_products.py --limit 100
  python create_products.py

Note: This script assumes categories have been created by create_categories.py""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--serial', help='Filter by specific serial number (e.g., LSH14J7C7MA114771)')
    parser.add_argument('--limit', type=int, help='Limit number of unique SKUs to process (useful for testing)')
    parser.add_argument('--checkpoint-dir', help='Checkpoint directory for import resumability')
    
    args = parser.parse_args()
    
    print(f"\n{'='*80}")
    print("🏭 Oscar Product Creator")
    print(f"{'='*80}")
    print("This script extracts unique SKUs from Oscar database and creates/updates")
    print("products in WooCommerce with proper category assignment and SVG images.")
    print("\n📋 Configuration:")
    print(f"   Serial filter: {args.serial or 'ALL SERIALS'}")
    print(f"   Limit: {args.limit or 'NO LIMIT'}")
    print(f"   Checkpoint dir: {args.checkpoint_dir or 'DEFAULT'}")
    print(f"\n🔄 Starting process...")
    
    creator = ProductCreator(serial_filter=args.serial, limit=args.limit, checkpoint_dir=args.checkpoint_dir)
    success = creator.run()
    
    if success:
        print("\n🎉 Product creation completed successfully!")
        return 0
    else:
        print("\n💥 Product creation completed with errors")
        return 1

if __name__ == '__main__':
    exit(main())