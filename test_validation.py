#!/usr/bin/env python3
"""
Test the enhanced category validation logic
"""
import sys
from pathlib import Path
base_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(base_dir))

# Import our enhanced script
from scripts.create_products import ProductCreator

# Test the problematic category
creator = ProductCreator('LSFAL11A4PA157987')
creator.connect()
creator.setup_woocommerce()

# Test validation of the problematic category
test_category = "Transmission Shift Actuation-AT-Electric vehicle"
print(f"🧪 Testing validation for: '{test_category}'")

result = creator.validate_category_exists(test_category)
if result:
    print(f"✅ SUCCESS: Found category ID {result}")
else:
    print(f"❌ FAILED: Category not found")

creator.close()