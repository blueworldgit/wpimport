#!/usr/bin/env python3
"""
WordPress Site Cleaner
Completely removes all products and categories from WooCommerce site
WARNING: This is destructive and irreversible!
"""
from woocommerce import API
from pathlib import Path
import sys
import argparse
import time

# Add parent directory to path for imports
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))
from config import WORDPRESS_URL

class WPCleaner:
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

    def get_all_products(self):
        """Get all product IDs"""
        print("🔍 Fetching all products...")
        
        page = 1
        per_page = 100
        all_products = []
        
        while True:
            try:
                response = self.wcapi.get('products', params={
                    'page': page,
                    'per_page': per_page,
                    'status': 'any'  # Include all statuses
                })
                
                if response.status_code == 200:
                    products = response.json()
                    if not products:
                        break
                    
                    all_products.extend(products)
                    print(f"   📄 Page {page}: {len(products)} products")
                    page += 1
                    
                    # Safety limit
                    if page > 200:  # Max 20,000 products
                        print("⚠️  Reached safety limit of 20,000 products")
                        break
                else:
                    print(f"❌ Error fetching products: {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"❌ Exception: {e}")
                break
        
        print(f"✓ Found {len(all_products)} products total")
        return all_products

    def get_all_categories(self):
        """Get all category IDs"""
        print("🔍 Fetching all categories...")
        
        page = 1
        per_page = 100
        all_categories = []
        
        while True:
            try:
                response = self.wcapi.get('products/categories', params={
                    'page': page,
                    'per_page': per_page,
                    'orderby': 'id',
                    'order': 'desc'  # Get newest first
                })
                
                if response.status_code == 200:
                    categories = response.json()
                    if not categories:
                        break
                    
                    all_categories.extend(categories)
                    print(f"   📄 Page {page}: {len(categories)} categories")
                    page += 1
                    
                    # Safety limit
                    if page > 50:  # Max 5,000 categories
                        print("⚠️  Reached safety limit of 5,000 categories")
                        break
                else:
                    print(f"❌ Error fetching categories: {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"❌ Exception: {e}")
                break
        
        print(f"✓ Found {len(all_categories)} categories total")
        return all_categories

    def delete_products(self, products, batch_size=20):
        """Delete all products"""
        if not products:
            print("ℹ️  No products to delete")
            return True
        
        print(f"\n🗑️  Deleting {len(products)} products...")
        
        # Delete in batches using batch API
        total_deleted = 0
        failed_deletions = []
        
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            batch_ids = [{'id': p['id'], 'force': True} for p in batch]
            
            try:
                response = self.wcapi.post('products/batch', {
                    'delete': batch_ids
                })
                
                if response.status_code == 200:
                    result = response.json()
                    deleted_count = len(result.get('delete', []))
                    total_deleted += deleted_count
                    print(f"   ✅ Batch {i//batch_size + 1}: Deleted {deleted_count} products")
                else:
                    print(f"   ❌ Batch {i//batch_size + 1}: Error {response.status_code}")
                    failed_deletions.extend([p['id'] for p in batch])
                
                # Small delay to avoid overwhelming the server
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ Batch {i//batch_size + 1}: Exception {e}")
                failed_deletions.extend([p['id'] for p in batch])
        
        print(f"✅ Successfully deleted {total_deleted} products")
        if failed_deletions:
            print(f"❌ Failed to delete {len(failed_deletions)} products")
        
        return len(failed_deletions) == 0

    def delete_categories(self, categories, batch_size=20):
        """Delete all categories (children first, then parents)"""
        if not categories:
            print("ℹ️  No categories to delete")
            return True
        
        print(f"\n🗑️  Deleting {len(categories)} categories...")
        
        # Sort categories: children first (higher parent IDs), then parents (parent=0)
        # This ensures we delete child categories before their parents
        sorted_categories = sorted(categories, key=lambda x: (-x['parent'], -x['id']))
        
        total_deleted = 0
        failed_deletions = []
        
        # Delete in batches
        for i in range(0, len(sorted_categories), batch_size):
            batch = sorted_categories[i:i + batch_size]
            batch_ids = [{'id': c['id'], 'force': True} for c in batch]
            
            try:
                response = self.wcapi.post('products/categories/batch', {
                    'delete': batch_ids
                })
                
                if response.status_code == 200:
                    result = response.json()
                    deleted_count = len(result.get('delete', []))
                    total_deleted += deleted_count
                    print(f"   ✅ Batch {i//batch_size + 1}: Deleted {deleted_count} categories")
                else:
                    print(f"   ❌ Batch {i//batch_size + 1}: Error {response.status_code}")
                    # Try individual deletion for failed batch
                    for cat in batch:
                        try:
                            individual_response = self.wcapi.delete(f"products/categories/{cat['id']}", params={'force': True})
                            if individual_response.status_code == 200:
                                total_deleted += 1
                            else:
                                failed_deletions.append(cat['id'])
                        except:
                            failed_deletions.append(cat['id'])
                
                # Small delay
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ Batch {i//batch_size + 1}: Exception {e}")
                # Try individual deletion
                for cat in batch:
                    try:
                        individual_response = self.wcapi.delete(f"products/categories/{cat['id']}", params={'force': True})
                        if individual_response.status_code == 200:
                            total_deleted += 1
                        else:
                            failed_deletions.append(cat['id'])
                    except:
                        failed_deletions.append(cat['id'])
        
        print(f"✅ Successfully deleted {total_deleted} categories")
        if failed_deletions:
            print(f"❌ Failed to delete {len(failed_deletions)} categories")
        
        return len(failed_deletions) == 0

    def clean_site(self, products_only=False, categories_only=False):
        """Clean the entire site"""
        print("="*80)
        print("🧹 WORDPRESS SITE CLEANER")
        print("="*80)
        print(f"🌐 Target: {WORDPRESS_URL}")
        
        # Get current counts
        if not categories_only:
            products = self.get_all_products()
        else:
            products = []
        
        if not products_only:
            categories = self.get_all_categories()
        else:
            categories = []
        
        total_items = len(products) + len(categories)
        
        if total_items == 0:
            print("\n✅ Site is already clean! No products or categories found.")
            return True
        
        print(f"\n📊 ITEMS TO DELETE:")
        print(f"   📦 Products: {len(products)}")
        print(f"   📁 Categories: {len(categories)}")
        print(f"   🎯 Total: {total_items}")
        
        # Final confirmation
        print(f"\n⚠️  WARNING: This will PERMANENTLY DELETE all items from {WORDPRESS_URL}")
        print("⚠️  This action CANNOT BE UNDONE!")
        
        confirm = input("\n❓ Type 'DELETE EVERYTHING' to confirm: ")
        if confirm != 'DELETE EVERYTHING':
            print("❌ Deletion cancelled.")
            return False
        
        print("\n🚀 Starting deletion process...")
        
        success = True
        
        # Delete products first (they depend on categories)
        if products:
            success &= self.delete_products(products)
        
        # Then delete categories
        if categories:
            success &= self.delete_categories(categories)
        
        if success:
            print(f"\n🎉 SUCCESS: Site cleaned successfully!")
            print(f"   📦 Products deleted: {len(products)}")
            print(f"   📁 Categories deleted: {len(categories)}")
        else:
            print(f"\n⚠️  PARTIAL SUCCESS: Some items may not have been deleted")
        
        return success

def main():
    parser = argparse.ArgumentParser(description='Clean WordPress/WooCommerce site')
    parser.add_argument('--products-only', action='store_true', help='Delete only products')
    parser.add_argument('--categories-only', action='store_true', help='Delete only categories')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompts')
    
    args = parser.parse_args()
    
    if args.products_only and args.categories_only:
        print("❌ Cannot use both --products-only and --categories-only")
        return 1
    
    try:
        cleaner = WPCleaner()
        
        # Override confirmation if --force is used
        if args.force:
            print("⚠️  FORCE MODE: Skipping confirmations")
            # Monkey patch input to always return the confirmation
            import builtins
            original_input = builtins.input
            builtins.input = lambda prompt: 'DELETE EVERYTHING' if 'DELETE EVERYTHING' in prompt else 'y'
        
        success = cleaner.clean_site(
            products_only=args.products_only,
            categories_only=args.categories_only
        )
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())