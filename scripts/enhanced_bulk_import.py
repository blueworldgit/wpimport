#!/usr/bin/env python3
"""
Enhanced Bulk Import with PNG Images
Uses pre-converted PNG files during product creation for optimal performance
"""
import sys
import json
import hashlib
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
from woocommerce import API
import requests
import time
from datetime import datetime
from tqdm import tqdm
import mimetypes

# Add parent directory to path
base_dir = Path(__file__).parent.parent
sys.path.insert(0, str(base_dir))

from config import WORDPRESS_URL

class EnhancedBulkImporter:
    def __init__(self):
        self.images_dir = base_dir / 'images' / 'converted'
        self.data_dir = base_dir / 'data'
        self.data_dir.mkdir(exist_ok=True)
        self.checkpoint_file = self.data_dir / 'checkpoints' / 'enhanced_import_checkpoint.json'
        self.checkpoint_file.parent.mkdir(exist_ok=True)
        
        self.processed_skus = set()
        self.load_checkpoint()
        
        # Load WooCommerce API
        self.load_api_credentials()
        
        # Stats
        self.stats = {
            'total_parts': 0,
            'products_created': 0,
            'images_uploaded': 0,
            'skipped': 0,
            'errors': []
        }
        
    def load_api_credentials(self):
        """Load WordPress API credentials"""
        keys_file = base_dir / 'keys.txt'
        try:
            with open(keys_file, 'r') as f:
                content = f.read().strip()
                lines = content.split('\\n')
                
                consumer_key = None
                consumer_secret = None
                
                for line in lines:
                    if 'ck_' in line:
                        consumer_key = line.strip()
                    elif 'cs_' in line:
                        consumer_secret = line.strip()
            
            if not consumer_key or not consumer_secret:
                raise Exception("API keys not found in keys.txt")
            
            self.wcapi = API(
                url=WORDPRESS_URL,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                version="wc/v3",
                timeout=60
            )
            
            print("✅ WooCommerce API initialized")
            
        except Exception as e:
            print(f"❌ Failed to load API credentials: {e}")
            sys.exit(1)
    
    def load_checkpoint(self):
        """Load processing checkpoint"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint_data = json.load(f)
                    self.processed_skus = set(checkpoint_data.get('processed_skus', []))
                print(f"📋 Loaded checkpoint: {len(self.processed_skus)} SKUs already processed")
            except Exception as e:
                print(f"⚠️  Checkpoint load error: {e}")
                self.processed_skus = set()
    
    def save_checkpoint(self):
        """Save processing checkpoint"""
        try:
            checkpoint_data = {
                'processed_skus': list(self.processed_skus),
                'last_updated': datetime.now().isoformat(),
                'stats': self.stats
            }
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Checkpoint save error: {e}")
    
    def get_parts_from_oscar(self, limit=None):
        """Extract parts from Oscar database with image matching"""
        print("🔍 Extracting parts from Oscar database...")
        
        try:
            conn = psycopg2.connect(
                dbname='parts_store',
                user='postgres', 
                password='N0rwich!',
                host='80.95.207.42',
                port='5432'
            )
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Build exclusion clause for processed SKUs
            exclusion_clause = ""
            if self.processed_skus:
                escaped_skus = [sku.replace("'", "''") for sku in self.processed_skus]
                sku_list = "','".join(escaped_skus)
                exclusion_clause = f"AND p.part_number NOT IN ('{sku_list}')"
            
            # Main query with PNG filename mapping
            query = f"""
            SELECT 
                p.id as part_id,
                p.part_number as sku,
                p.usage_name as name,
                p.call_out_order as callout_number,
                p.unit_qty,
                p.lr,
                p.remark,
                p.nn_note,
                ct.title as diagram_name,
                pt.title as main_category,
                sn.serial,
                sn.vehicle_brand
            FROM motorpartsdata_part p
            JOIN motorpartsdata_childtitle ct ON p.child_title_id = ct.id
            JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id
            JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
            WHERE p.part_number IS NOT NULL 
            AND p.part_number != ''
            {exclusion_clause}
            ORDER BY sn.serial, pt.title, ct.title, p.part_number
            {f'LIMIT {limit}' if limit else ''}
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            self.stats['total_parts'] = len(results)
            print(f"✅ Found {len(results)} parts to import")
            return results
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            return []
    
    def find_diagram_png(self, serial, diagram_name):
        """Find PNG file for a diagram"""
        # Clean diagram name for filename matching
        diagram_clean = diagram_name.replace(' - ', '_').replace(' ', '_').replace('&', '_').replace(',', '').replace('(', '').replace(')', '').replace('/', '_')
        
        # Try exact match first
        exact_filename = f"{serial}_{diagram_clean}.png"
        exact_path = self.images_dir / exact_filename
        
        if exact_path.exists():
            return exact_path
        
        # Try fuzzy matching (search for similar names)
        for png_file in self.images_dir.glob(f"{serial}_*.png"):
            if diagram_clean.lower() in png_file.stem.lower():
                return png_file
        
        return None
    
    def upload_image_to_wordpress(self, image_path, alt_text):
        """Upload image to WordPress media library"""
        try:
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(str(image_path))
            if not mime_type:
                mime_type = 'image/png'
            
            # Read image data
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Upload to WordPress
            headers = {
                'Content-Disposition': f'attachment; filename={image_path.name}',
                'Content-Type': mime_type
            }
            
            response = requests.post(
                f"{WORDPRESS_URL}/wp-json/wp/v2/media",
                data=image_data,
                headers=headers,
                auth=self.get_wp_auth(),
                timeout=60
            )
            
            if response.status_code == 201:
                media_data = response.json()
                return {"id": media_data['id']}
            else:
                print(f"   ❌ Image upload failed: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Image upload error: {e}")
            return None
    
    def get_wp_auth(self):
        """Get WordPress authentication"""
        # You'll need to add WordPress username/app_password to config
        # For now, return None - WooCommerce API handles auth
        return None
    
    def create_product_with_image(self, part_data):
        """Create WooCommerce product with PNG image"""
        try:
            # Generate unique SKU
            original_sku = part_data['sku']
            part_id = part_data['part_id']
            hash_input = f"{original_sku}-{part_id}"
            sku_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:4].upper()
            unique_sku = f"{original_sku}-{sku_suffix}"
            
            # Build product name with diagram code
            product_name = f"{part_data['name']}"
            if part_data['diagram_name']:
                product_name = f"{part_data['diagram_name']} - {product_name}"
            
            # Build categories (simplified)
            categories = []
            if part_data['vehicle_brand']:
                categories.append(part_data['vehicle_brand'])
            if part_data['serial']:
                categories.append(part_data['serial'])
            if part_data['main_category']:
                categories.append(part_data['main_category'])
            
            # Find and upload diagram image
            image_list = []
            png_path = self.find_diagram_png(part_data['serial'], part_data['diagram_name'])
            
            if png_path:
                alt_text = f"Diagram: {part_data['diagram_name']}"
                image_data = self.upload_image_to_wordpress(png_path, alt_text)
                if image_data:
                    image_list.append(image_data)
                    self.stats['images_uploaded'] += 1
                    print(f"   📷 Uploaded: {png_path.name}")
            
            # Build product data
            product_data = {
                "name": product_name,
                "type": "simple",
                "sku": unique_sku,
                "regular_price": "0.00",
                "description": f"Part for {part_data['serial']} - {part_data['main_category']}",
                "short_description": f"Callout: {part_data['callout_number'] or 'N/A'}",
                "categories": [{"name": cat} for cat in categories],
                "images": image_list,
                "manage_stock": False,
                "stock_status": "instock",
                "meta_data": [
                    {"key": "original_sku", "value": original_sku},
                    {"key": "oscar_part_id", "value": str(part_data['part_id'])},
                    {"key": "callout_number", "value": str(part_data['callout_number'] or '')},
                    {"key": "unit_qty", "value": part_data['unit_qty'] or ''},
                    {"key": "lr", "value": part_data['lr'] or ''},
                    {"key": "vehicle_serial", "value": part_data['serial']},
                    {"key": "diagram_name", "value": part_data['diagram_name'] or ''},
                    {"key": "has_diagram_image", "value": 'true' if png_path else 'false'}
                ]
            }
            
            # Create product
            response = self.wcapi.post("products", product_data)
            
            if response.status_code == 201:
                self.stats['products_created'] += 1
                self.processed_skus.add(original_sku)
                return response.json()['id']
            else:
                print(f"   ❌ Product creation failed: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Product creation error: {e}")
            return None
    
    def import_products(self, limit=None):
        """Main import process"""
        print("\\n" + "="*70)
        print("🚀 ENHANCED BULK IMPORT WITH IMAGES")
        print("="*70)
        print(f"WordPress: {WORDPRESS_URL}")
        print(f"Images: {len(list(self.images_dir.glob('*.png')))} PNG files available")
        print("="*70)
        
        # Get parts to import
        parts = self.get_parts_from_oscar(limit=limit)
        
        if not parts:
            print("❌ No parts to import")
            return
        
        # Import each part
        print(f"\\n📦 Processing {len(parts)} parts...")
        
        for i, part in enumerate(tqdm(parts, desc="Creating products"), 1):
            print(f"\\n{i}. {part['sku']} - {part['name']}")
            
            product_id = self.create_product_with_image(part)
            
            if product_id:
                print(f"   ✅ Created product ID: {product_id}")
            else:
                self.stats['errors'].append(f"Failed: {part['sku']}")
                self.stats['skipped'] += 1
            
            # Save checkpoint every 10 products
            if i % 10 == 0:
                self.save_checkpoint()
                print(f"   💾 Checkpoint saved ({i}/{len(parts)})")
                time.sleep(1)  # Rate limiting
        
        # Final checkpoint
        self.save_checkpoint()
        self.print_summary()
    
    def print_summary(self):
        """Print import summary"""
        print("\\n" + "="*70)
        print("📊 IMPORT SUMMARY")
        print("="*70)
        print(f"Total parts processed:    {self.stats['total_parts']}")
        print(f"Products created:         {self.stats['products_created']}")
        print(f"Images uploaded:          {self.stats['images_uploaded']}")
        print(f"Skipped/errors:           {self.stats['skipped']}")
        print("="*70)
        
        if self.stats['errors']:
            print("\\n❌ First 5 errors:")
            for error in self.stats['errors'][:5]:
                print(f"   • {error}")
        
        success_rate = (self.stats['products_created'] / self.stats['total_parts']) * 100 if self.stats['total_parts'] > 0 else 0
        print(f"\\n✅ Success rate: {success_rate:.1f}%")
        
        if self.stats['products_created'] > 0:
            print("\\n🎯 Next steps:")
            print("   1. Run pricing update script")
            print("   2. Test products in WooCommerce")
            print("   3. Import remaining batches")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Bulk Import with Images')
    parser.add_argument('--limit', type=int, help='Limit number of products to import')
    parser.add_argument('--test', action='store_true', help='Test with 10 products only')
    
    args = parser.parse_args()
    
    if args.test:
        limit = 10
    else:
        limit = args.limit
    
    importer = EnhancedBulkImporter()
    importer.import_products(limit=limit)

if __name__ == "__main__":
    main()