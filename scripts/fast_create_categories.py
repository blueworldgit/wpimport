#!/usr/bin/env python3
"""
Fast Async Oscar Category Creator
Extracts categories from Oscar database and creates them in WooCommerce with async processing
"""
import asyncio
import aiohttp
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
import sys
import time
import re
import requests
from tqdm.asyncio import tqdm
from datetime import datetime

# Add parent directory to path for imports
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))
from config import WORDPRESS_URL

# Database connection parameters
DB_CONFIG = {
    'dbname': 'parts_store',
    'user': 'postgres',
    'password': 'N0rwich!',
    'host': '80.95.207.42',
    'port': '5432'
}

class FastCategoryCreator:
    def __init__(self, serial_filter=None, concurrent_requests=10):
        self.serial_filter = serial_filter
        self.concurrent_requests = concurrent_requests
        self.conn = None
        self.consumer_key = None
        self.consumer_secret = None
        self.session = None
        self.category_cache = {}  # {name: id}
        self.error_log = []
        
        self.stats = {
            'categories_created': 0,
            'categories_found': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
    def connect(self):
        """Connect to Oscar database"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            print("✓ Connected to Oscar database")
            return True
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False
    
    def load_credentials(self):
        """Load WooCommerce credentials"""
        keys_file = base_dir / 'keys.txt'
        if not keys_file.exists():
            raise FileNotFoundError("keys.txt not found")
        
        with open(keys_file, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        
        for i, line in enumerate(lines):
            if 'Consumer key' in line and i+1 < len(lines): 
                self.consumer_key = lines[i+1]
            if 'Consumer secret' in line and i+1 < len(lines): 
                self.consumer_secret = lines[i+1]
        
        if not self.consumer_key or not self.consumer_secret:
            raise Exception("WooCommerce credentials not found in keys.txt")
        
        print("✓ WooCommerce credentials loaded")
    
    def sanitize_category_name(self, name):
        """Sanitize category names for WooCommerce compatibility"""
        if not name:
            return "Uncategorized"
        
        # Remove diagram codes (JE123A001 - ) from category names
        name = re.sub(r'^[A-Z]{2}\d+[A-Z]?\d+\s*-\s*', '', name)
        
        # Replace problematic characters but keep full length
        sanitized = name.replace('&', 'and').replace('/', '-').replace('\\', '-')
        sanitized = sanitized.replace('(', '').replace(')', '').replace(',', '')
        
        # Clean up extra spaces and dashes
        sanitized = re.sub(r'\s+', ' ', sanitized)
        sanitized = re.sub(r'-+', '-', sanitized)
        
        return sanitized.strip(' -')
    
    async def preload_existing_categories(self):
        """Preload all existing categories to avoid creating duplicates"""
        print("📂 Preloading existing WordPress categories...")
        
        # Clear any existing cache first
        self.category_cache.clear()
        
        try:
            # Use sync requests for initial load
            page = 1
            all_categories = []
            
            while True:
                url = f"{WORDPRESS_URL}/wp-json/wc/v3/products/categories"
                params = {'per_page': 100, 'page': page, '_': int(time.time())}  # Add cache buster
                
                response = requests.get(url, params=params, auth=(self.consumer_key, self.consumer_secret))
                if response.status_code != 200:
                    if response.status_code == 404:  # No more pages
                        break
                    print(f"⚠️ HTTP {response.status_code}: {response.text}")
                    break
                
                categories = response.json()
                if not categories:
                    break
                
                all_categories.extend(categories)
                page += 1
            
            # Build category cache and show what was found
            print(f"🔍 Found {len(all_categories)} total categories:")
            
            if len(all_categories) <= 5:  # Show details if few categories
                for cat in all_categories:
                    self.category_cache[cat['name']] = cat['id']
                    print(f"   🔍 Found existing: {cat['name']} (ID: {cat['id']}, Parent: {cat.get('parent', 0)})")
            else:
                for cat in all_categories:
                    self.category_cache[cat['name']] = cat['id']
                    print(f"   🔍 Found existing: {cat['name']} (ID: {cat['id']}, Parent: {cat.get('parent', 0)})")
            
            print(f"✅ Cached {len(all_categories)} existing categories")
            
            if len(all_categories) == 0:
                print("✅ Perfect! No existing categories found")
            elif len(all_categories) == 1 and 'Uncategorized' in [c['name'] for c in all_categories]:
                print("✅ Perfect! Only 'Uncategorized' found (as expected)")
            else:
                print(f"⚠️ WARNING: {len(all_categories)} existing categories found - expected 1 (Uncategorized)")
            
        except Exception as e:
            print(f"⚠️ Category preloading failed: {e}")
            import traceback
            traceback.print_exc()
    
    def extract_category_hierarchy(self):
        """Extract all unique categories from database"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Build WHERE clause for serial filtering
        where_clause = ""
        params = []
        if self.serial_filter:
            where_clause = "WHERE sn.serial = %s"
            params.append(self.serial_filter)
        
        print(f"🔍 Extracting category hierarchy...")
        if self.serial_filter:
            print(f"  📋 Filtering by serial: {self.serial_filter}")
        
        # Get all unique category combinations
        query = f"""
            SELECT DISTINCT
                sn.vehicle_brand,
                sn.serial,
                pt.title as parent_category,
                ct.title as child_category
            FROM motorpartsdata_serialnumber sn
            JOIN motorpartsdata_parenttitle pt ON pt.serial_number_id = sn.id
            JOIN motorpartsdata_childtitle ct ON ct.parent_id = pt.id
            {where_clause}
            ORDER BY sn.vehicle_brand, sn.serial, pt.title, ct.title
        """
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Build category hierarchy 
        brands = set()
        serials = {}  # {serial: brand}
        parents = {}  # {parent: serial}
        children = {}  # {child: parent}
        
        print(f"📋 Processing {len(rows)} database rows...")
        
        # Build hierarchy - no dual-role detection needed
        for row in rows:
            brand = self.sanitize_category_name(row['vehicle_brand'])
            serial = self.sanitize_category_name(row['serial'])
            parent = self.sanitize_category_name(row['parent_category'])
            child = self.sanitize_category_name(row['child_category'])
            
            brands.add(brand)
            serials[serial] = brand
            parents[parent] = serial
            
            # Only add to children if it's not a self-reference
            if child != parent:
                children[child] = parent
            else:
                print(f"   ⏭️  SKIPPING self-referencing category: '{child}' (child == parent)")
        
        print(f"📊 Category hierarchy:")
        print(f"   📂 Parent categories: {len(parents)}")
        print(f"   📄 Child categories: {len(children)}")
        
        cursor.close()
        
        print(f"📊 Found:")
        print(f"   🏢 Brands: {len(brands)}")
        print(f"   🚗 Serials: {len(serials)}")
        print(f"   📂 Parent categories: {len(parents)}")
        print(f"   📄 Child categories: {len(children)}")
        
        return {
            'brands': brands,
            'serials': serials,
            'parents': parents,
            'children': children
        }
    
    async def create_category_async(self, session, name, parent_id=0):
        """Create a single category asynchronously"""
        # Check if already exists in cache
        if name in self.category_cache:
            self.stats['categories_found'] += 1
            print(f"   🔍 CACHE HIT: '{name}' already exists (ID: {self.category_cache[name]}) - SKIPPING CREATION")
            return self.category_cache[name]
        
        try:
            # Create category
            url = f"{WORDPRESS_URL}/wp-json/wc/v3/products/categories"
            data = {
                'name': name,
                'parent': parent_id
            }
            
            auth = aiohttp.BasicAuth(self.consumer_key, self.consumer_secret)
            
            async with session.post(url, json=data, auth=auth) as response:
                if response.status == 201:
                    result = await response.json()
                    category_id = result['id']
                    self.category_cache[name] = category_id
                    self.stats['categories_created'] += 1
                    print(f"   ✅ CREATED NEW: {name} (ID: {category_id}, Parent: {parent_id})")
                    return category_id
                elif response.status == 400:
                    # Category might already exist
                    error_data = await response.json()
                    if 'term_exists' in str(error_data):
                        # Try to find existing category
                        search_url = f"{WORDPRESS_URL}/wp-json/wc/v3/products/categories"
                        params = {'search': name, 'per_page': 10}
                        
                        async with session.get(search_url, params=params, auth=auth) as search_response:
                            if search_response.status == 200:
                                categories = await search_response.json()
                                for cat in categories:
                                    if cat['name'] == name:
                                        self.category_cache[name] = cat['id']
                                        self.stats['categories_found'] += 1
                                        print(f"   🔍 SEARCH FOUND EXISTING: '{name}' (ID: {cat['id']}, Parent: {cat.get('parent', 0)}) - CREATION FAILED BUT CATEGORY EXISTS")
                                        return cat['id']
                    
                    self.error_log.append(f"Category creation failed for '{name}': {error_data}")
                    self.stats['errors'] += 1
                    return None
                else:
                    error_text = await response.text()
                    self.error_log.append(f"HTTP {response.status} creating '{name}': {error_text}")
                    self.stats['errors'] += 1
                    return None
                    
        except Exception as e:
            self.error_log.append(f"Exception creating '{name}': {str(e)}")
            self.stats['errors'] += 1
            return None
    
    async def create_category_batch(self, session, category_list, parent_lookup, desc):
        """Create a batch of categories with proper parent relationships"""
        tasks = []
        results = {}
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.concurrent_requests)
        
        async def create_with_semaphore(name):
            async with semaphore:
                parent_id = parent_lookup.get(name, 0)
                result = await self.create_category_async(session, name, parent_id)
                results[name] = result
                return result
        
        # Create all tasks
        for name in category_list:
            tasks.append(create_with_semaphore(name))
        
        # Execute with progress bar
        await tqdm.gather(*tasks, desc=desc, total=len(tasks))
        
        return results
    
    async def create_categories_async(self, categories):
        """Create all categories in WooCommerce with async processing"""
        print(f"\n🚀 Creating Category Hierarchy in WooCommerce (Async)")
        print(f"{'='*60}")
        
        # Create aiohttp session
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(limit=self.concurrent_requests * 2)
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            
            # Level 1: Create brands (top level)
            print("\n📁 Level 1: Brand categories...")
            brand_list = list(categories['brands'])
            brand_lookup = {brand: 0 for brand in brand_list}  # All brands are top-level (parent=0)
            
            brand_results = await self.create_category_batch(
                session, brand_list, brand_lookup, "Brands"
            )
            print(f"   📊 Brand results: {brand_results}")
            
            # Level 2: Create serials under brands  
            print("\n🚗 Level 2: Serial categories...")
            serial_list = list(categories['serials'].keys())
            serial_lookup = {}
            for serial, brand in categories['serials'].items():
                brand_id = brand_results.get(brand)
                if brand_id:
                    serial_lookup[serial] = brand_id
                    print(f"   🔗 {serial} → parent {brand} (ID: {brand_id})")
                else:
                    serial_lookup[serial] = 0
                    print(f"   ⚠️ {serial} → no parent found for brand '{brand}'")
            
            serial_results = await self.create_category_batch(
                session, serial_list, serial_lookup, "Serials"
            )
            
            # Level 3: Create parent categories under serials
            print("\n📂 Level 3: Parent categories...")
            parent_list = list(categories['parents'].keys())
            parent_lookup = {}
            for parent, serial in categories['parents'].items():
                serial_id = serial_results.get(serial)
                if serial_id:
                    parent_lookup[parent] = serial_id
                else:
                    parent_lookup[parent] = 0
                    print(f"   ⚠️ {parent} → no parent found for serial '{serial}'")
            
            parent_results = await self.create_category_batch(
                session, parent_list, parent_lookup, "Parents"
            )
            
            # Level 4: Create child categories under parents
            print("\n📄 Level 4: Child categories...")
            child_list = list(categories['children'].keys())
            child_lookup = {}
            for child, parent in categories['children'].items():
                parent_id = parent_results.get(parent)
                if parent_id:
                    child_lookup[child] = parent_id
                else:
                    child_lookup[child] = 0
                    print(f"   ⚠️ {child} → no parent found for parent '{parent}'")
            
            await self.create_category_batch(
                session, child_list, child_lookup, "Children"
            )
    async def run_async(self):
        """Run the async category creation process"""
        try:
            # Connect to database
            if not self.connect():
                return False
            
            # Load credentials
            self.load_credentials()
            
            # Preload existing categories
            await self.preload_existing_categories()
            
            # Extract hierarchy from database
            categories = self.extract_category_hierarchy()
            
            # Create categories asynchronously
            await self.create_categories_async(categories)
            
            # Print final stats
            duration = datetime.now() - self.stats['start_time']
            print(f"\n🎉 ASYNC CATEGORY CREATION COMPLETED")
            print(f"{'='*60}")
            print(f"⏱️  Total time: {duration.total_seconds():.1f}s")
            print(f"✅ Categories created: {self.stats['categories_created']}")
            print(f"🔍 Categories found existing: {self.stats['categories_found']}")
            print(f"❌ Errors: {self.stats['errors']}")
            
            # Expected counts
            expected_new = 1 + 1 + 47 + 155  # brand + serial + parents + children
            print(f"\n📊 EXPECTED vs ACTUAL:")
            print(f"   Expected new categories: {expected_new}")
            print(f"   Actual new categories: {self.stats['categories_created']}")
            print(f"   Expected existing: 1 (Uncategorized)")
            print(f"   Actual existing: {self.stats['categories_found']}")
            
            if self.stats['categories_found'] > 1:
                print(f"   ⚠️  WARNING: {self.stats['categories_found'] - 1} unexpected existing categories detected!")
                print(f"   💡 Check the detailed logs above for 'CACHE HIT' and 'SEARCH FOUND EXISTING' messages")
            
            total_categories = self.stats['categories_created'] + self.stats['categories_found']
            if duration.total_seconds() > 0:
                rate = total_categories / duration.total_seconds()
                print(f"📈 Processing rate: {rate:.1f} categories/second")
            
            if self.error_log:
                print(f"\n⚠️  Error Log ({len(self.error_log)} errors):")
                for i, error in enumerate(self.error_log[:10]):  # Show first 10 errors
                    print(f"   {i+1}. {error}")
                if len(self.error_log) > 10:
                    print(f"   ... and {len(self.error_log) - 10} more errors")
            
            return self.stats['errors'] == 0
            
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            return False
        finally:
            if self.conn:
                self.conn.close()
    
    def run(self):
        """Run the category creation process"""
        return asyncio.run(self.run_async())

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fast async category creator from Oscar database to WooCommerce')
    parser.add_argument('--serial', help='Filter by specific serial number')
    parser.add_argument('--concurrent', type=int, default=10, help='Number of concurrent requests (default: 10)')
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print("🚀 Fast Async Oscar Category Creator")
    print(f"{'='*60}")
    print(f"🔗 Concurrent requests: {args.concurrent}")
    if args.serial:
        print(f"🚗 Serial filter: {args.serial}")
    
    creator = FastCategoryCreator(serial_filter=args.serial, concurrent_requests=args.concurrent)
    success = creator.run()
    
    if success:
        print("\n✅ Fast category creation completed successfully!")
        return 0
    else:
        print("\n❌ Fast category creation completed with errors")
        return 1

if __name__ == '__main__':
    exit(main())