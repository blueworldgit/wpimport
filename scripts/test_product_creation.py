#!/usr/bin/env python3
"""
WordPress Product Creator Test
Creates a test product with specified SKU
"""
from woocommerce import API
from pathlib import Path
import sys
import argparse

# Add parent directory to path for imports
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))
from config import WORDPRESS_URL

class WPProductCreator:
    def __init__(self):
        self.wcapi = None
        self.load_credentials()
        
    def load_credentials(self):
        """Load WooCommerce API credentials"""
        keys_file = base_dir / 'keys.txt'
        
        consumer_key = None
        consumer_secret = None
        
        with open(keys_file, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
            for i, line in enumerate(lines):
                if 'Consumer key' in line and i+1 < len(lines): 
                    consumer_key = lines[i+1]
                if 'Consumer secret' in line and i+1 < len(lines): 
                    consumer_secret = lines[i+1]
        
        if not consumer_key or not consumer_secret:
            raise Exception("WooCommerce credentials not found in keys.txt")
        
        # Initialize WooCommerce API
        self.wcapi = API(
            url=WORDPRESS_URL,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            wp_api=True,
            version="wc/v3",
            timeout=30
        )
        print(f"✓ Connected to WordPress: {WORDPRESS_URL}")

    def check_sku_exists(self, sku):
        """Check if a product with this SKU already exists"""
        try:
            response = self.wcapi.get('products', params={'sku': sku})
            
            if response.status_code == 200:
                products = response.json()
                return len(products) > 0, products
            else:
                print(f"❌ Error checking SKU: {response.status_code}")
                return False, []
                
        except Exception as e:
            print(f"❌ Exception checking SKU: {e}")
            return False, []

    def create_product(self, sku, name=None, description=None, price=None, categories=None):
        """Create a product with the specified details"""
        
        # Check if SKU already exists
        exists, existing_products = self.check_sku_exists(sku)
        
        if exists:
            print(f"⚠️  Product with SKU '{sku}' already exists:")
            for product in existing_products:
                print(f"   📦 ID: {product['id']}, Name: {product['name']}, Status: {product['status']}")
            return existing_products[0]
        
        # Generate default values if not provided
        if name is None:
            name = f"Test Product - {sku}"
        
        if description is None:
            description = f"Test product created with SKU {sku} for testing purposes."
        
        if price is None:
            price = "99.99"
        
        # Prepare product data
        product_data = {
            'name': name,
            'sku': sku,
            'type': 'simple',
            'regular_price': str(price),
            'description': description,
            'short_description': f"Test product {sku}",
            'status': 'publish',
            'catalog_visibility': 'visible',
            'manage_stock': False,
            'stock_status': 'instock'
        }
        
        # Add categories if provided
        if categories:
            product_data['categories'] = categories
        
        print(f"🚀 Creating product with SKU: {sku}")
        print(f"   📝 Name: {name}")
        print(f"   💰 Price: £{price}")
        print(f"   📂 Categories: {len(categories) if categories else 0}")
        
        try:
            response = self.wcapi.post('products', product_data)
            
            if response.status_code == 201:
                product = response.json()
                print(f"✅ Product created successfully!")
                print(f"   🆔 Product ID: {product['id']}")
                print(f"   🔗 URL: {product['permalink']}")
                print(f"   📊 Status: {product['status']}")
                return product
            else:
                print(f"❌ Error creating product: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   💬 Error message: {error_data.get('message', 'Unknown error')}")
                    if 'data' in error_data:
                        print(f"   📋 Error details: {error_data['data']}")
                except:
                    print(f"   📋 Raw response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Exception creating product: {e}")
            return None

    def get_sample_categories(self, limit=3):
        """Get some sample categories to assign to the product"""
        try:
            response = self.wcapi.get('products/categories', params={
                'per_page': limit,
                'orderby': 'count',
                'order': 'desc'
            })
            
            if response.status_code == 200:
                categories = response.json()
                return [{'id': cat['id']} for cat in categories]
            else:
                print(f"⚠️  Could not fetch categories: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"⚠️  Exception fetching categories: {e}")
            return []

    def delete_product(self, product_id):
        """Delete a product by ID"""
        try:
            response = self.wcapi.delete(f'products/{product_id}', params={'force': True})
            
            if response.status_code == 200:
                print(f"✅ Product {product_id} deleted successfully")
                return True
            else:
                print(f"❌ Error deleting product: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Exception deleting product: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Test WordPress product creation')
    parser.add_argument('--sku', default='C00155802', help='SKU for the test product')
    parser.add_argument('--name', help='Product name')
    parser.add_argument('--description', help='Product description')
    parser.add_argument('--price', help='Product price')
    parser.add_argument('--categories', action='store_true', help='Add sample categories')
    parser.add_argument('--delete', help='Delete product by ID instead of creating')
    
    args = parser.parse_args()
    
    print("="*80)
    print("🧪 WORDPRESS PRODUCT CREATION TEST")
    print("="*80)
    
    try:
        creator = WPProductCreator()
        
        if args.delete:
            # Delete mode
            print(f"🗑️  Deleting product ID: {args.delete}")
            success = creator.delete_product(args.delete)
            return 0 if success else 1
        else:
            # Create mode
            categories = None
            if args.categories:
                print("🔍 Fetching sample categories...")
                categories = creator.get_sample_categories()
                if categories:
                    print(f"✓ Found {len(categories)} categories to assign")
            
            product = creator.create_product(
                sku=args.sku,
                name=args.name,
                description=args.description,
                price=args.price,
                categories=categories
            )
            
            if product:
                print(f"\n🎉 Test completed successfully!")
                print(f"   📦 Product ID: {product['id']}")
                print(f"   🔗 View product: {product['permalink']}")
                print(f"\n💡 To delete this test product, run:")
                print(f"   python {sys.argv[0]} --delete {product['id']}")
                return 0
            else:
                print(f"\n❌ Test failed!")
                return 1
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())