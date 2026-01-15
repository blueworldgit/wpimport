#!/usr/bin/env python3
"""
Show summary of products without images
"""
import json

# Load the results
with open('products_without_images.json', 'r') as f:
    products = json.load(f)

print(f"📊 SUMMARY: Products Without Images")
print(f"=" * 50)
print(f"Total products without images: {len(products)}")
print(f"\nSample products:")
print(f"-" * 50)

for i, product in enumerate(products[:10], 1):
    print(f"{i:2d}. {product['sku']:<25} | {product['name'][:40]}")

if len(products) > 10:
    print(f"... and {len(products) - 10} more")

print(f"\n💾 Full list saved in: products_without_images.json")