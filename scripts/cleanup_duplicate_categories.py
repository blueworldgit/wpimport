#!/usr/bin/env python3
"""
Cleanup Duplicate Categories Script
Finds and consolidates duplicate category names in WordPress
"""

import requests
from requests.auth import HTTPBasicAuth
from pathlib import Path
import json
from collections import defaultdict

class CategoryCleaner:
    def __init__(self):
        self.load_credentials()
        self.duplicates_found = {}
        
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
        
    def get_all_categories(self):
        """Get all categories from WordPress"""
        print("📂 Fetching all categories...")
        
        all_categories = []
        page = 1
        
        while True:
            url = f"{self.wp_url}/wp-json/wc/v3/products/categories"
            params = {'per_page': 100, 'page': page}
            
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
                
            all_categories.extend(categories)
            page += 1
            
        print(f"✅ Found {len(all_categories)} total categories")
        return all_categories
        
    def find_duplicates(self, categories):
        """Find categories with duplicate names"""
        print("\n🔍 Analyzing for duplicates...")
        
        category_groups = defaultdict(list)
        
        # Group categories by name
        for cat in categories:
            category_groups[cat['name']].append(cat)
            
        # Find duplicates
        duplicates = {}
        for name, cats in category_groups.items():
            if len(cats) > 1:
                duplicates[name] = cats
                
        print(f"🚨 Found {len(duplicates)} category names with duplicates:")
        
        for name, cats in duplicates.items():
            print(f"\n📂 '{name}' ({len(cats)} copies):")
            for cat in cats:
                print(f"   - ID: {cat['id']}, Parent: {cat['parent']}, Count: {cat['count']}")
                
        return duplicates
        
    def get_products_in_category(self, category_id):
        """Get all products in a specific category"""
        try:
            url = f"{self.wp_url}/wp-json/wc/v3/products"
            params = {'category': category_id, 'per_page': 100}
            
            response = requests.get(
                url,
                params=params,
                auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret),
                timeout=30
            )
            
            if response.status_code == 200:
                products = response.json()
                return [p['id'] for p in products]
            else:
                print(f"⚠️ Error getting products for category {category_id}: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Exception getting products for category {category_id}: {e}")
            return []
            
    def move_products_to_category(self, product_ids, target_category_id):
        """Move products from one category to another"""
        moved_count = 0
        
        for product_id in product_ids:
            try:
                # Get current product
                url = f"{self.wp_url}/wp-json/wc/v3/products/{product_id}"
                response = requests.get(
                    url,
                    auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret),
                    timeout=30
                )
                
                if response.status_code == 200:
                    product = response.json()
                    current_categories = product.get('categories', [])
                    
                    # Add target category if not already present
                    category_ids = [cat['id'] for cat in current_categories]
                    if target_category_id not in category_ids:
                        current_categories.append({'id': target_category_id})
                        
                        # Update product
                        update_data = {'categories': current_categories}
                        update_response = requests.put(
                            url,
                            json=update_data,
                            auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret),
                            timeout=30
                        )
                        
                        if update_response.status_code in [200, 201]:
                            moved_count += 1
                        else:
                            print(f"⚠️ Failed to update product {product_id}")
                            
            except Exception as e:
                print(f"❌ Error moving product {product_id}: {e}")
                
        return moved_count
        
    def delete_empty_category(self, category_id):
        """Delete an empty category"""
        try:
            url = f"{self.wp_url}/wp-json/wc/v3/products/categories/{category_id}"
            params = {'force': True}  # Force delete
            
            response = requests.delete(
                url,
                params=params,
                auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret),
                timeout=30
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Error deleting category {category_id}: {e}")
            return False
            
    def consolidate_duplicates(self, duplicates):
        """Consolidate duplicate categories"""
        print("\n🔧 Consolidating duplicate categories...")
        
        for name, duplicate_categories in duplicates.items():
            print(f"\n📂 Processing '{name}'...")
            
            # Sort by ID to keep the oldest/first one
            duplicate_categories.sort(key=lambda x: x['id'])
            target_category = duplicate_categories[0]  # Keep the first one
            categories_to_remove = duplicate_categories[1:]  # Remove the rest
            
            print(f"   ✅ Keeping category ID {target_category['id']} as primary")
            print(f"   🗑️  Will remove {len(categories_to_remove)} duplicates")
            
            # Move products from duplicate categories to the primary one
            total_moved = 0
            for cat_to_remove in categories_to_remove:
                print(f"   🔄 Moving products from ID {cat_to_remove['id']}...")
                
                # Get products in this category
                product_ids = self.get_products_in_category(cat_to_remove['id'])
                print(f"      Found {len(product_ids)} products to move")
                
                if product_ids:
                    moved = self.move_products_to_category(product_ids, target_category['id'])
                    total_moved += moved
                    print(f"      ✅ Moved {moved} products")
                    
                # Delete the empty duplicate category
                if self.delete_empty_category(cat_to_remove['id']):
                    print(f"      🗑️ Deleted empty category ID {cat_to_remove['id']}")
                else:
                    print(f"      ⚠️ Failed to delete category ID {cat_to_remove['id']}")
                    
            print(f"   ✅ Consolidated '{name}': moved {total_moved} products, kept ID {target_category['id']}")
            
    def cleanup_duplicates(self):
        """Main cleanup process"""
        print("🧹 DUPLICATE CATEGORY CLEANUP")
        print("=" * 50)
        
        # Get all categories
        categories = self.get_all_categories()
        
        # Find duplicates
        duplicates = self.find_duplicates(categories)
        
        if not duplicates:
            print("\n✅ No duplicate categories found!")
            return
            
        print(f"\n⚠️  Found {len(duplicates)} category names with duplicates")
        
        # Ask for confirmation
        response = input("\n🤔 Do you want to proceed with consolidation? (y/N): ")
        if response.lower() != 'y':
            print("❌ Cleanup cancelled")
            return
            
        # Consolidate duplicates
        self.consolidate_duplicates(duplicates)
        
        print("\n✅ Duplicate cleanup completed!")
        
        # Verify results
        print("\n🔍 Verifying cleanup...")
        final_categories = self.get_all_categories()
        final_duplicates = self.find_duplicates(final_categories)
        
        if not final_duplicates:
            print("✅ All duplicates successfully removed!")
        else:
            print(f"⚠️ {len(final_duplicates)} duplicate groups still remain")

def main():
    cleaner = CategoryCleaner()
    cleaner.cleanup_duplicates()

if __name__ == "__main__":
    main()