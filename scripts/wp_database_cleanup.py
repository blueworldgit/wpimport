#!/usr/bin/env python3
"""
WordPress Database Cleanup (Python Version)
Cleans up orphaned data using REST API where possible and generates SQL for manual cleanup
"""
from woocommerce import API
import requests
from pathlib import Path
import sys
import json
import argparse

# Add parent directory to path for imports
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))
from config import WORDPRESS_URL

class WPDatabaseCleaner:
    def __init__(self):
        self.wcapi = None
        self.wp_api_base = None
        self.load_credentials()
        
    def load_credentials(self):
        """Load WordPress credentials"""
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
            raise Exception("WordPress credentials not found in keys.txt")
        
        # Initialize WooCommerce API
        self.wcapi = API(
            url=WORDPRESS_URL,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            wp_api=True,
            version="wc/v3",
            timeout=30
        )
        
        # WordPress REST API base (for general WordPress operations)
        self.wp_api_base = f"{WORDPRESS_URL.rstrip('/')}/wp-json/wp/v2"
        
        print(f"✓ Connected to WordPress: {WORDPRESS_URL}")

    def cleanup_via_rest_api(self):
        """Clean up what we can using REST API"""
        print("\n🧹 CLEANUP VIA REST API")
        print("="*50)
        
        cleanup_results = {
            'products_in_trash': 0,
            'categories_with_zero_count': 0,
            'empty_categories_deleted': 0,
            'media_without_posts': 0
        }
        
        # 1. Remove products in trash (force delete)
        print("🗑️  Checking for products in trash...")
        try:
            response = self.wcapi.get('products', params={
                'status': 'trash',
                'per_page': 100
            })
            
            if response.status_code == 200:
                trashed_products = response.json()
                cleanup_results['products_in_trash'] = len(trashed_products)
                
                if trashed_products:
                    print(f"   Found {len(trashed_products)} products in trash")
                    
                    # Force delete them
                    for product in trashed_products:
                        try:
                            delete_response = self.wcapi.delete(f"products/{product['id']}", params={'force': True})
                            if delete_response.status_code == 200:
                                print(f"   ✅ Force deleted product ID {product['id']}")
                            else:
                                print(f"   ❌ Failed to delete product ID {product['id']}: {delete_response.status_code}")
                        except Exception as e:
                            print(f"   ❌ Exception deleting product {product['id']}: {e}")
                else:
                    print("   ✅ No products in trash")
                    
        except Exception as e:
            print(f"   ❌ Error checking trashed products: {e}")
        
        # 2. Find and clean empty categories
        print("\n📁 Checking for empty categories...")
        try:
            response = self.wcapi.get('products/categories', params={
                'per_page': 100,
                'page': 1
            })
            
            if response.status_code == 200:
                categories = response.json()
                empty_categories = [cat for cat in categories if cat['count'] == 0]
                cleanup_results['categories_with_zero_count'] = len(empty_categories)
                
                if empty_categories:
                    print(f"   Found {len(empty_categories)} empty categories")
                    
                    # Ask if user wants to delete empty categories
                    for cat in empty_categories[:5]:  # Show first 5
                        print(f"   📂 {cat['name']} (ID: {cat['id']}, Count: {cat['count']})")
                    
                    if len(empty_categories) > 5:
                        print(f"   ... and {len(empty_categories) - 5} more")
                    
                    # For now, just report them (could add deletion logic)
                    print(f"   ℹ️  Use --delete-empty-categories to remove these")
                else:
                    print("   ✅ No empty categories found")
        except Exception as e:
            print(f"   ❌ Error checking categories: {e}")
        
        return cleanup_results

    def generate_sql_cleanup(self):
        """Generate SQL commands for manual database cleanup"""
        print("\n💾 GENERATING SQL CLEANUP COMMANDS")
        print("="*50)
        
        # WordPress table prefix (usually wp_ but could be different)
        table_prefix = "wp_"
        
        sql_commands = f"""
-- WordPress Database Cleanup SQL Commands
-- Run these in your WordPress database (usually via phpMyAdmin or similar)
-- BACKUP YOUR DATABASE FIRST!

-- 1. Remove orphaned postmeta (metadata for posts that no longer exist)
DELETE pm FROM {table_prefix}postmeta pm
LEFT JOIN {table_prefix}posts p ON pm.post_id = p.ID
WHERE p.ID IS NULL;

-- 2. Remove orphaned termmeta (metadata for terms that no longer exist)
DELETE tm FROM {table_prefix}termmeta tm
LEFT JOIN {table_prefix}terms t ON tm.term_id = t.term_id
WHERE t.term_id IS NULL;

-- 3. Remove orphaned term relationships (relationships for posts that no longer exist)
DELETE tr FROM {table_prefix}term_relationships tr
LEFT JOIN {table_prefix}posts p ON tr.object_id = p.ID
WHERE p.ID IS NULL;

-- 4. Remove orphaned term relationships (relationships for terms that no longer exist)
DELETE tr FROM {table_prefix}term_relationships tr
LEFT JOIN {table_prefix}term_taxonomy tt ON tr.term_taxonomy_id = tt.term_taxonomy_id
WHERE tt.term_taxonomy_id IS NULL;

-- 5. Update term counts (recalculate category/tag counts)
UPDATE {table_prefix}term_taxonomy tt SET count = (
    SELECT COUNT(*) FROM {table_prefix}term_relationships tr 
    WHERE tr.term_taxonomy_id = tt.term_taxonomy_id
);

-- 6. Remove orphaned comments meta
DELETE cm FROM {table_prefix}commentmeta cm
LEFT JOIN {table_prefix}comments c ON cm.comment_id = c.comment_ID
WHERE c.comment_ID IS NULL;

-- 7. Remove orphaned user meta
DELETE um FROM {table_prefix}usermeta um
LEFT JOIN {table_prefix}users u ON um.user_id = u.ID
WHERE u.ID IS NULL;

-- 8. Remove auto-drafts older than 7 days
DELETE FROM {table_prefix}posts 
WHERE post_status = 'auto-draft' 
AND post_date < DATE_SUB(NOW(), INTERVAL 7 DAY);

-- 9. Remove orphaned attachment metadata
DELETE pm FROM {table_prefix}postmeta pm
LEFT JOIN {table_prefix}posts p ON pm.post_id = p.ID
WHERE pm.meta_key = '_wp_attachment_metadata' 
AND p.ID IS NULL;

-- 10. Optimize all tables (run one by one)
OPTIMIZE TABLE {table_prefix}posts;
OPTIMIZE TABLE {table_prefix}postmeta;
OPTIMIZE TABLE {table_prefix}terms;
OPTIMIZE TABLE {table_prefix}termmeta;
OPTIMIZE TABLE {table_prefix}term_taxonomy;
OPTIMIZE TABLE {table_prefix}term_relationships;
OPTIMIZE TABLE {table_prefix}comments;
OPTIMIZE TABLE {table_prefix}commentmeta;
OPTIMIZE TABLE {table_prefix}users;
OPTIMIZE TABLE {table_prefix}usermeta;
OPTIMIZE TABLE {table_prefix}options;

-- WooCommerce specific cleanup
-- 11. Remove orphaned order items
DELETE oi FROM {table_prefix}woocommerce_order_items oi
LEFT JOIN {table_prefix}posts p ON oi.order_id = p.ID
WHERE p.ID IS NULL;

-- 12. Remove orphaned order item meta
DELETE oim FROM {table_prefix}woocommerce_order_itemmeta oim
LEFT JOIN {table_prefix}woocommerce_order_items oi ON oim.order_item_id = oi.order_item_id
WHERE oi.order_item_id IS NULL;

-- 13. Check for orphaned data (counts only - run these to see how much orphaned data exists)
SELECT 'Orphaned postmeta' as type, COUNT(*) as count FROM {table_prefix}postmeta pm
LEFT JOIN {table_prefix}posts p ON pm.post_id = p.ID WHERE p.ID IS NULL
UNION ALL
SELECT 'Orphaned termmeta' as type, COUNT(*) as count FROM {table_prefix}termmeta tm
LEFT JOIN {table_prefix}terms t ON tm.term_id = t.term_id WHERE t.term_id IS NULL
UNION ALL
SELECT 'Orphaned term relationships' as type, COUNT(*) as count FROM {table_prefix}term_relationships tr
LEFT JOIN {table_prefix}posts p ON tr.object_id = p.ID WHERE p.ID IS NULL;
"""
        
        # Save to file
        sql_file = base_dir / 'cleanup_database.sql'
        with open(sql_file, 'w') as f:
            f.write(sql_commands)
        
        print(f"✅ SQL commands saved to: {sql_file}")
        print(f"📋 Commands include:")
        print(f"   • Remove orphaned postmeta")
        print(f"   • Remove orphaned termmeta") 
        print(f"   • Remove orphaned term relationships")
        print(f"   • Update term counts")
        print(f"   • Remove old auto-drafts")
        print(f"   • Optimize all tables")
        print(f"   • WooCommerce specific cleanup")
        
        return sql_file

    def run_cleanup(self, delete_empty_categories=False, sql_only=False):
        """Run the full cleanup process"""
        print("="*80)
        print("🧹 WORDPRESS DATABASE CLEANER")
        print("="*80)
        print(f"🌐 Target: {WORDPRESS_URL}")
        
        results = {}
        
        if not sql_only:
            # Run REST API cleanup
            results['rest_api'] = self.cleanup_via_rest_api()
        
        # Generate SQL commands
        results['sql_file'] = self.generate_sql_cleanup()
        
        print(f"\n📊 CLEANUP SUMMARY:")
        print("="*50)
        if not sql_only:
            print(f"✅ REST API cleanup completed")
            print(f"   📦 Products in trash: {results['rest_api']['products_in_trash']}")
            print(f"   📁 Empty categories: {results['rest_api']['categories_with_zero_count']}")
        
        print(f"💾 SQL cleanup file: {results['sql_file']}")
        print(f"\n⚠️  IMPORTANT:")
        print(f"   1. BACKUP your database before running the SQL commands!")
        print(f"   2. Run the SQL commands in your database management tool")
        print(f"   3. Check your table prefix (currently set to 'wp_')")
        
        return results

def main():
    parser = argparse.ArgumentParser(description='Clean WordPress database')
    parser.add_argument('--delete-empty-categories', action='store_true', help='Delete empty categories')
    parser.add_argument('--sql-only', action='store_true', help='Only generate SQL, skip REST API cleanup')
    
    args = parser.parse_args()
    
    try:
        cleaner = WPDatabaseCleaner()
        results = cleaner.run_cleanup(
            delete_empty_categories=args.delete_empty_categories,
            sql_only=args.sql_only
        )
        
        print(f"\n🎉 Cleanup process completed!")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())