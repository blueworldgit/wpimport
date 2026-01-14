#!/usr/bin/env python3
"""
WordPress Category Analyzer
Analyzes WooCommerce categories and compares with Oscar report data
"""
from woocommerce import API
from pathlib import Path
import sys
import json
from collections import defaultdict
import re

# Add parent directory to path for imports
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))
from config import WORDPRESS_URL

class WPCategoryAnalyzer:
    def __init__(self):
        self.wcapi = None
        self.categories = []
        self.category_tree = defaultdict(list)
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
        print("\n🔍 Fetching all categories from WordPress...")
        
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
                    if not categories:  # Empty response means no more pages
                        break
                    
                    all_categories.extend(categories)
                    print(f"   📄 Page {page}: {len(categories)} categories")
                    page += 1
                else:
                    print(f"❌ Error fetching categories: {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"❌ Exception fetching categories: {e}")
                break
        
        self.categories = all_categories
        print(f"✓ Total categories fetched: {len(all_categories)}")
        return all_categories

    def build_category_tree(self):
        """Build category hierarchy tree"""
        print("\n🌳 Building category tree...")
        
        # Sort by parent first, then by name
        sorted_categories = sorted(self.categories, key=lambda x: (x['parent'], x['name']))
        
        # Build parent -> children mapping
        for category in sorted_categories:
            parent_id = category['parent']
            self.category_tree[parent_id].append(category)
        
        # Count main categories (parent = 0)
        main_categories = self.category_tree[0]
        total_subcategories = len(self.categories) - len(main_categories)
        
        print(f"✓ Main categories: {len(main_categories)}")
        print(f"✓ Sub-categories: {total_subcategories}")
        
        return main_categories, total_subcategories

    def print_category_tree(self, parent_id=0, level=0, max_level=3):
        """Print category tree structure"""
        if level > max_level:
            return
            
        categories = self.category_tree[parent_id]
        
        for category in categories:
            indent = "  " * level
            icon = "📁" if level == 0 else "📂" if level == 1 else "📄"
            
            print(f"{indent}{icon} {category['name']} (ID: {category['id']}, Count: {category['count']})")
            
            # Show children if not at max level
            if level < max_level:
                self.print_category_tree(category['id'], level + 1, max_level)

    def find_serial_categories(self, serial_number):
        """Find categories that might be related to a specific serial"""
        print(f"\n🔍 Searching for categories related to serial: {serial_number}")
        
        # Clean serial for matching
        clean_serial = serial_number.replace('-', '').replace('_', '').upper()
        
        related_categories = []
        
        for category in self.categories:
            name = category['name'].upper()
            slug = category['slug'].upper()
            
            # Check for serial in name or slug
            if clean_serial in name or clean_serial in slug:
                related_categories.append(category)
                continue
            
            # Check for partial matches (first 8 chars)
            if len(clean_serial) >= 8:
                partial = clean_serial[:8]
                if partial in name or partial in slug:
                    related_categories.append(category)
        
        if related_categories:
            print(f"✓ Found {len(related_categories)} categories related to {serial_number}:")
            for cat in related_categories:
                parent_name = "ROOT" if cat['parent'] == 0 else next(
                    (c['name'] for c in self.categories if c['id'] == cat['parent']), 
                    f"Parent ID {cat['parent']}"
                )
                print(f"   📂 {cat['name']} (ID: {cat['id']}, Parent: {parent_name}, Count: {cat['count']})")
        else:
            print(f"❌ No categories found specifically for {serial_number}")
        
        return related_categories

    def analyze_category_patterns(self):
        """Analyze category naming patterns"""
        print("\n📊 Analyzing category patterns...")
        
        # Analyze naming patterns
        patterns = {
            'has_diagram_code': 0,
            'has_serial': 0,
            'automotive_terms': 0,
            'empty_categories': 0,
            'total_products': 0
        }
        
        automotive_keywords = [
            'suspension', 'brake', 'engine', 'body', 'panel', 'lamp', 'door',
            'window', 'roof', 'bumper', 'wheel', 'tire', 'steering', 'transmission',
            'battery', 'electrical', 'hvac', 'air', 'intake', 'exhaust'
        ]
        
        for category in self.categories:
            name_lower = category['name'].lower()
            
            # Check for diagram codes (like JE123A001)
            if re.search(r'[A-Z]{2}\d{3}[A-Z]\d{3}', category['name']):
                patterns['has_diagram_code'] += 1
            
            # Check for serial-like patterns
            if re.search(r'[A-Z]{3}\d{2}[A-Z]\d+', category['name']):
                patterns['has_serial'] += 1
            
            # Check for automotive terms
            if any(keyword in name_lower for keyword in automotive_keywords):
                patterns['automotive_terms'] += 1
            
            # Track empty categories
            if category['count'] == 0:
                patterns['empty_categories'] += 1
            
            patterns['total_products'] += category['count']
        
        print(f"   📋 Categories with diagram codes: {patterns['has_diagram_code']}")
        print(f"   🔢 Categories with serial patterns: {patterns['has_serial']}")
        print(f"   🚗 Categories with automotive terms: {patterns['automotive_terms']}")
        print(f"   📭 Empty categories: {patterns['empty_categories']}")
        print(f"   📦 Total products across all categories: {patterns['total_products']}")
        
        return patterns

    def export_category_data(self, filename=None):
        """Export category data to JSON file"""
        if filename is None:
            filename = base_dir / 'data' / 'wp_categories_export.json'
        
        # Create data directory if it doesn't exist
        filename.parent.mkdir(exist_ok=True)
        
        export_data = {
            'export_timestamp': str(Path(__file__).stat().st_mtime),
            'total_categories': len(self.categories),
            'wordpress_url': WORDPRESS_URL,
            'categories': self.categories,
            'category_tree': {str(k): v for k, v in self.category_tree.items()}  # JSON needs string keys
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Category data exported to: {filename}")
        return filename

    def compare_with_oscar_report(self, report_file=None):
        """Compare WordPress categories with Oscar report"""
        if report_file is None:
            report_file = base_dir / 'report.txt'
        
        print(f"\n🔄 Comparing with Oscar report: {report_file}")
        
        if not report_file.exists():
            print(f"❌ Report file not found: {report_file}")
            return
        
        # Read report and extract LSFAL11A4PA157987 section
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find LSFAL11A4PA157987 section
        serial_section = None
        lines = content.split('\n')
        
        start_found = False
        oscar_categories = []
        oscar_subcategories = []
        
        for i, line in enumerate(lines):
            if '🚗 Serial: LSFAL11A4PA157987' in line:
                start_found = True
                continue
            
            if start_found:
                if '🚗 Serial:' in line and 'LSFAL11A4PA157987' not in line:
                    # Next serial found, stop
                    break
                
                # Extract main categories (📁)
                if '📁 ' in line and '(' in line and 'parts)' in line:
                    category_name = line.split('📁 ')[1].split(' (')[0].strip()
                    parts_count = int(line.split('(')[1].split(' parts)')[0])
                    oscar_categories.append({'name': category_name, 'parts': parts_count})
                
                # Extract subcategories (📂)
                elif '📂 ' in line and '(' in line and 'parts)' in line:
                    subcategory_name = line.split('📂 ')[1].split(' (')[0].strip()
                    parts_count = int(line.split('(')[1].split(' parts)')[0])
                    oscar_subcategories.append({'name': subcategory_name, 'parts': parts_count})
        
        if oscar_categories:
            print(f"✓ Found Oscar data for LSFAL11A4PA157987:")
            print(f"   📁 Main categories in Oscar: {len(oscar_categories)}")
            print(f"   📂 Sub-categories in Oscar: {len(oscar_subcategories)}")
            
            # Show comparison
            wp_main = len(self.category_tree[0])
            wp_total = len(self.categories)
            wp_sub = wp_total - wp_main
            
            print(f"\n📊 Comparison:")
            print(f"   Oscar Main Categories:     {len(oscar_categories)}")
            print(f"   WordPress Main Categories: {wp_main}")
            print(f"   Oscar Sub-Categories:      {len(oscar_subcategories)}")
            print(f"   WordPress Sub-Categories:  {wp_sub}")
            
            # Look for matching categories
            print(f"\n🔍 Looking for matching categories...")
            matches = 0
            for oscar_cat in oscar_categories:
                for wp_cat in self.categories:
                    if oscar_cat['name'].lower() in wp_cat['name'].lower() or \
                       wp_cat['name'].lower() in oscar_cat['name'].lower():
                        matches += 1
                        print(f"   ✓ Match: '{oscar_cat['name']}' ≈ '{wp_cat['name']}'")
                        break
            
            print(f"✓ Found {matches} potential matches out of {len(oscar_categories)} Oscar categories")
            
        else:
            print(f"❌ No Oscar data found for LSFAL11A4PA157987 in report")

def main():
    try:
        analyzer = WPCategoryAnalyzer()
        
        # Fetch all categories
        categories = analyzer.fetch_all_categories()
        
        # Build category tree
        main_cats, sub_cats = analyzer.build_category_tree()
        
        # Print category overview
        print("\n" + "="*80)
        print("📊 WORDPRESS CATEGORY ANALYSIS")
        print("="*80)
        
        print(f"🌐 WordPress Site: {WORDPRESS_URL}")
        print(f"📁 Total Categories: {len(categories)}")
        print(f"📂 Main Categories: {len(main_cats)}")
        print(f"📄 Sub-Categories: {sub_cats}")
        
        # Show category tree (limited depth for readability)
        print(f"\n🌳 Category Tree (Top 2 levels):")
        analyzer.print_category_tree(max_level=2)
        
        # Look for serial-specific categories
        analyzer.find_serial_categories('LSFAL11A4PA157987')
        
        # Analyze patterns
        patterns = analyzer.analyze_category_patterns()
        
        # Export data
        export_file = analyzer.export_category_data()
        
        # Compare with Oscar report
        analyzer.compare_with_oscar_report()
        
        print(f"\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())