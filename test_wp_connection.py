#!/usr/bin/env python3
"""
Quick test script to verify WordPress/WooCommerce API connections
"""
import sys
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth

# Add parent directory to path
base_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(base_dir))

from config import WORDPRESS_URL

def load_woocommerce_creds():
    """Load WooCommerce API credentials from keys.txt"""
    keys_file = base_dir / 'keys.txt'
    with open(keys_file, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    
    consumer_key = None
    consumer_secret = None
    
    for i, line in enumerate(lines):
        if 'Consumer key' in line and i+1 < len(lines): 
            consumer_key = lines[i+1]
        if 'Consumer secret' in line and i+1 < len(lines): 
            consumer_secret = lines[i+1]
    
    return consumer_key, consumer_secret

def load_wordpress_creds():
    """Load WordPress REST API credentials from productioncreds.txt"""
    creds_file = base_dir / 'productioncreds.txt'
    with open(creds_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    wp_username = None
    wp_app_password = None
    
    for i, line in enumerate(lines):
        if line == "developer":
            wp_username = line
            for j in range(i+1, min(len(lines), i+4)):
                if ' ' in lines[j] and len(lines[j]) > 20:
                    wp_app_password = lines[j]
                    break
            break
    
    return wp_username, wp_app_password

def test_woocommerce_api():
    """Test WooCommerce API connection"""
    print("\n" + "="*60)
    print("Testing WooCommerce API Connection")
    print("="*60)
    
    try:
        consumer_key, consumer_secret = load_woocommerce_creds()
        print(f"URL: {WORDPRESS_URL}")
        print(f"Consumer Key: {consumer_key[:20]}...")
        print(f"Consumer Secret: {consumer_secret[:20]}...")
        
        # Test connection by getting system status
        url = f"{WORDPRESS_URL}/wp-json/wc/v3/system_status"
        response = requests.get(
            url,
            auth=(consumer_key, consumer_secret),
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ WooCommerce API: Connected successfully!")
            data = response.json()
            print(f"   WooCommerce Version: {data.get('environment', {}).get('version', 'Unknown')}")
            print(f"   WordPress Version: {data.get('environment', {}).get('wp_version', 'Unknown')}")
            return True
        else:
            print(f"❌ WooCommerce API: Failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ WooCommerce API: Error - {e}")
        return False

def test_wordpress_rest_api():
    """Test WordPress REST API connection (used for media uploads)"""
    print("\n" + "="*60)
    print("Testing WordPress REST API Connection")
    print("="*60)
    
    try:
        wp_username, wp_app_password = load_wordpress_creds()
        print(f"URL: {WORDPRESS_URL}")
        print(f"Username: {wp_username}")
        print(f"App Password: {wp_app_password[:20]}...")
        
        # Test connection by getting current user
        url = f"{WORDPRESS_URL}/wp-json/wp/v2/users/me"
        response = requests.get(
            url,
            auth=HTTPBasicAuth(wp_username, wp_app_password),
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ WordPress REST API: Connected successfully!")
            data = response.json()
            print(f"   User: {data.get('name', 'Unknown')}")
            print(f"   Roles: {', '.join(data.get('roles', []))}")
            
            # Check if user can upload media
            capabilities = data.get('capabilities', {})
            can_upload = capabilities.get('upload_files', False)
            print(f"   Can upload files: {'✅ Yes' if can_upload else '❌ No'}")
            return True
        else:
            print(f"❌ WordPress REST API: Failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ WordPress REST API: Error - {e}")
        return False

def test_product_fetch():
    """Test fetching a product"""
    print("\n" + "="*60)
    print("Testing Product Fetch")
    print("="*60)
    
    try:
        consumer_key, consumer_secret = load_woocommerce_creds()
        
        # Get one product
        url = f"{WORDPRESS_URL}/wp-json/wc/v3/products"
        response = requests.get(
            url,
            auth=(consumer_key, consumer_secret),
            params={'per_page': 1},
            timeout=10
        )
        
        if response.status_code == 200:
            products = response.json()
            if products:
                product = products[0]
                print("✅ Product Fetch: Success!")
                print(f"   Sample Product ID: {product.get('id')}")
                print(f"   Name: {product.get('name', 'N/A')[:50]}")
                print(f"   SKU: {product.get('sku', 'N/A')}")
                print(f"   Images: {len(product.get('images', []))}")
                return True
            else:
                print("⚠️  Product Fetch: No products found in store")
                return True
        else:
            print(f"❌ Product Fetch: Failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Product Fetch: Error - {e}")
        return False

def main():
    print("\n🔌 WordPress/WooCommerce API Connection Test")
    print("="*60)
    
    results = {
        'woocommerce': test_woocommerce_api(),
        'wordpress_rest': test_wordpress_rest_api(),
        'product_fetch': test_product_fetch()
    }
    
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ All tests passed! Connection is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())
