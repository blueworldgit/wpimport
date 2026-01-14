#!/usr/bin/env python3
"""
WordPress Complete Cleanup Script
Removes ALL products and categories to start fresh
"""

import requests
from requests.auth import HTTPBasicAuth
from pathlib import Path
import time

class WordPressCleaner:
    def __init__(self):
        self.load_credentials()
        
    def load_credentials(self):
        """Load API credentials"""
        base_dir = Path(__file__).parent.parent
        
        # Load keys
        keys_file = base_dir / 'keys.txt'
        with open(keys_file, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            
        # Parse keys file format
        self.consumer_key = None
        self.consumer_secret = None
        for i, line in enumerate(lines):
            if 'Consumer key' in line and i + 1 < len(lines):
                self.consumer_key = lines[i + 1]
            elif 'Consumer secret' in line and i + 1 < len(lines):
                self.consumer_secret = lines[i + 1]
        
        self.wp_url = "https://maxusvanparts.co.uk"
        
    def delete_all_products(self):
        """Delete all products from WordPress"""
        print("🗑️ Deleting ALL products...")
        
        deleted_count = 0
        page = 1
        
        while True:
            # Get products
            url = f"{self.wp_url}/wp-json/wc/v3/products"
            params = {'per_page': 100, 'page': 1}  # Always get page 1 since we're deleting
            
            response = requests.get(
                url,
                params=params,
                auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret),
                timeout=30
            )
            
            if response.status_code != 200:
                break
                
            products = response.json()
            if not products:
                break
            
            print(f"   Deleting batch of {len(products)} products...")
            
            # Delete each product
            for product in products:
                try:
                    delete_url = f"{self.wp_url}/wp-json/wc/v3/products/{product['id']}"
                    delete_response = requests.delete(
                        delete_url,
                        params={'force': True},  # Force delete
                        auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret),
                        timeout=30
                    )
                    
                    if delete_response.status_code == 200:
                        deleted_count += 1
                        if deleted_count % 50 == 0:
                            print(f"   Progress: {deleted_count} products deleted...")
                    else:
                        print(f"   ⚠️ Failed to delete product {product['id']}: {delete_response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Error deleting product {product['id']}: {e}")
                    
                # Rate limiting
                time.sleep(0.1)
                
        print(f"✅ Deleted {deleted_count} products total")
        return deleted_count
        
    def delete_all_categories(self):
        """Delete all custom categories (keep default WooCommerce ones)"""
        print("\n🗑️ Deleting ALL custom categories...")
        
        deleted_count = 0
        
        # Keep trying until no more categories to delete
        while True:
            # Get categories
            url = f"{self.wp_url}/wp-json/wc/v3/products/categories"
            params = {'per_page': 100, 'page': 1}
            
            response = requests.get(
                url,
                params=params,
                auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret),
                timeout=30
            )
            
            if response.status_code != 200:
                break
                
            categories = response.json()
            if not categories:
                break
                
            # Filter out default WooCommerce categories
            custom_categories = []
            default_cats = ['Uncategorized', 'uncategorized']
            
            for cat in categories:
                if cat['name'] not in default_cats and cat['id'] != 15:  # 15 is usually Uncategorized
                    custom_categories.append(cat)
                    
            if not custom_categories:
                break
                
            print(f"   Deleting batch of {len(custom_categories)} categories...")
            
            batch_deleted = 0
            # Delete each category
            for category in custom_categories:
                try:
                    delete_url = f"{self.wp_url}/wp-json/wc/v3/products/categories/{category['id']}"
                    delete_response = requests.delete(
                        delete_url,
                        params={'force': True},  # Force delete
                        auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret),
                        timeout=30
                    )
                    
                    if delete_response.status_code == 200:
                        deleted_count += 1
                        batch_deleted += 1
                    else:
                        print(f"   ⚠️ Failed to delete category {category['name']} (ID: {category['id']}): {delete_response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Error deleting category {category['name']}: {e}")
                    
                # Rate limiting
                time.sleep(0.1)
                
            if batch_deleted == 0:
                # No categories were deleted in this batch, probably due to dependencies
                print("   ⚠️ No more categories can be deleted (may have dependencies)")
                break
                
        print(f"✅ Deleted {deleted_count} categories total")
        return deleted_count
        
    def clean_media_library(self):
        """Optional: Clean up uploaded images"""
        print("\n📷 Checking media library...")
        
        try:
            # Use WordPress credentials for media endpoint
            creds_file = Path('productioncreds.txt')
            with open(creds_file, 'r') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
                wp_user = lines[4]  # developer
                wp_pass = lines[5]  # app password
            
            url = f"{self.wp_url}/wp-json/wp/v2/media"
            params = {'per_page': 10}
            
            response = requests.get(
                url,
                params=params,
                auth=HTTPBasicAuth(wp_user, wp_pass),
                timeout=30
            )
            
            if response.status_code == 200:
                media = response.json()
                print(f"   Found {len(media)} recent media files")
                print("   ℹ️  Media cleanup not included - do manually if needed")
            else:
                print(f"   ⚠️ Could not access media library: {response.status_code}")
                
        except Exception as e:
            print(f"   ⚠️ Media check failed: {e}")
            
    def complete_cleanup(self):
        """Perform complete WordPress cleanup"""
        print("🧹 COMPLETE WORDPRESS CLEANUP")
        print("=" * 50)
        print("⚠️  WARNING: This will delete ALL products and categories!")
        print("🎯 This will give you a clean slate for fresh import")
        
        # Confirmation
        response = input("\n🤔 Are you sure you want to delete EVERYTHING? (type 'YES' to confirm): ")
        if response != 'YES':
            print("❌ Cleanup cancelled")
            return
            
        print("\n🚀 Starting complete cleanup...")
        
        # Step 1: Delete all products first (removes category dependencies)
        products_deleted = self.delete_all_products()
        
        # Step 2: Delete all categories
        categories_deleted = self.delete_all_categories()
        
        # Step 3: Check media
        self.clean_media_library()
        
        print(f"\n✅ CLEANUP COMPLETED!")
        print(f"   🗑️ Deleted {products_deleted} products")
        print(f"   🗑️ Deleted {categories_deleted} categories")
        print(f"\n🎉 WordPress is now clean and ready for fresh import!")
        
        # Clear local checkpoint
        print(f"\n🧹 Clearing local checkpoint...")
        try:
            checkpoint_file = Path('data/checkpoints/import_checkpoint.json')
            if checkpoint_file.exists():
                checkpoint_file.unlink()
                print(f"   ✅ Cleared checkpoint file")
        except Exception as e:
            print(f"   ⚠️ Could not clear checkpoint: {e}")

def main():
    cleaner = WordPressCleaner()
    cleaner.complete_cleanup()

if __name__ == "__main__":
    main()