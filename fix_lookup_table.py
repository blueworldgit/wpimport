"""
Fix WooCommerce Lookup Table - Clear SKU residue
Run this after cleanup_products.py to fix "SKU already present in lookup table" errors
"""
from woocommerce import API
import requests

# Production Configuration
WORDPRESS_URL = "https://maxusvanparts.co.uk"
WORDPRESS_USERNAME = "developer"
WORDPRESS_PASSWORD = "nIbM 6KlW sft3 hQyj OG4P ZYeI"
CONSUMER_KEY = "ck_1be77215f05ca7f848ac0ec16a6b68e76ced9302"
CONSUMER_SECRET = "cs_b2c2be6911c85fe9abc62b4ec5170b9ab746392e"

def fix_lookup_table():
    """Try to regenerate WooCommerce product lookup tables"""
    
    print("\n" + "="*60)
    print("WooCommerce Lookup Table Fix")
    print("="*60)
    print(f"WordPress URL: {WORDPRESS_URL}\n")
    
    wcapi = API(
        url=WORDPRESS_URL,
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET,
        version="wc/v3",
        timeout=30
    )
    
    # Try to use WooCommerce System Status Tools endpoint
    print("Attempting to regenerate product lookup tables via API...")
    
    try:
        # First try the system tools endpoint
        response = wcapi.post("system_status/tools/regenerate_product_lookup_tables", {})
        
        if response.status_code == 200:
            print("✓ Product lookup tables regenerated successfully!\n")
            return True
        else:
            print(f"⚠️  API method failed: {response.status_code}\n")
    except Exception as e:
        print(f"⚠️  API method failed: {e}\n")
    
    # If API doesn't work, provide manual instructions
    print("="*60)
    print("Manual Fix Required")
    print("="*60)
    print("\nThe lookup table needs to be cleared manually.")
    print("\nOption 1: Run SQL in phpMyAdmin or WordPress database:")
    print("-" * 60)
    print("TRUNCATE TABLE wp_wc_product_meta_lookup;")
    print("-" * 60)
    
    print("\nOption 2: Use WP-CLI (if you have SSH access):")
    print("-" * 60)
    print('wp db query "TRUNCATE TABLE wp_wc_product_meta_lookup;"')
    print("-" * 60)
    
    print("\nOption 3: WordPress Admin > WooCommerce > Status > Tools:")
    print("  - Find 'Product lookup tables'")
    print("  - Click 'Regenerate'")
    print("-" * 60)
    
    print("\nAfter running one of these, your import should work!\n")
    return False

if __name__ == "__main__":
    fix_lookup_table()
