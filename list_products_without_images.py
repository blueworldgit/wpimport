#!/usr/bin/env python3
"""
Script to connect to WordPress and list all products without images
"""

import requests
import json
import sys
import os
from pathlib import Path

# Add scripts directory to path to import utilities
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
from upload_missing_images_optimized import get_wp_auth

def load_config():
    """Load configuration from config.py"""
    with open('config.py', 'r') as f:
        config_content = f.read()
        config = {}
        exec(config_content, config)
    return config

def get_all_products(wordpress_url, auth, per_page=100):
    """Fetch all products from WooCommerce API"""
    all_products = []
    page = 1
    
    print("📡 Fetching products from WordPress/WooCommerce...")
    
    while True:
        try:
            response = requests.get(
                f"{wordpress_url}/wp-json/wc/v3/products",
                params={
                    'per_page': per_page, 
                    'page': page,
                    'status': 'publish'  # Only published products
                },
                auth=auth,
                timeout=30
            )
            
            if response.status_code == 200:
                products = response.json()
                if not products:  # No more products
                    break
                
                all_products.extend(products)
                print(f"   📦 Fetched page {page}: {len(products)} products (Total: {len(all_products)})")
                page += 1
                
            elif response.status_code == 400:
                # Page doesn't exist - we've reached the end
                break
            else:
                print(f"❌ Error fetching products page {page}: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                break
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            break
    
    return all_products

def find_products_without_images(products):
    """Identify products that don't have any images"""
    products_without_images = []
    
    print(f"\n🔍 Analyzing {len(products)} products for images...")
    
    for product in products:
        product_id = product.get('id', 'Unknown')
        sku = product.get('sku', 'NO_SKU')
        name = product.get('name', 'NO_NAME')
        images = product.get('images', [])
        
        # Check if product has any images
        if not images or len(images) == 0:
            products_without_images.append({
                'id': product_id,
                'sku': sku,
                'name': name,
                'permalink': product.get('permalink', ''),
                'status': product.get('status', 'unknown')
            })
    
    return products_without_images

def output_results(products_without_images, total_products):
    """Output the results in a clear format"""
    
    print(f"\n{'='*80}")
    print(f"📊 PRODUCTS WITHOUT IMAGES REPORT")
    print(f"{'='*80}")
    
    print(f"📈 Total products analyzed: {total_products}")
    print(f"🖼️  Products with images: {total_products - len(products_without_images)}")
    print(f"❌ Products WITHOUT images: {len(products_without_images)}")
    
    if len(products_without_images) > 0:
        percentage = (len(products_without_images) / total_products) * 100
        print(f"📊 Percentage without images: {percentage:.1f}%")
        
        print(f"\n🔍 DETAILED LIST OF PRODUCTS WITHOUT IMAGES:")
        print(f"{'-'*80}")
        
        for i, product in enumerate(products_without_images, 1):
            print(f"{i:3d}. ID: {product['id']:<6} | SKU: {product['sku']:<20} | {product['name'][:40]}")
            if product['permalink']:
                print(f"      🔗 {product['permalink']}")
        
        # Save to file for easy review
        output_file = "products_without_images.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(products_without_images, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
    else:
        print(f"\n🎉 All products have images!")

def main():
    """Main function"""
    try:
        print("🚀 WordPress Products Without Images Analyzer")
        print("=" * 50)
        
        # Load configuration
        config = load_config()
        wordpress_url = config['WORDPRESS_URL']
        print(f"🌐 WordPress URL: {wordpress_url}")
        
        # Get authentication credentials
        try:
            wp_username, wp_app_password = get_wp_auth()
            print(f"🔐 Authentication: ✅ ({wp_username})")
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return
        
        # Fetch all products
        all_products = get_all_products(wordpress_url, (wp_username, wp_app_password))
        
        if not all_products:
            print("❌ No products found or unable to fetch products")
            return
        
        # Find products without images
        products_without_images = find_products_without_images(all_products)
        
        # Output results
        output_results(products_without_images, len(all_products))
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()