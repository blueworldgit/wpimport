"""
Test Import - 10 products WITHOUT images
Products only, images can be added manually later
"""
import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from scripts.import_to_woocommerce import WooCommerceImporter

def main():
    base_dir = Path(__file__).resolve().parent
    
    # Configuration - PRODUCTION SITE
    WORDPRESS_URL = "https://maxusvanparts.co.uk/"
    CONSUMER_KEY = "ck_1be77215f05ca7f848ac0ec16a6b68e76ced9302"
    CONSUMER_SECRET = "cs_b2c2be6911c85fe9abc62b4ec5170b9ab746392e"
    
    # Paths
    checkpoint_dir = base_dir / 'data' / 'checkpoints'
    log_dir = base_dir / 'logs'
    test_data_file = base_dir / 'data' / 'extracted' / 'extracted_data_test.json'
    
    # Load test data
    print("\n" + "="*60)
    print("Loading Test Data (No Images)")
    print("="*60 + "\n")
    
    with open(test_data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Limit to 10 products
    products = data['products'][:10]
    print(f"Testing with {len(products)} products\n")
    
    # Create importer WITHOUT WordPress credentials (skip images)
    importer = WooCommerceImporter(
        api_url=WORDPRESS_URL,
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET,
        checkpoint_dir=checkpoint_dir,
        log_dir=log_dir,
        wp_username=None,  # No credentials = skip image upload
        wp_app_password=None
    )
    
    # Test connection
    print("="*60)
    print("Testing WooCommerce Connection")
    print("="*60 + "\n")
    
    if not importer.test_connection():
        print("\n✗ Cannot connect to WooCommerce. Aborting.")
        return
    
    # Skip placeholder upload
    print("Skipping image uploads (products only)\n")
    
    # Import products
    print("="*60)
    print("Importing 10 Test Products")
    print("="*60 + "\n")
    
    for i, product in enumerate(products, 1):
        print(f"\n[{i}/10] Importing: {product['name']}")
        print(f"  SKU: {product['sku']}")
        print(f"  Diagram: {product.get('diagram_code', 'N/A')}")
        
        if product['type'] == 'simple':
            result = importer.create_simple_product(product)
            if result:
                product_id = result if isinstance(result, int) else result.get('id')
                print(f"  ✓ Created product ID: {product_id}")
        elif product['type'] == 'variable':
            result = importer.create_variable_product(product)
            if result:
                product_id = result if isinstance(result, int) else result.get('id')
                print(f"  ✓ Created variable product ID: {product_id}")
    
    # Print summary
    importer.print_summary()

if __name__ == '__main__':
    main()
