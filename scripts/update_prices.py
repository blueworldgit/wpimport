"""
Price Update Script - Phase 4
Updates WooCommerce product prices from Excel file
"""
import sys
import pandas as pd
from pathlib import Path
from woocommerce import API
from tqdm import tqdm
import time

# Add parent directory to path for config
base_dir = Path(__file__).parent.parent
sys.path.insert(0, str(base_dir))

from config import WORDPRESS_URL

class PriceUpdater:
    def __init__(self, excel_file, wcapi):
        self.excel_file = excel_file
        self.wcapi = wcapi
        self.stats = {
            'total_in_excel': 0,
            'prices_updated': 0,
            'not_found': 0,
            'errors': [],
            'skipped': []
        }
    
    def load_pricing_data(self):
        """Load pricing data from Excel file"""
        print(f"\nLoading pricing data from: {self.excel_file}")
        
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
        
        self.stats['total_in_excel'] = len(df)
        
        print(f"✓ Loaded {len(df)} valid price records")
        print(f"  SKU range: {df['Part Number'].min()} to {df['Part Number'].max()}")
        print(f"  Price range: £{df['Retail Price'].min():.2f} to £{df['Retail Price'].max():.2f}")
        
        return df
    
    def get_product_by_sku(self, sku):
        """Get WooCommerce product by SKU"""
        try:
            response = self.wcapi.get("products", params={"sku": sku, "per_page": 1})
            
            if response.status_code == 200:
                products = response.json()
                if products:
                    return products[0]
            
            return None
        
        except Exception as e:
            self.stats['errors'].append(f"Error fetching SKU {sku}: {str(e)}")
            return None
    
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
    
    def update_variation_price(self, parent_id, variation_id, price, sku):
        """Update variation price in WooCommerce"""
        try:
            price_str = f"{price:.2f}"
            
            response = self.wcapi.put(f"products/{parent_id}/variations/{variation_id}", {
                "regular_price": price_str
            })
            
            if response.status_code == 200:
                return True
            else:
                self.stats['errors'].append(f"Failed to update variation {sku}: {response.status_code}")
                return False
        
        except Exception as e:
            self.stats['errors'].append(f"Error updating variation {sku}: {str(e)}")
            return False
    
    def search_in_variations(self, sku, price):
        """Search for SKU in product variations"""
        try:
            # Get all variable products
            page = 1
            while True:
                response = self.wcapi.get("products", params={
                    "type": "variable",
                    "per_page": 100,
                    "page": page
                })
                
                if response.status_code != 200 or not response.json():
                    break
                
                products = response.json()
                
                for product in products:
                    # Get variations for this product
                    var_response = self.wcapi.get(f"products/{product['id']}/variations", params={"per_page": 100})
                    
                    if var_response.status_code == 200:
                        variations = var_response.json()
                        
                        for variation in variations:
                            if variation.get('sku') == sku:
                                # Found it!
                                if self.update_variation_price(product['id'], variation['id'], price, sku):
                                    return True
                
                page += 1
                
                # Safety limit
                if page > 50:
                    break
            
            return False
        
        except Exception as e:
            self.stats['errors'].append(f"Error searching variations for {sku}: {str(e)}")
            return False
    
    def update_prices(self, df, test_mode=False, test_limit=None):
        """
        Update prices for all products in dataframe
        
        Args:
            df: DataFrame with pricing data
            test_mode: If True, only update first N products
            test_limit: Number of products to update in test mode
        """
        if test_mode and test_limit:
            df = df.head(test_limit)
            print(f"\n🔧 TEST MODE: Updating first {test_limit} products only\n")
        
        print(f"\n{'='*60}")
        print(f"Updating Prices for {len(df)} Products")
        print(f"{'='*60}\n")
        
        for index, row in tqdm(df.iterrows(), total=len(df), desc="Updating prices"):
            sku = row['Part Number']
            price = row['Retail Price']
            
            # First, try to find as simple product
            product = self.get_product_by_sku(sku)
            
            if product:
                # Found as simple product
                if self.update_product_price(product['id'], price, sku):
                    self.stats['prices_updated'] += 1
            else:
                # Not found as simple product, search in variations
                if self.search_in_variations(sku, price):
                    self.stats['prices_updated'] += 1
                else:
                    self.stats['not_found'] += 1
                    self.stats['skipped'].append(sku)
            
            # Rate limiting
            time.sleep(0.3)
        
        print("\n")
    
    def print_summary(self):
        """Print update summary"""
        print(f"\n{'='*60}")
        print("Price Update Summary")
        print(f"{'='*60}")
        print(f"Total SKUs in Excel:     {self.stats['total_in_excel']}")
        print(f"Prices updated:          {self.stats['prices_updated']}")
        print(f"Not found in WC:         {self.stats['not_found']}")
        print(f"Errors:                  {len(self.stats['errors'])}")
        print(f"{'='*60}\n")
        
        if self.stats['not_found'] > 0:
            print(f"\n⚠ {self.stats['not_found']} SKUs not found in WooCommerce")
            print("  (These products may not be imported yet)")
            if len(self.stats['skipped']) <= 20:
                print(f"  SKUs: {', '.join(self.stats['skipped'])}")
        
        if self.stats['errors']:
            print(f"\n⚠ {len(self.stats['errors'])} errors encountered:")
            for error in self.stats['errors'][:10]:
                print(f"  - {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more")
        
        if self.stats['prices_updated'] > 0:
            print(f"\n✓ Successfully updated {self.stats['prices_updated']} product prices!")


def main():
    """Main price update function"""
    
    # Paths
    excel_file = base_dir / 'PRCJUL25.xlsx'
    
    if not excel_file.exists():
        print(f"\n✗ Excel file not found: {excel_file}")
        print("Please ensure PRCJUL25.xlsx is in the project root directory.")
        return
    
    # Load keys
    keys_file = base_dir / 'keys.txt'
    with open(keys_file, 'r') as f:
        content = f.read().strip()
        lines = content.split('\n')
        consumer_key = None
        consumer_secret = None
        
        for i, line in enumerate(lines):
            if 'ck_' in line:
                consumer_key = line.strip()
            elif 'cs_' in line:
                consumer_secret = line.strip()
    
    # Initialize API
    wcapi = API(
        url=WORDPRESS_URL,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        version="wc/v3",
        timeout=30
    )
    
    print("\n" + "="*60)
    print("WooCommerce Price Update - Phase 4")
    print("="*60)
    print(f"WordPress URL: {WORDPRESS_URL}")
    print(f"Excel file: {excel_file.name}")
    
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
    
    # Create updater
    updater = PriceUpdater(excel_file, wcapi)
    
    # Load pricing data
    try:
        df = updater.load_pricing_data()
    except Exception as e:
        print(f"\n✗ Error loading Excel file: {str(e)}")
        return
    
    # Ask user confirmation
    print(f"\n⚠️  This will update prices for products in WooCommerce")
    print(f"   Matching {updater.stats['total_in_excel']} SKUs from Excel file")
    
    # Uncomment for production - require confirmation
    # confirm = input("\nType 'UPDATE' to confirm: ")
    # if confirm != 'UPDATE':
    #     print("\n✗ Cancelled. No prices were updated.")
    #     return
    
    # Get list of imported SKUs to update
    print("\n🔧 Running in TEST MODE - will update prices for currently imported products only")
    
    # Load imported SKUs
    extracted_file = base_dir / 'data' / 'extracted' / 'extracted_data_test.json'
    if extracted_file.exists():
        import json
        with open(extracted_file, 'r') as f:
            extracted_data = json.load(f)
        
        imported_skus = []
        for p in extracted_data['products']:
            if p['type'] == 'simple':
                imported_skus.append(p['sku'])
            else:
                for v in p['variations']:
                    imported_skus.append(v['sku'])
        
        # Filter Excel data to only imported SKUs
        df = df[df['Part Number'].isin(imported_skus)]
        print(f"✓ Found {len(df)} pricing records for imported products")
    
    confirm = input("\nPress Enter to continue or Ctrl+C to cancel: ")
    
    # Update prices
    updater.update_prices(df, test_mode=False)
    
    # Print summary
    updater.print_summary()
    
    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    print("1. Check updated products in WooCommerce")
    print("2. If everything looks good, run again without test_mode")
    print("3. Update script line 214 to remove test_mode for full update")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
