#!/usr/bin/env python3
"""
Complete WordPress Cleanup Script - Delete all WooCommerce products and empty trash
Use this to start completely fresh before a new import
"""
import sys
from pathlib import Path
from woocommerce import API
import time

# Add parent directory to path for config
base_dir = Path(__file__).parent.parent
sys.path.insert(0, str(base_dir))

from config import WORDPRESS_URL

class WordPressCleaner:
    def __init__(self, wcapi):
        self.wcapi = wcapi
        self.stats = {
            'products_deleted': 0,
            'products_trashed': 0,
            'trash_emptied': 0,
            'categories_deleted': 0,
            'errors': []
        }
    
    def get_all_products(self, status='any'):
        """Get all products with specified status"""
        print(f"📋 Fetching all products (status: {status})...")
        all_products = []
        page = 1
        
        while True:
            response = self.wcapi.get("products", params={
                "per_page": 100, 
                "page": page,
                "status": status
            })
            
            if response.status_code != 200:
                print(f"❌ Error fetching products: {response.status_code}")
                break
            
            products = response.json()
            if not products:
                break
            
            all_products.extend(products)
            print(f"   📄 Page {page}: {len(products)} products")
            page += 1
        
        print(f"✅ Found {len(all_products)} total products")
        return all_products
    
    def get_all_categories(self):
        """Get all product categories"""
        print("📋 Fetching all product categories...")
        all_categories = []
        page = 1
        
        while True:
            response = self.wcapi.get("products/categories", params={
                "per_page": 100, 
                "page": page
            })
            
            if response.status_code != 200:
                print(f"❌ Error fetching categories: {response.status_code}")
                break
            
            categories = response.json()
            if not categories:
                break
            
            all_categories.extend(categories)
            print(f"   📄 Page {page}: {len(categories)} categories")
            page += 1
        
        print(f"✅ Found {len(all_categories)} total categories")
        return all_categories
    
    def delete_products_batch(self, products, force=True):
        """Delete products in batches"""
        if not products:
            return
        
        total = len(products)
        batch_size = 50  # Smaller batches for better reliability
        
        print(f"🗑️  Deleting {total} products (force={force})...")
        
        for i in range(0, total, batch_size):
            batch = products[i:i+batch_size]
            
            try:
                # Prepare batch delete data
                delete_data = [{"id": p["id"], "force": force} for p in batch]
                
                response = self.wcapi.post("products/batch", {
                    "delete": delete_data
                })
                
                if response.status_code == 200:
                    result = response.json()
                    deleted_count = len(result.get('delete', []))
                    
                    if force:
                        self.stats['products_deleted'] += deleted_count
                    else:
                        self.stats['products_trashed'] += deleted_count
                    
                    print(f"   ✅ Batch {i//batch_size + 1}: {deleted_count} products")
                else:
                    print(f"   ❌ Batch {i//batch_size + 1} failed: {response.status_code}")
                    self.stats['errors'].append(f"Batch delete failed: {response.status_code}")
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ Batch {i//batch_size + 1} error: {e}")
                self.stats['errors'].append(f"Batch error: {e}")
    
    def delete_categories_batch(self, categories, force=True):
        """Delete categories in batches"""
        if not categories:
            return
        
        total = len(categories)
        batch_size = 50
        
        print(f"🗑️  Deleting {total} categories...")
        
        # Delete in reverse order (children first) to avoid dependency issues
        categories.reverse()
        
        for i in range(0, total, batch_size):
            batch = categories[i:i+batch_size]
            
            try:
                delete_data = [{"id": c["id"], "force": force} for c in batch]
                
                response = self.wcapi.post("products/categories/batch", {
                    "delete": delete_data
                })
                
                if response.status_code == 200:
                    result = response.json()
                    deleted_count = len(result.get('delete', []))
                    self.stats['categories_deleted'] += deleted_count
                    print(f"   ✅ Batch {i//batch_size + 1}: {deleted_count} categories")
                else:
                    print(f"   ❌ Category batch {i//batch_size + 1} failed: {response.status_code}")
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ Category batch {i//batch_size + 1} error: {e}")
                self.stats['errors'].append(f"Category batch error: {e}")
    
    def clean_lookup_tables(self):
        """Clean WooCommerce lookup tables"""
        print("🧹 Cleaning WooCommerce lookup tables...")
        try:
            # Clear transients
            response = self.wcapi.post("system_status/tools/clear_transients", {})
            if response.status_code == 200:
                print("   ✅ Cleared transients")
            
            # Regenerate product lookup tables
            response = self.wcapi.post("system_status/tools/regenerate_product_lookup_tables", {})
            if response.status_code == 200:
                print("   ✅ Regenerated product lookup tables")
            else:
                print("   ⚠️  Could not auto-regenerate lookup tables")
                print("   💡 Manual fix: Run TRUNCATE TABLE wp_wc_product_meta_lookup; in phpMyAdmin")
                
        except Exception as e:
            print(f"   ❌ Lookup table cleanup error: {e}")
            print("   💡 Manual fix: Run TRUNCATE TABLE wp_wc_product_meta_lookup; in phpMyAdmin")
    
    def complete_cleanup(self, include_categories=False):
        """Perform complete cleanup: products + trash + categories"""
        print("\\n" + "="*70)
        print("🧹 COMPLETE WORDPRESS CLEANUP")
        print("="*70)
        
        # Step 1: Get all products (any status)
        all_products = self.get_all_products(status='any')
        
        if not all_products:
            print("\\n✅ No products found. Store is already clean!")
        else:
            total = len(all_products)
            print(f"\\n⚠️  WARNING: This will PERMANENTLY DELETE ALL {total} products!")
            print("   This includes published, draft, and trashed products.")
            
            if include_categories:
                categories = self.get_all_categories()
                if categories:
                    print(f"   Also deleting {len(categories)} product categories.")
            
            confirm = input("\\nType 'DELETE EVERYTHING' to confirm: ")
            
            if confirm != 'DELETE EVERYTHING':
                print("\\n❌ Cancelled. Nothing was deleted.")
                return
            
            # Step 2: Force delete all products (bypasses trash)
            self.delete_products_batch(all_products, force=True)
            
            # Step 3: Delete categories if requested
            if include_categories:
                categories = self.get_all_categories()
                if categories:
                    self.delete_categories_batch(categories, force=True)
            
            # Step 4: Clean lookup tables
            self.clean_lookup_tables()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print cleanup summary"""
        print("\\n" + "="*70)
        print("🧹 CLEANUP SUMMARY")
        print("="*70)
        print(f"Products deleted:     {self.stats['products_deleted']}")
        print(f"Products trashed:     {self.stats['products_trashed']}")
        print(f"Categories deleted:   {self.stats['categories_deleted']}")
        print(f"Errors:               {len(self.stats['errors'])}")
        print("="*70)
        
        if self.stats['errors']:
            print("\\n❌ Errors encountered:")
            for error in self.stats['errors'][:10]:
                print(f"   - {error}")
            if len(self.stats['errors']) > 10:
                print(f"   ... and {len(self.stats['errors']) - 10} more")
        
        if len(self.stats['errors']) == 0:
            print("\\n✅ CLEANUP COMPLETE! WordPress is ready for fresh import.")
            print("\\n📝 Next steps:")
            print("   1. Run your clearloader.py script")
            print("   2. Import new products")
            print("   3. Update prices")
        else:
            print("\\n⚠️  Some errors occurred. Manual cleanup may be needed.")

def main():
    """Main cleanup function"""
    
    # Load API keys
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
            print("❌ API keys not found in keys.txt")
            return
            
    except Exception as e:
        print(f"❌ Could not load API keys: {e}")
        return
    
    # Initialize WooCommerce API
    wcapi = API(
        url=WORDPRESS_URL,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        version="wc/v3",
        timeout=60
    )
    
    # Test connection
    try:
        response = wcapi.get("products", params={"per_page": 1})
        if response.status_code != 200:
            print(f"❌ API connection failed: {response.status_code}")
            return
        print("✅ WooCommerce API connection successful")
    except Exception as e:
        print(f"❌ API connection error: {e}")
        return
    
    # Ask about categories
    print("\\n🤔 Options:")
    print("   1. Delete products only")
    print("   2. Delete products AND categories (complete reset)")
    
    choice = input("\\nEnter choice (1 or 2): ").strip()
    include_categories = choice == '2'
    
    if include_categories:
        print("\\n⚠️  Selected: Complete reset (products + categories)")
    else:
        print("\\n🎯 Selected: Products only")
    
    # Run cleanup
    cleaner = WordPressCleaner(wcapi)
    cleaner.complete_cleanup(include_categories=include_categories)

if __name__ == "__main__":
    main()