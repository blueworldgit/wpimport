"""
Find diagrams that only have SVG (no PNG conversion)
These are the 24 corrupted diagrams
"""
import os
from pathlib import Path

# Get all HTML files
html_dir = Path('LSFAL11A4PA157987')
all_diagrams = []

for root, dirs, files in os.walk(html_dir):
    for file in files:
        if file.endswith('.html'):
            # Get relative path from html_dir
            rel_path = os.path.relpath(os.path.join(root, file), html_dir)
            diagram_name = rel_path.replace('.html', '')
            all_diagrams.append(diagram_name)

print(f"\nTotal diagrams found: {len(all_diagrams)}")

# Check which ones would be SVG-only (no PNG in images/converted/)
images_dir = Path('images/converted')
svg_only = []

for diagram in all_diagrams:
    png_file = f"LSFAL11A4PA157987_{diagram}.png"
    svg_file = f"LSFAL11A4PA157987_{diagram}.svg"
    
    png_path = images_dir / png_file
    svg_path = images_dir / svg_file
    
    # If SVG exists but PNG doesn't, it's SVG-only
    if not png_path.exists() and svg_path.exists():
        svg_only.append(diagram)

print(f"SVG-only diagrams: {len(svg_only)}")
print("\nFirst 10 SVG-only diagrams:")
print("="*80)
for i, diagram in enumerate(svg_only[:10], 1):
    print(f"{i:2d}. {diagram}")

# Now find products that use these diagrams
import json
data_file = Path('data/extracted/extracted_data_test.json')

if data_file.exists():
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    print("\n" + "="*80)
    print("Products using SVG-only diagrams (from test data):")
    print("="*80)
    
    svg_products = []
    for product in data['products']:
        diagram_file = product['diagram_file'].replace('.html', '')
        if diagram_file in svg_only:
            svg_products.append(product)
            print(f"SKU: {product['sku']:12} | {product['name'][:50]}")
            print(f"     Diagram: {diagram_file}")
            print()
    
    if not svg_products:
        print("(No test products use SVG-only diagrams)")
        print("\nYou need to extract products from these categories:")
        for diagram in svg_only[:5]:
            print(f"  - {diagram}")
