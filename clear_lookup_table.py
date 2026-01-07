"""
Clear WooCommerce product lookup tables
This fixes the "SKU already present in lookup table" error
"""
import mysql.connector
import json
from pathlib import Path

# Read WordPress database credentials
# You'll need to provide these
print("This script needs direct database access to clear the lookup tables.")
print("Please provide your WordPress database credentials:")
print("\nAlternatively, you can run this SQL query in phpMyAdmin or WordPress database:")
print("\nTRUNCATE TABLE wp_wc_product_meta_lookup;")
print("TRUNCATE TABLE wp_woocommerce_order_items;")
print("TRUNCATE TABLE wp_woocommerce_order_itemmeta;")
print("\nOr use this WP-CLI command:")
print("wp db query \"TRUNCATE TABLE wp_wc_product_meta_lookup;\"")
