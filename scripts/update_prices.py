"""
Price Update Script - Phase 4 (WordPress-First)
Updates WooCommerce product prices from Excel file using WordPress-first approach
"""
import sys
import pandas as pd
from pathlib import Path
from woocommerce import API
from tqdm import tqdm
import time
from datetime import datetime

# Add parent directory to path for config
base_dir = Path(__file__).parent.parent
sys.path.insert(0, str(base_dir))

from config import WORDPRESS_URL

class PriceUpdater:
    def __init__(self, excel_file, wcapi, category_id=None):
        self.excel_file = excel_file
        self.wcapi = wcapi
        self.category_id = category_id  # Filter products to this WP category
        self.pricing_lookup = {}  # In-memory price lookup
        self.no_price_log = base_dir / 'nopricefound.txt'
        self.stats = {
            'total_in_db': 0,
            'total_in_excel': 0,
            'prices_updated': 0,
            'not_found_in_excel': 0,
            'not_found_in_wp': 0,
            'no_pricing_needed': 0,
            'errors': [],
            'skipped': []
        }
        
        # Initialize the no price log file
        self.init_no_price_log()
    
    def init_no_price_log(self):
        """Initialize the no price found log file"""
        try:
            with open(self.no_price_log, 'w', encoding='utf-8') as f:
                f.write(f"# SKUs Not Found in Excel - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("# These Oscar SKUs exist in database but have no pricing in Excel file\n\n")
        except Exception as e:
            print(f"Warning: Could not initialize no price log: {e}")
    
    def log_no_price_sku(self, sku):
        """Log a SKU that has no pricing in Excel"""
        try:
            with open(self.no_price_log, 'a', encoding='utf-8') as f:
                f.write(f"{sku}\n")
        except Exception as e:
            self.stats['errors'].append(f"Could not log no-price SKU {sku}: {e}")
    
    def load_pricing_data(self):
        """Load pricing data from Excel file into memory lookup"""
        print(f"\n📊 Loading pricing data from: {self.excel_file}")
        
        df = pd.read_excel(self.excel_file)
        
        # Verify required columns exist
        required_cols = ['Part Number', 'Retail Price']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Clean the data
        df['Part Number'] = df['Part Number'].astype(str).str.strip()
        df['Retail Price'] = pd.to_numeric(df['Retail Price'], errors='coerce')
        
        # Remove rows with invalid prices
        df = df[df['Retail Price'].notna()]
        df = df[df['Retail Price'] > 0]
        
        # Create fast lookup dictionary
        for _, row in df.iterrows():
            self.pricing_lookup[row['Part Number']] = row['Retail Price']
        
        self.stats['total_in_excel'] = len(self.pricing_lookup)
        
        print(f"✅ Loaded {len(self.pricing_lookup)} valid price records into memory")
        print(f"   SKU range: {min(self.pricing_lookup.keys())} to {max(self.pricing_lookup.keys())}")
        
        if self.pricing_lookup:
            prices = list(self.pricing_lookup.values())
            print(f"   Price range: £{min(prices):.2f} to £{max(prices):.2f}")
        
        return True
    
    def get_imported_skus_from_wordpress(self):
        """Get unique original_sku values from WordPress products"""
        try:
            print(f"\n🔍 Querying WordPress for imported original_sku metadata...")
            
            unique_skus = set()
            page = 1
            
            params = {"per_page": 100, "page": page, "status": "publish"}
            if self.category_id:
                params["category"] = self.category_id

            while True:
                response = self.wcapi.get("products", params=params)
                
                if response.status_code != 200 or not response.json():
                    break
                
                products = response.json()
                if not products:
                    break
                
                # Extract original_sku metadata from each product
                for product in products:
                    meta_data = product.get('meta_data', [])
                    for meta in meta_data:
                        if meta.get('key') == 'original_sku':
                            original_sku = meta.get('value')
                            if original_sku:
                                unique_skus.add(str(original_sku).strip())
                
                print(f"   📄 Processed page {page}: {len(products)} products")
                page += 1
                params["page"] = page
                
                # Safety limit
                if page > 200:
                    print("   ⚠️ Reached page limit (200), stopping")
                    break
            
            unique_skus_list = sorted(list(unique_skus))
            self.stats['total_in_db'] = len(unique_skus_list)
            
            print(f"✅ Found {len(unique_skus_list)} unique original_sku values in WordPress")
            
            return unique_skus_list
        
        except Exception as e:
            print(f"❌ WordPress query error: {e}")
            return []
    def get_products_by_original_sku(self, original_sku):
        """Get WooCommerce products by original_sku metadata that have no pricing"""
        try:
            # Search for products with this original SKU that have no regular price
            response = self.wcapi.get("products", params={
                "meta_key": "original_sku",
                "meta_value": original_sku,
                "per_page": 100,  # Get all matches
                "status": "publish"
            })
            
            if response.status_code == 200:
                products = response.json()
                # Filter for products with no pricing or zero pricing
                no_price_products = []
                for product in products:
                    regular_price = product.get('regular_price', '')
                    if not regular_price or regular_price == '0' or regular_price == '0.00':
                        no_price_products.append(product)
                
                return no_price_products if no_price_products else []
            
            return []
        
        except Exception as e:
            self.stats['errors'].append(f"Error fetching original SKU {original_sku}: {str(e)}")
            return []
    
    def get_all_products_needing_pricing(self):
        """Get all WordPress products that need pricing, grouped by original_sku - FAST BATCH METHOD"""
        try:
            print(f"\n🔍 Loading all WordPress products to check pricing status...")
            
            products_by_sku = {}
            page = 1
            
            params = {"per_page": 100, "page": page, "status": "publish"}
            if self.category_id:
                params["category"] = self.category_id

            while True:
                response = self.wcapi.get("products", params=params)
                
                if response.status_code != 200 or not response.json():
                    break
                
                products = response.json()
                if not products:
                    break
                
                # Process each product
                for product in products:
                    # Get original_sku from metadata
                    original_sku = None
                    meta_data = product.get('meta_data', [])
                    for meta in meta_data:
                        if meta.get('key') == 'original_sku':
                            original_sku = meta.get('value')
                            break
                    
                    if original_sku:
                        original_sku = str(original_sku).strip()
                        
                        # Check if product needs pricing
                        regular_price = product.get('regular_price', '')
                        needs_pricing = not regular_price or regular_price == '0' or regular_price == '0.00'
                        
                        if original_sku not in products_by_sku:
                            products_by_sku[original_sku] = {
                                'needs_pricing': [],
                                'already_priced': [],
                                'total_count': 0
                            }
                        
                        products_by_sku[original_sku]['total_count'] += 1
                        
                        if needs_pricing:
                            products_by_sku[original_sku]['needs_pricing'].append(product)
                        else:
                            products_by_sku[original_sku]['already_priced'].append(product)
                
                print(f"   📄 Processed page {page}: {len(products)} products")
                page += 1
                params["page"] = page
                
                # Safety limit
                if page > 200:
                    print("   ⚠️ Reached page limit (200), stopping")
                    break
            
            total_products = sum(data['total_count'] for data in products_by_sku.values())
            needs_pricing_count = sum(len(data['needs_pricing']) for data in products_by_sku.values())
            already_priced_count = sum(len(data['already_priced']) for data in products_by_sku.values())
            
            print(f"✅ Loaded {total_products} products across {len(products_by_sku)} unique SKUs")
            print(f"   📦 Products needing pricing: {needs_pricing_count}")
            print(f"   ✅ Products already priced: {already_priced_count}")
            
            return products_by_sku
        
        except Exception as e:
            print(f"❌ Error loading products: {e}")
            return {}
    
    def update_product_price(self, product_id, price, sku):
        """Update product price in WooCommerce"""
        try:
            price_str = f"{price:.2f}"
            
            response = self.wcapi.put(f"products/{product_id}", {
                "regular_price": price_str
            })
            
            if response.status_code == 200:
                return True
            else:
                self.stats['errors'].append(f"Failed to update {sku}: {response.status_code}")
                return False
        
        except Exception as e:
            self.stats['errors'].append(f"Error updating {sku}: {str(e)}")
            return False
    
    def update_multiple_products_price(self, products, price, original_sku):
        """Update price for multiple products with same original SKU"""
        updated_count = 0
        
        for product in products:
            try:
                if self.update_product_price(product['id'], price, f"{original_sku} (WP SKU: {product['sku']})"):
                    updated_count += 1
            except Exception as e:
                self.stats['errors'].append(f"Error updating product {product['id']} for original SKU {original_sku}: {str(e)}")
        
        return updated_count
    
    def update_prices_optimized(self, test_mode=False, test_limit=None):
        """
        Optimized price update: WordPress-first approach
        
        Args:
            test_mode: If True, only update first N SKUs
            test_limit: Number of SKUs to update in test mode
        """
        
        # Step 1: Load all products and group by SKU in one go (MUCH FASTER!)
        products_by_sku = self.get_all_products_needing_pricing()
        if not products_by_sku:
            print("❌ No products found in WordPress")
            return
        
        unique_skus = sorted(products_by_sku.keys())
        self.stats['total_in_db'] = len(unique_skus)
        
        # Step 2: Filter for test mode
        if test_mode and test_limit:
            unique_skus = unique_skus[:test_limit]
            print(f"\n🔧 TEST MODE: Processing first {test_limit} SKUs only\n")
        
        print(f"\n{'='*60}")
        print(f"⚡ FAST Batch Processing {len(unique_skus)} Unique SKUs")
        print(f"{'='*60}\n")
        
        # Step 3: Process each SKU (no individual API calls - data already loaded!)
        for sku in tqdm(unique_skus, desc="Processing SKUs"):
            # Fast Excel lookup
            if sku not in self.pricing_lookup:
                self.stats['not_found_in_excel'] += 1
                self.stats['skipped'].append(f"{sku} (no price in Excel)")
                self.log_no_price_sku(sku)
                continue
            
            price = self.pricing_lookup[sku]
            sku_data = products_by_sku[sku]
            
            # Products that need pricing (already identified in batch load)
            products_to_update = sku_data['needs_pricing']
            
            if products_to_update:
                # Update all products that need pricing
                updated_count = self.update_multiple_products_price(products_to_update, price, sku)
                if updated_count > 0:
                    self.stats['prices_updated'] += updated_count
            else:
                # All products already have pricing
                if sku_data['total_count'] > 0:
                    self.stats['no_pricing_needed'] += 1
            
            # Minimal rate limiting since we're not querying, just updating
            time.sleep(0.1)
        
        print("\n")
    
    def print_summary(self):
        """Print update summary"""
        print(f"\n{'='*60}")
        print("WordPress-First Price Update Summary")
        print(f"{'='*60}")
        print(f"Unique SKUs in WordPress:     {self.stats['total_in_db']}")
        print(f"Pricing records in Excel:     {self.stats['total_in_excel']}")
        print(f"WordPress products updated:   {self.stats['prices_updated']}")
        print(f"SKUs not in Excel:            {self.stats['not_found_in_excel']}")
        print(f"SKUs not found in WP:         {self.stats['not_found_in_wp']}")
        print(f"Products already priced:      {self.stats['no_pricing_needed']}")
        print(f"Errors:                       {len(self.stats['errors'])}")
        print(f"{'='*60}\n")
        print("ℹ️  WordPress-first approach: Only processes SKUs that exist in WordPress")
        print("   Multiple WordPress products may be updated per Oscar SKU")
        
        if self.stats['not_found_in_excel'] > 0:
            print(f"\n⚠ {self.stats['not_found_in_excel']} Oscar SKUs have no pricing in Excel")
            print(f"   📝 Missing SKUs logged to: {self.no_price_log}")
            
        if self.stats['no_pricing_needed'] > 0:
            print(f"\n✅ {self.stats['no_pricing_needed']} Oscar SKUs already have pricing in WordPress")
            
        if self.stats['not_found_in_wp'] > 0:
            print(f"\n⚠ {self.stats['not_found_in_wp']} SKUs had issues in WordPress")
            print("  (This should be rare with WordPress-first approach)")
        
        if self.stats['errors']:
            print(f"\n⚠ {len(self.stats['errors'])} errors encountered:")
            for error in self.stats['errors'][:10]:
                print(f"  - {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more")
        
        if self.stats['prices_updated'] > 0:
            print(f"\n✅ Successfully updated {self.stats['prices_updated']} WordPress product prices!")
            efficiency = (self.stats['total_in_db'] - self.stats['not_found_in_excel']) / self.stats['total_in_db'] * 100 if self.stats['total_in_db'] > 0 else 0
            print(f"📊 Coverage: {efficiency:.1f}% of WordPress SKUs have pricing in Excel")


def main():
    """Main price update function"""
    
    # Paths
    excel_file = base_dir / 'PRCJUL25.xlsx'
    
    if not excel_file.exists():
        print(f"\n✗ Excel file not found: {excel_file}")
        print("Please ensure PRCJUL25.xlsx is in the project root directory.")
        return
    
    # Load keys (matching keys.txt format: label line then value line)
    keys_file = base_dir / 'keys.txt'
    consumer_key = None
    consumer_secret = None
    with open(keys_file, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f if l.strip()]
    for i, line in enumerate(lines):
        if 'Consumer key' in line and i + 1 < len(lines):
            consumer_key = lines[i + 1]
        if 'Consumer secret' in line and i + 1 < len(lines):
            consumer_secret = lines[i + 1]
    
    # Initialize API
    wcapi = API(
        url=WORDPRESS_URL,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        version="wc/v3",
        timeout=30
    )
    
    print("\n" + "="*60)
    print("WooCommerce Price Update - Phase 4 (WordPress-First)")
    print("="*60)
    # Serial to filter by — LSH14C4C5NA129710 = WP category ID 7301
    SERIAL = 'LSH14C4C5NA129710'
    SERIAL_CATEGORY_ID = 7301

    print(f"WordPress URL: {WORDPRESS_URL}")
    print(f"Excel file: {excel_file.name}")
    print(f"Filtering to serial: {SERIAL} (category ID {SERIAL_CATEGORY_ID})")
    
    # Test connection
    try:
        response = wcapi.get("products", params={"per_page": 1})
        if response.status_code != 200:
            print("\n✗ API connection failed")
            return
        print("✓ API connection successful")
    except Exception as e:
        print(f"\n✗ API connection error: {str(e)}")
        return
    
    # Create updater — scoped to LSH14C4C5NA129710 (category 7301)
    updater = PriceUpdater(excel_file, wcapi, category_id=SERIAL_CATEGORY_ID)
    
    # Load pricing data into memory
    try:
        updater.load_pricing_data()
    except Exception as e:
        print(f"\n✗ Error loading Excel file: {str(e)}")
        return
    
    # Ask for test mode
    test_mode = input("\nRun in test mode? (y/N): ").strip().lower() == 'y'
    test_limit = None
    if test_mode:
        try:
            test_limit = int(input("Enter number of SKUs to test (default 10): ") or "10")
        except:
            test_limit = 10
    
    print(f"\n⚠️  This will update prices using WordPress-first approach")
    print(f"   Excel pricing records: {updater.stats['total_in_excel']}")
    print(f"   Will query WordPress for all imported original_sku metadata")
    
    confirm = input("\nPress Enter to continue or Ctrl+C to cancel: ")
    
    # Update prices using optimized approach
    updater.update_prices_optimized(
        test_mode=test_mode, 
        test_limit=test_limit
    )
    
    # Print summary
    updater.print_summary()
    
    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    print("1. Check updated products in WooCommerce")
    print("2. Run without test_mode for full update")
    print("3. The optimized approach is much faster!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
