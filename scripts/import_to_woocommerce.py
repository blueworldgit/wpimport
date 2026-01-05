"""
WooCommerce Import Script - Phase 3
Imports products from extracted JSON data into WooCommerce
"""
import os
import json
import time
from pathlib import Path
from datetime import datetime
from woocommerce import API
from tqdm import tqdm

class WooCommerceImporter:
    def __init__(self, api_url, consumer_key, consumer_secret, checkpoint_dir, log_dir):
        self.wcapi = API(
            url=api_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            version="wc/v3",
            timeout=30
        )
        self.checkpoint_dir = Path(checkpoint_dir)
        self.log_dir = Path(log_dir)
        self.stats = {
            'start_time': datetime.now().isoformat(),
            'products_created': 0,
            'products_updated': 0,
            'variations_created': 0,
            'categories_created': 0,
            'images_uploaded': 0,
            'errors': [],
            'skipped': []
        }
        self.category_cache = {}  # name -> ID mapping
        self.placeholder_ids = {}  # Will store uploaded placeholder image IDs
        self.processed_skus = set()  # Track processed SKUs to avoid duplicates
    
    def test_connection(self):
        """Test API connection"""
        try:
            response = self.wcapi.get("products", params={"per_page": 1})
            if response.status_code == 200:
                print("✓ WooCommerce API connection successful")
                return True
            else:
                print(f"✗ API connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ API connection error: {str(e)}")
            return False
    
    def upload_placeholder_images(self, placeholder_dir):
        """
        Upload placeholder images to WordPress media library
        Returns dict mapping placeholder type to media ID
        """
        print("\n" + "="*60)
        print("Uploading Placeholder Images to WordPress")
        print("="*60 + "\n")
        
        placeholders = {
            'general': placeholder_dir / 'placeholder_general.png',
            'left': placeholder_dir / 'placeholder_left.png',
            'right': placeholder_dir / 'placeholder_right.png'
        }
        
        for key, filepath in placeholders.items():
            if not filepath.exists():
                print(f"⚠ Placeholder not found: {filepath}")
                continue
            
            try:
                with open(filepath, 'rb') as img:
                    files = {'file': img}
                    # Use requests to upload to wp-json/wp/v2/media
                    import requests
                    response = requests.post(
                        f"{self.wcapi.url}/wp-json/wp/v2/media",
                        files=files,
                        auth=(self.wcapi.consumer_key, self.wcapi.consumer_secret),
                        headers={'Content-Disposition': f'attachment; filename="{filepath.name}"'}
                    )
                    
                    if response.status_code == 201:
                        media_data = response.json()
                        self.placeholder_ids[key] = media_data['id']
                        print(f"✓ Uploaded {key} placeholder (ID: {media_data['id']})")
                        self.stats['images_uploaded'] += 1
                    else:
                        print(f"⚠ Failed to upload {key}: {response.status_code}")
            
            except Exception as e:
                print(f"✗ Error uploading {key}: {str(e)}")
        
        print(f"\n✓ Placeholder IDs: {self.placeholder_ids}\n")
        return self.placeholder_ids
    
    def upload_image_to_wordpress(self, image_path):
        """
        Upload a single image (PNG or SVG) to WordPress media library
        Returns media ID or None if upload fails
        """
        import requests
        
        try:
            # Determine MIME type
            mime_type = 'image/png' if image_path.suffix == '.png' else 'image/svg+xml'
            
            with open(image_path, 'rb') as img:
                files = {'file': img}
                response = requests.post(
                    f"{self.wcapi.url}/wp-json/wp/v2/media",
                    files=files,
                    auth=(self.wcapi.consumer_key, self.wcapi.consumer_secret),
                    headers={
                        'Content-Disposition': f'attachment; filename="{image_path.name}"',
                        'Content-Type': mime_type
                    }
                )
                
                if response.status_code == 201:
                    media_data = response.json()
                    return media_data['id']
                else:
                    print(f"    Upload failed: HTTP {response.status_code}")
                    return None
        
        except Exception as e:
            print(f"    Upload error: {str(e)}")
            return None
    
    def get_or_create_category(self, category_name, parent_id=0):
        """
        Get existing category ID or create new one
        Uses cache to avoid repeated API calls
        """
        # Check cache first
        cache_key = f"{category_name}_{parent_id}"
        if cache_key in self.category_cache:
            return self.category_cache[cache_key]
        
        # Search for existing category
        try:
            response = self.wcapi.get("products/categories", params={
                "search": category_name,
                "parent": parent_id,
                "per_page": 100
            })
            
            if response.status_code == 200:
                categories = response.json()
                for cat in categories:
                    if cat['name'].lower() == category_name.lower() and cat['parent'] == parent_id:
                        self.category_cache[cache_key] = cat['id']
                        return cat['id']
        except Exception as e:
            print(f"⚠ Error searching category: {str(e)}")
        
        # Create new category
        try:
            category_data = {
                "name": category_name,
                "parent": parent_id,
                "slug": category_name.lower().replace(' ', '-').replace('&', 'and')
            }
            
            response = self.wcapi.post("products/categories", category_data)
            
            if response.status_code == 201:
                cat_data = response.json()
                self.category_cache[cache_key] = cat_data['id']
                self.stats['categories_created'] += 1
                return cat_data['id']
            else:
                print(f"⚠ Failed to create category '{category_name}': {response.status_code}")
                return None
        
        except Exception as e:
            print(f"✗ Error creating category '{category_name}': {str(e)}")
            return None
    
    def build_category_hierarchy(self, categories_list):
        """
        Build category hierarchy and return category IDs
        categories_list: [serial, parent_category, diagram_name]
        Returns: list of category IDs
        """
        category_ids = []
        parent_id = 0
        
        for category_name in categories_list:
            cat_id = self.get_or_create_category(category_name, parent_id)
            if cat_id:
                category_ids.append(cat_id)
                parent_id = cat_id  # Next category is child of this one
        
        return category_ids
    
    def get_diagram_image_path(self, product_data):
        """
        Find diagram image for product (PNG or SVG)
        Priority: PNG → SVG → placeholder
        Returns: (file_path, file_type) or (None, None)
        """
        base_dir = Path(__file__).resolve().parent.parent
        images_dir = base_dir / 'images' / 'converted'
        
        # Get serial number and diagram name from product data
        diagram_file = product_data.get('diagram_file', '')
        if diagram_file:
            # Extract diagram name from HTML file path
            diagram_name = Path(diagram_file).stem.replace(' ', '_')
            
            # Build expected filename pattern (SerialNumber_DiagramName)
            # Try to extract serial from categories
            categories = product_data.get('categories', [])
            serial_number = None
            for cat in categories:
                if cat.startswith('LSF') and len(cat) == 17:
                    serial_number = cat
                    break
            
            if serial_number:
                base_filename = f"{serial_number}_{diagram_name}"
                
                # Check for PNG first (preferred)
                png_path = images_dir / f"{base_filename}.png"
                if png_path.exists():
                    return (png_path, 'png')
                
                # Check for SVG as fallback
                svg_path = images_dir / f"{base_filename}.svg"
                if svg_path.exists():
                    return (svg_path, 'svg')
        
        return (None, None)
    
    def assign_placeholder_image(self, product_data):
        """
        Assign appropriate placeholder based on orientation
        Returns image ID to use for product
        """
        if product_data['type'] == 'simple':
            orientation = product_data.get('orientation', '').lower() if product_data.get('orientation') else ''
            
            if 'left' in orientation:
                return self.placeholder_ids.get('left', self.placeholder_ids.get('general'))
            elif 'right' in orientation:
                return self.placeholder_ids.get('right', self.placeholder_ids.get('general'))
        
        return self.placeholder_ids.get('general')
    
    def create_simple_product(self, product_data):
        """Create a simple WooCommerce product"""
        sku = product_data['sku']
        
        # Check if already processed
        if sku in self.processed_skus:
            self.stats['skipped'].append(f"Duplicate SKU: {sku}")
            return None
        
        # Build product title with diagram code
        diagram_code = product_data.get('diagram_code', '')
        if diagram_code:
            product_title = f"{diagram_code} - {product_data['name']}"
        else:
            product_title = product_data['name']
        
        # Build product description
        description = f"<p><strong>Part Number:</strong> {sku}</p>"
        if diagram_code:
            description += f"<p><strong>Diagram Code:</strong> {diagram_code}</p>"
        description += f"<p><strong>Callout Number:</strong> {product_data['callout']}</p>"
        description += f"<p><strong>Quantity:</strong> {product_data['quantity']}</p>"
        
        if product_data.get('remark'):
            description += f"<p><strong>Remark:</strong> {product_data['remark']}</p>"
        
        # Get category IDs
        category_ids = self.build_category_hierarchy(product_data['categories'])
        
        # Try to find diagram image (PNG or SVG)
        diagram_path, img_type = self.get_diagram_image_path(product_data)
        image_id = None
        
        if diagram_path:
            # Upload diagram image to WordPress
            try:
                image_id = self.upload_image_to_wordpress(diagram_path)
                if image_id:
                    self.stats['images_uploaded'] += 1
                    print(f"  ✓ Uploaded {img_type.upper()}: {diagram_path.name}")
            except Exception as e:
                print(f"  ⚠ Failed to upload {img_type.upper()}: {e}")
                # Fall back to placeholder
                image_id = self.assign_placeholder_image(product_data)
        else:
            # Use placeholder if no diagram image exists
            image_id = self.assign_placeholder_image(product_data)
        
        # Build product data
        wc_product = {
            "name": product_title,
            "type": "simple",
            "sku": sku,
            "regular_price": "0.00",  # Placeholder price
            "description": description,
            "short_description": product_data.get('remark', ''),
            "categories": [{"id": cat_id} for cat_id in category_ids],
            "images": [{"id": image_id}] if image_id else [],
            "manage_stock": True,
            "stock_quantity": 50,
            "stock_status": "instock",
            "meta_data": [
                {"key": "diagram_code", "value": diagram_code},
                {"key": "callout_number", "value": product_data['callout']},
                {"key": "diagram_file", "value": product_data['diagram_file']},
                {"key": "orientation", "value": product_data.get('orientation', 'N/A')},
                {"key": "quantity_per_vehicle", "value": product_data['quantity']},
                {"key": "remark", "value": product_data.get('remark', '')}
            ]
        }
        
        try:
            response = self.wcapi.post("products", wc_product)
            
            if response.status_code == 201:
                self.processed_skus.add(sku)
                self.stats['products_created'] += 1
                return response.json()['id']
            else:
                error_msg = f"Failed to create product {sku}: {response.status_code} - {response.text}"
                self.stats['errors'].append(error_msg)
                return None
        
        except Exception as e:
            error_msg = f"Error creating product {sku}: {str(e)}"
            self.stats['errors'].append(error_msg)
            return None
    
    def create_variable_product(self, product_data):
        """Create a variable WooCommerce product with variations"""
        # Get category IDs
        category_ids = self.build_category_hierarchy(product_data['categories'])
        
        # Build product title with diagram code
        diagram_code = product_data.get('diagram_code', '')
        if diagram_code:
            product_title = f"{diagram_code} - {product_data['name']}"
        else:
            product_title = product_data['name']
        
        # Build description
        description = ""
        if diagram_code:
            description += f"<p><strong>Diagram Code:</strong> {diagram_code}</p>"
        description += f"<p><strong>Callout Number:</strong> {product_data['callout']}</p>"
        description += f"<p>This product has {len(product_data['variations'])} variations.</p>"
        
        # Get placeholder image (use general for parent)
        image_id = self.placeholder_ids.get('general')
        
        # Build parent product
        wc_product = {
            "name": product_title,
            "type": "variable",
            "description": description,
            "categories": [{"id": cat_id} for cat_id in category_ids],
            "images": [{"id": image_id}] if image_id else [],
            "attributes": [
                {
                    "name": "Orientation",
                    "visible": True,
                    "variation": True,
                    "options": [v['orientation'] for v in product_data['variations'] if v['orientation']]
                }
            ],
            "meta_data": [
                {"key": "diagram_code", "value": diagram_code},
                {"key": "callout_number", "value": product_data['callout']},
                {"key": "diagram_file", "value": product_data['diagram_file']}
            ]
        }
        
        try:
            # Create parent product
            response = self.wcapi.post("products", wc_product)
            
            if response.status_code != 201:
                error_msg = f"Failed to create variable product {product_data['name']}: {response.status_code}"
                self.stats['errors'].append(error_msg)
                return None
            
            parent_id = response.json()['id']
            self.stats['products_created'] += 1
            
            # Create variations
            for variation in product_data['variations']:
                sku = variation['sku']
                
                # Check if SKU already used
                if sku in self.processed_skus:
                    self.stats['skipped'].append(f"Duplicate SKU in variation: {sku}")
                    continue
                
                # Get placeholder image for variation
                var_image_id = self.placeholder_ids.get('left') if 'left' in variation['orientation'].lower() \
                    else self.placeholder_ids.get('right') if 'right' in variation['orientation'].lower() \
                    else self.placeholder_ids.get('general')
                
                variation_data = {
                    "sku": sku,
                    "regular_price": "0.00",
                    "manage_stock": True,
                    "stock_quantity": 50,
                    "stock_status": "instock",
                    "attributes": [
                        {
                            "name": "Orientation",
                            "option": variation['orientation']
                        }
                    ],
                    "image": {"id": var_image_id} if var_image_id else None,
                    "meta_data": [
                        {"key": "quantity_per_vehicle", "value": variation['quantity']},
                        {"key": "remark", "value": variation['remark']}
                    ]
                }
                
                var_response = self.wcapi.post(f"products/{parent_id}/variations", variation_data)
                
                if var_response.status_code == 201:
                    self.processed_skus.add(sku)
                    self.stats['variations_created'] += 1
                else:
                    error_msg = f"Failed to create variation {sku}: {var_response.status_code}"
                    self.stats['errors'].append(error_msg)
            
            return parent_id
        
        except Exception as e:
            error_msg = f"Error creating variable product {product_data['name']}: {str(e)}"
            self.stats['errors'].append(error_msg)
            return None
    
    def import_products(self, products_data, test_mode=False):
        """
        Import products from extracted data
        
        Args:
            products_data: List of product dictionaries
            test_mode: If True, ask for confirmation after each product
        """
        print(f"\n{'='*60}")
        print(f"Importing {len(products_data)} products to WooCommerce")
        print(f"{'='*60}\n")
        
        for product in tqdm(products_data, desc="Importing products"):
            if product['type'] == 'simple':
                self.create_simple_product(product)
            elif product['type'] == 'variable':
                self.create_variable_product(product)
            
            # Rate limiting (WooCommerce API: ~60 requests/minute)
            time.sleep(0.5)
        
        self.stats['end_time'] = datetime.now().isoformat()
    
    def save_checkpoint(self, filename='import_checkpoint.json'):
        """Save import progress for resumability"""
        checkpoint_path = self.checkpoint_dir / filename
        
        checkpoint_data = {
            'processed_skus': list(self.processed_skus),
            'stats': self.stats,
            'category_cache': self.category_cache,
            'placeholder_ids': self.placeholder_ids
        }
        
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        return checkpoint_path
    
    def print_summary(self):
        """Print import summary"""
        print(f"\n{'='*60}")
        print("Import Summary")
        print(f"{'='*60}")
        print(f"Products created:        {self.stats['products_created']}")
        print(f"Variations created:      {self.stats['variations_created']}")
        print(f"Categories created:      {self.stats['categories_created']}")
        print(f"Images uploaded:         {self.stats['images_uploaded']}")
        print(f"Skipped (duplicates):    {len(self.stats['skipped'])}")
        print(f"Errors:                  {len(self.stats['errors'])}")
        print(f"{'='*60}\n")
        
        if self.stats['errors']:
            print("\n⚠ Errors encountered:")
            for error in self.stats['errors'][:10]:
                print(f"  - {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more")
        
        if self.stats['skipped']:
            print(f"\n⚠ Skipped {len(self.stats['skipped'])} items (see logs for details)")


def main():
    """Main import function"""
    # Paths
    base_dir = Path(__file__).parent.parent
    data_file = base_dir / 'data' / 'extracted' / 'extracted_data_test.json'
    checkpoint_dir = base_dir / 'data' / 'checkpoints'
    log_dir = base_dir / 'logs'
    placeholder_dir = base_dir / 'images' / 'placeholders'
    
    # Load keys
    keys_file = base_dir / 'keys.txt'
    with open(keys_file, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
        # Find lines after "Consumer key" and "Consumer secret"
        consumer_key = None
        consumer_secret = None
        for i, line in enumerate(lines):
            if 'Consumer key' in line and i + 1 < len(lines):
                consumer_key = lines[i + 1]
            elif 'Consumer secret' in line and i + 1 < len(lines):
                consumer_secret = lines[i + 1]
    
    # Load config
    import sys
    sys.path.insert(0, str(base_dir))
    from config import WORDPRESS_URL
    wp_url = WORDPRESS_URL
    
    print("\n" + "="*60)
    print("WooCommerce EPC Import - Phase 3")
    print("="*60)
    print(f"\nWordPress URL: {wp_url}")
    print(f"Data file: {data_file.name}")
    
    # Create importer
    importer = WooCommerceImporter(wp_url, consumer_key, consumer_secret, checkpoint_dir, log_dir)
    
    # Test connection
    if not importer.test_connection():
        print("\n✗ Cannot proceed - API connection failed")
        print("Please check:")
        print("  1. WordPress URL is correct")
        print("  2. WooCommerce is installed and activated")
        print("  3. API keys are valid")
        return
    
    # Upload placeholders
    importer.upload_placeholder_images(placeholder_dir)
    
    if not importer.placeholder_ids:
        print("\n⚠ No placeholder images uploaded - continuing without images")
    
    # Load extracted data
    with open(data_file, 'r', encoding='utf-8') as f:
        extracted_data = json.load(f)
    
    print(f"\n✓ Loaded {len(extracted_data['products'])} products from {data_file.name}")
    
    # Import products
    importer.import_products(extracted_data['products'])
    
    # Save checkpoint
    checkpoint_path = importer.save_checkpoint()
    print(f"\n✓ Checkpoint saved to: {checkpoint_path}")
    
    # Print summary
    importer.print_summary()
    
    print("\n✓ Import complete!")
    print("\nNext steps:")
    print("  1. Check your WooCommerce products in WordPress admin")
    print("  2. Update pricing with Phase 4 script (when ready)")
    print("  3. Replace placeholder images with Phase 5 script (when ready)")


if __name__ == "__main__":
    main()
