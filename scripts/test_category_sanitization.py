#!/usr/bin/env python3
"""
Test category name sanitization to show before/after examples
"""
import re

def sanitize_category_name(name):
    """Sanitize category names for WooCommerce compatibility"""
    if not name:
        return "Uncategorized"
    
    # Remove diagram codes (JE123A001 - ) from category names
    name = re.sub(r'^[A-Z]{2}\d+[A-Z]?\d+\s*-\s*', '', name)
    
    # Replace problematic characters but keep full length
    sanitized = name.replace('&', 'and').replace('/', '-').replace('\\', '-')
    sanitized = sanitized.replace('(', '').replace(')', '').replace(',', '')
    
    # Clean up extra spaces and dashes
    sanitized = re.sub(r'\s+', ' ', sanitized)  # Multiple spaces -> single space
    sanitized = re.sub(r'-+', '-', sanitized)   # Multiple dashes -> single dash
    
    return sanitized.strip(' -')

# Test with actual category names from the error log
test_names = [
    "Body Interior & Exterior Electronics",
    "JE184A001 - Urea system",
    "JE843A001 - BatteryandElectrical Energy Storage",
    "JE321A001 - Front Interior HVAC Airflow", 
    "JE312A004 - Refrigerant Plumbing & Hardware-PHEV",
    "JE312A001 - Refrigerant Plumbing & Hardware",
    "JE830A001 - Body Interior & Exterior Electronics",
    "JE140A001 - Air filter",
    "JE222A001 - Rear Suspension",
    "Transmission CSC and Operating Mechanism(6MT back drive)",
    "Three Seats Arrangement for VAN Vehicle (Australia, New Zealand)"
]

print("Category Name Sanitization Examples:")
print("=" * 80)
print(f"{'Original':<50} | {'Sanitized':<30}")
print("-" * 80)

for name in test_names:
    sanitized = sanitize_category_name(name)
    print(f"{name:<50} | {sanitized:<30}")