#!/usr/bin/env python3
"""
WordPress Serial Analyzer
Analyzes WooCommerce categories and products for a specific serial number
"""
from woocommerce import API
from pathlib import Path
import sys
import argparse
from collections import defaultdict
import re

# Add parent directory to path for imports
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))
from config import WORDPRESS_URL

class WPSerialAnalyzer:
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

    def fetch_all_categories(self):
        """Fetch all categories from WooCommerce"""
        print("🔍 Fetching categories...")
        
        page = 1
        per_page = 100
        all_categories = []
        
        while True:
            try:
                response = self.wcapi.get('products/categories', params={
                    'page': page,
                    'per_page': per_page,
                    'orderby': 'name',
                    'order': 'asc'
                })
                
                if response.status_code == 200:
                    categories = response.json()
                    if not categories:
                        break
                    
                    all_categories.extend(categories)
                    page += 1
                    
                    # Limit to avoid too many API calls
                    if page > 20:  # Max 2000 categories
                        break
                else:
                    print(f"❌ Error fetching categories: {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"❌ Exception: {e}")
                break
        
        return all_categories

    def find_serial_related_categories(self, serial_number):
        """Find categories related to a specific serial number"""
        print(f"🔍 Searching for categories related to: {serial_number}")
        
        # Get all categories
        all_categories = self.fetch_all_categories()
        
        if not all_categories:
            print("❌ No categories found")
            return [], [], 0
        
        # Clean serial for matching
        clean_serial = serial_number.replace('-', '').replace('_', '').upper()
        
        # Find categories that match the serial
        related_categories = []
        
        for category in all_categories:
            name_upper = category['name'].upper()
            slug_upper = category['slug'].upper()
            
            # Direct match
            if clean_serial in name_upper or clean_serial in slug_upper:
                related_categories.append(category)
                continue
            
            # Partial match (first 8-12 characters)
            for length in [12, 10, 8]:
                if len(clean_serial) >= length:
                    partial = clean_serial[:length]
                    if partial in name_upper or partial in slug_upper:
                        related_categories.append(category)
                        break
        
        if not related_categories:
            print(f"❌ No categories found for serial: {serial_number}")
            return [], [], 0
        
        # Separate main categories (parent = 0) from subcategories
        main_categories = [cat for cat in related_categories if cat['parent'] == 0]
        sub_categories = [cat for cat in related_categories if cat['parent'] != 0]
        
        print(f"✓ Found {len(related_categories)} categories for {serial_number}")
        print(f"  📁 Main categories: {len(main_categories)}")
        print(f"  📂 Sub-categories: {len(sub_categories)}")
        
        # Calculate total products
        total_products = sum(cat['count'] for cat in related_categories)
        
        return main_categories, sub_categories, total_products

    def get_products_for_serial(self, serial_number):
        """Get products that contain the serial number in SKU or name"""
        print(f"🔍 Searching for products related to: {serial_number}")
        
        page = 1
        per_page = 100
        serial_products = []
        
        # Clean serial for matching
        clean_serial = serial_number.replace('-', '').replace('_', '').upper()
        
        while True:
            try:
                response = self.wcapi.get('products', params={
                    'page': page,
                    'per_page': per_page,
                    'search': serial_number  # Search in product names and descriptions
                })
                
                if response.status_code == 200:
                    products = response.json()
                    if not products:
                        break
                    
                    # Filter products that actually match our serial
                    for product in products:
                        product_name_upper = product['name'].upper()
                        product_sku_upper = product['sku'].upper()
                        
                        if (clean_serial in product_name_upper or 
                            clean_serial in product_sku_upper or
                            serial_number.upper() in product_name_upper or
                            serial_number.upper() in product_sku_upper):
                            serial_products.append(product)
                    
                    page += 1
                    
                    # Limit to avoid too many API calls
                    if page > 10:  # Max 1000 products to check
                        break
                else:
                    print(f"❌ Error fetching products: {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"❌ Exception: {e}")
                break
        
        return serial_products

    def get_category_by_id(self, category_id):
        """Get category details by ID"""
        try:
            response = self.wcapi.get(f'products/categories/{category_id}')
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error fetching category {category_id}: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Exception: {e}")
            return None

    def get_subcategories(self, parent_id):
        """Get all subcategories for a parent category"""
        try:
            response = self.wcapi.get('products/categories', params={
                'parent': parent_id,
                'per_page': 100
            })
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error fetching subcategories: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Exception: {e}")
            return []

    def get_products_in_category(self, category_id):
        """Get products in a specific category"""
        try:
            response = self.wcapi.get('products', params={
                'category': category_id,
                'per_page': 100
            })
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error fetching products: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Exception: {e}")
            return []

    def analyze_category_hierarchy(self, all_categories, category_id, level=0, max_level=5):
        """Recursively analyze category hierarchy"""
        if level > max_level:
            return {'count': 0, 'products': 0, 'children': []}
        
        # Find direct children of this category
        children = [cat for cat in all_categories if cat['parent'] == category_id]
        
        total_child_categories = len(children)
        total_child_products = 0
        child_details = []
        
        for child in children:
            # Get products count for this child
            child_products = child['count']
            total_child_products += child_products
            
            # Recursively analyze this child's hierarchy
            child_hierarchy = self.analyze_category_hierarchy(all_categories, child['id'], level + 1, max_level)
            
            child_info = {
                'id': child['id'],
                'name': child['name'],
                'products': child_products,
                'direct_children': child_hierarchy['count'],
                'total_descendants': child_hierarchy['count'] + sum(1 for _ in child_hierarchy['children']),
                'children': child_hierarchy['children']
            }
            child_details.append(child_info)
            
            # Add descendant counts
            total_child_categories += child_hierarchy['count']
        
        return {
            'count': total_child_categories,
            'products': total_child_products,
            'children': child_details
        }

    def analyze_category(self, category_id):
        """Analyze WordPress for a specific category ID with full hierarchy"""
        print("="*80)
        print(f"🔍 WORDPRESS CATEGORY ANALYSIS FOR ID: {category_id}")
        print("="*80)
        
        # Get category details
        category = self.get_category_by_id(category_id)
        if not category:
            print(f"❌ Category {category_id} not found")
            return None
        
        print(f"✓ Found category: {category['name']}")
        print(f"  🆔 ID: {category['id']}")
        print(f"  🔗 Slug: {category['slug']}")
        print(f"  👆 Parent ID: {category['parent']}")
        print(f"  📦 Direct Product Count: {category['count']}")
        
        # Get all categories to build full hierarchy
        print("🔍 Fetching all categories for hierarchy analysis...")
        all_categories = self.fetch_all_categories()
        
        # Count categories by level
        level_1_categories = [cat for cat in all_categories if cat['parent'] == category_id]
        level_2_categories = []
        level_3_categories = []
        
        for l1_cat in level_1_categories:
            l2_cats = [cat for cat in all_categories if cat['parent'] == l1_cat['id']]
            level_2_categories.extend(l2_cats)
            
            for l2_cat in l2_cats:
                l3_cats = [cat for cat in all_categories if cat['parent'] == l2_cat['id']]
                level_3_categories.extend(l3_cats)
        
        # Get products in this category (direct only)
        products = self.get_products_in_category(category_id)
        
        # Calculate total products including all sub-levels
        total_products_all_levels = category['count']
        for cat in level_1_categories + level_2_categories + level_3_categories:
            total_products_all_levels += cat['count']
        
        print(f"\n📊 COMPLETE HIERARCHY ANALYSIS FOR: {category['name']}")
        print("="*70)
        print(f"📁 Main Category: {category['name']} (ID: {category_id})")
        print(f"📂 Level 1 Sub-categories: {len(level_1_categories)}")
        print(f"📄 Level 2 Sub-sub-categories: {len(level_2_categories)}")
        print(f"📋 Level 3 Sub-sub-sub-categories: {len(level_3_categories)}")
        print(f"🎯 Total Sub-categories (all levels): {len(level_1_categories) + len(level_2_categories) + len(level_3_categories)}")
        print(f"📦 Direct Products in main category: {len(products)}")
        print(f"📦 Total Products (including all sub-categories): {total_products_all_levels}")
        
        # Show level breakdown
        if level_1_categories:
            print(f"\n📂 LEVEL 1 SUB-CATEGORIES:")
            print("-" * 50)
            for i, sub_cat in enumerate(level_1_categories[:10]):  # Show first 10
                l2_count = len([cat for cat in all_categories if cat['parent'] == sub_cat['id']])
                print(f"  {i+1:2d}. {sub_cat['name'][:50]} (ID: {sub_cat['id']}, Products: {sub_cat['count']}, Children: {l2_count})")
            
            if len(level_1_categories) > 10:
                print(f"  ... and {len(level_1_categories) - 10} more level 1 categories")
        
        if level_2_categories:
            print(f"\n📄 LEVEL 2 SUB-SUB-CATEGORIES (sample):")
            print("-" * 50)
            for i, sub_cat in enumerate(level_2_categories[:10]):  # Show first 10
                l3_count = len([cat for cat in all_categories if cat['parent'] == sub_cat['id']])
                # Find parent name
                parent_name = next((cat['name'] for cat in level_1_categories if cat['id'] == sub_cat['parent']), 'Unknown')
                print(f"  {i+1:2d}. {sub_cat['name'][:40]} (Parent: {parent_name[:20]}, Products: {sub_cat['count']}, Children: {l3_count})")
            
            if len(level_2_categories) > 10:
                print(f"  ... and {len(level_2_categories) - 10} more level 2 categories")
        
        if level_3_categories:
            print(f"\n📋 LEVEL 3 SUB-SUB-SUB-CATEGORIES (sample):")
            print("-" * 50)
            for i, sub_cat in enumerate(level_3_categories[:5]):  # Show first 5
                # Find parent name
                parent_name = next((cat['name'] for cat in level_2_categories if cat['id'] == sub_cat['parent']), 'Unknown')
                print(f"  {i+1:2d}. {sub_cat['name'][:40]} (Parent: {parent_name[:20]}, Products: {sub_cat['count']})")
            
            if len(level_3_categories) > 5:
                print(f"  ... and {len(level_3_categories) - 5} more level 3 categories")
        
        # Final summary matching Oscar format
        total_main_cats = 1  # The category itself
        total_sub_cats = len(level_1_categories) + len(level_2_categories) + len(level_3_categories)
        
        print(f"\n✅ SUMMARY (Oscar format comparison):")
        print("="*60)
        print(f"📁 Main Categories: {total_main_cats}")
        print(f"📂 Sub-Categories (all levels): {total_sub_cats}")
        print(f"   📂 Level 1: {len(level_1_categories)}")
        print(f"   📄 Level 2: {len(level_2_categories)}")
        print(f"   📋 Level 3: {len(level_3_categories)}")
        print(f"📦 Total Products: {total_products_all_levels}")
        print(f"🏗️  Category Depth: {3 if level_3_categories else 2 if level_2_categories else 1} levels")
        
        return {
            'main_categories': total_main_cats,
            'sub_categories_l1': len(level_1_categories),
            'sub_categories_l2': len(level_2_categories), 
            'sub_categories_l3': len(level_3_categories),
            'total_sub_categories': total_sub_cats,
            'products': total_products_all_levels,
            'direct_products': len(products)
        }
        print(f"📦 Product Count: {category['count']}")
        
        # Get parent category if it has one
        parent_info = "ROOT (Main Category)"
        if category['parent'] != 0:
            parent_category = self.get_category_by_id(category['parent'])
            if parent_category:
                parent_info = f"{parent_category['name']} (ID: {parent_category['id']})"
        
        print(f"📂 Parent: {parent_info}")
        
        # Get subcategories
        subcategories = self.get_subcategories(category_id)
        print(f"📂 Sub-categories: {len(subcategories)}")
        
        # Get products in this category
        products = self.get_products_in_category(category_id)
        print(f"📦 Direct Products: {len(products)}")
        
        # Show subcategory details
        if subcategories:
            print(f"\n📋 SUB-CATEGORIES:")
            print("-" * 50)
            total_subcategory_products = 0
            
            for subcat in subcategories:
                subcat_products = self.get_products_in_category(subcat['id'])
                total_subcategory_products += len(subcat_products)
                print(f"  📂 {subcat['name']} (ID: {subcat['id']}, Products: {len(subcat_products)})")
            
            print(f"\n📊 Products in subcategories: {total_subcategory_products}")
        
        # Show product samples
        if products:
            print(f"\n🔍 SAMPLE PRODUCTS (showing first 10):")
            print("-" * 60)
            for i, product in enumerate(products[:10]):
                status = "✅" if product['status'] == 'publish' else "❌"
                stock_status = product['stock_status'].upper()
                price = product['price'] if product['price'] else 'No price'
                print(f"  {status} {product['name'][:50]}...")
                print(f"     SKU: {product['sku']}, Price: £{price}, Stock: {stock_status}")
                
            if len(products) > 10:
                print(f"  ... and {len(products) - 10} more products")
        
        # Calculate totals
        total_subcategory_products = sum(len(self.get_products_in_category(sub['id'])) for sub in subcategories)
        total_all_products = len(products) + total_subcategory_products
        
        print(f"\n✅ FINAL SUMMARY:")
        print("="*60)
        print(f"📁 Category: {category['name']}")
        print(f"📂 Sub-categories: {len(subcategories)}")
        print(f"📦 Direct Products: {len(products)}")
        print(f"🔢 Products in Subcategories: {total_subcategory_products}")
        print(f"🎯 Total Products (All): {total_all_products}")
        
        return {
            'category_name': category['name'],
            'category_id': category['id'],
            'sub_categories': len(subcategories),
            'direct_products': len(products),
            'subcategory_products': total_subcategory_products,
            'total_products': total_all_products
        }

    def analyze_serial(self, serial_number):
        """Analyze WordPress for a specific serial number"""
        print("="*80)
        print(f"🔍 WORDPRESS ANALYSIS FOR: {serial_number}")
        print("="*80)
        
        # Find categories
        main_categories, sub_categories, category_products = self.find_serial_related_categories(serial_number)
        
        # Find products directly
        serial_products = self.get_products_for_serial(serial_number)
        
        print(f"\n📊 SUMMARY FOR {serial_number}")
        print("-" * 60)
        print(f"🌐 WordPress Site: {WORDPRESS_URL}")
        print(f"📁 Main categories found: {len(main_categories)}")
        print(f"📂 Sub-categories found: {len(sub_categories)}")
        print(f"📦 Products in categories: {category_products}")
        print(f"🔍 Products found by search: {len(serial_products)}")
        
        # Show category details if found
        if main_categories or sub_categories:
            print(f"\n📋 CATEGORY BREAKDOWN:")
            print("-" * 40)
            
            if main_categories:
                print("📁 MAIN CATEGORIES:")
                for cat in main_categories:
                    print(f"  • {cat['name']} (ID: {cat['id']}, Products: {cat['count']})")
            
            if sub_categories:
                print("\n📂 SUB-CATEGORIES:")
                for cat in sub_categories:
                    parent_name = "Unknown"
                    # Try to find parent name from main categories
                    for main_cat in main_categories:
                        if main_cat['id'] == cat['parent']:
                            parent_name = main_cat['name']
                            break
                    print(f"  • {cat['name']} (Parent: {parent_name}, Products: {cat['count']})")
        
        # Show product samples if found
        if serial_products:
            print(f"\n🔍 SAMPLE PRODUCTS (showing first 10):")
            print("-" * 50)
            for i, product in enumerate(serial_products[:10]):
                status = "✅" if product['status'] == 'publish' else "❌"
                stock_status = product['stock_status'].upper()
                price = product['price'] if product['price'] else 'No price'
                print(f"  {status} {product['name'][:60]}...")
                print(f"     SKU: {product['sku']}, Price: £{price}, Stock: {stock_status}")
                
            if len(serial_products) > 10:
                print(f"  ... and {len(serial_products) - 10} more products")
        
        # Final summary
        total_items = len(main_categories) + len(sub_categories) + len(serial_products)
        
        print(f"\n✅ FINAL SUMMARY:")
        print("="*60)
        print(f"📁 Main Categories: {len(main_categories)}")
        print(f"📂 Sub-Categories: {len(sub_categories)}")
        print(f"📦 Total Products: {len(serial_products)}")
        print(f"🎯 Total Items Found: {total_items}")
        
        return {
            'main_categories': len(main_categories),
            'sub_categories': len(sub_categories),
            'products': len(serial_products),
            'category_products': category_products,
            'total_items': total_items
        }

def main():
    parser = argparse.ArgumentParser(description='Analyze WordPress/WooCommerce for serial number or category data')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--serial', help='Serial number to analyze (e.g., LSFAL11A4PA157987)')
    group.add_argument('--category', type=int, help='Category ID to analyze (e.g., 517)')
    
    args = parser.parse_args()
    
    try:
        analyzer = WPSerialAnalyzer()
        
        if args.serial:
            result = analyzer.analyze_serial(args.serial)
            print(f"\n🎉 Analysis complete for serial {args.serial}!")
        
        elif args.category:
            result = analyzer.analyze_category(args.category)
            if result:
                print(f"\n🎉 Analysis complete for category {args.category}!")
            else:
                return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())