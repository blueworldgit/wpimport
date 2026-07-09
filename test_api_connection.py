"""
WooCommerce API Connection Test Script
Tests the connection to WordPress/WooCommerce using REST API credentials
"""

from woocommerce import API
import json

# API Credentials
WP_URL = "https://maxusvanparts.acstestweb.co.uk/"
CONSUMER_KEY = "ck_25e08d3d9ab1625648f25ccefa4080e8497f7c69"
CONSUMER_SECRET = "cs_d493ee9d22846bb489fd20e7a07b494199b3cfd2"

def test_connection():
    """
    Test WooCommerce API connection and retrieve basic site info
    """
    print("="*70)
    print("WooCommerce API Connection Test")
    print("="*70)
    print(f"\nWordPress URL: {WP_URL}")
    print(f"Consumer Key: {CONSUMER_KEY[:20]}...")
    print(f"Consumer Secret: {CONSUMER_SECRET[:20]}...")
    print("\n" + "-"*70)
    
    try:
        # Initialize WooCommerce API
        wcapi = API(
            url=WP_URL,
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET,
            version="wc/v3",
            timeout=30
        )
        
        print("\n✓ WooCommerce API initialized successfully")
        
        # Test 1: Get WooCommerce System Status
        print("\nTest 1: Retrieving WooCommerce system status...")
        response = wcapi.get("system_status")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Connection successful!")
            print(f"  - WooCommerce Version: {data.get('environment', {}).get('version', 'N/A')}")
            print(f"  - WordPress Version: {data.get('environment', {}).get('wp_version', 'N/A')}")
            print(f"  - PHP Version: {data.get('environment', {}).get('php_version', 'N/A')}")
        else:
            print(f"✗ Failed with status code: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
        
        # Test 2: Get Products Count
        print("\nTest 2: Retrieving products...")
        response = wcapi.get("products", params={"per_page": 5})
        
        if response.status_code == 200:
            products = response.json()
            print(f"✓ Found {len(products)} products (showing first 5)")
            
            if products:
                print("\n  Existing Products:")
                for i, product in enumerate(products, 1):
                    print(f"    {i}. {product['name']} (ID: {product['id']}, SKU: {product.get('sku', 'N/A')})")
            else:
                print("  No products found (this is expected for a new setup)")
        else:
            print(f"✗ Failed with status code: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
        
        # Test 3: Get Product Categories
        print("\nTest 3: Retrieving product categories...")
        response = wcapi.get("products/categories", params={"per_page": 10})
        
        if response.status_code == 200:
            categories = response.json()
            print(f"✓ Found {len(categories)} categories (showing first 10)")
            
            if categories:
                print("\n  Existing Categories:")
                for i, cat in enumerate(categories, 1):
                    parent = cat.get('parent', 0)
                    parent_text = f"(Parent ID: {parent})" if parent > 0 else "(Top Level)"
                    print(f"    {i}. {cat['name']} (ID: {cat['id']}) {parent_text}")
            else:
                print("  No categories found (default categories may be hidden)")
        else:
            print(f"✗ Failed with status code: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
        
        # Test 4: Get Product Attributes
        print("\nTest 4: Retrieving product attributes...")
        response = wcapi.get("products/attributes")
        
        if response.status_code == 200:
            attributes = response.json()
            print(f"✓ Found {len(attributes)} global attributes")
            
            if attributes:
                print("\n  Existing Attributes:")
                for i, attr in enumerate(attributes, 1):
                    print(f"    {i}. {attr['name']} (ID: {attr['id']}, Slug: {attr['slug']})")
            else:
                print("  No attributes found (will be created during import)")
        else:
            print(f"✗ Failed with status code: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
        
        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED - API Connection is working correctly!")
        print("="*70)
        print("\nYou can now proceed with the import scripts.")
        return True
        
    except Exception as e:
        print("\n" + "="*70)
        print("✗ CONNECTION FAILED")
        print("="*70)
        print(f"\nError: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Check if WordPress is running (visit the URL in browser)")
        print("  2. Verify WooCommerce plugin is activated")
        print("  3. Confirm API keys are correct (WooCommerce → Settings → Advanced → REST API)")
        print("  4. Check if the URL is accessible from your Python environment")
        return False

if __name__ == "__main__":
    test_connection()
