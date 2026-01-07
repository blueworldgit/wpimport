"""
Check which products are using SVG vs PNG images
"""
import json
from pathlib import Path

# Load test data
with open('data/extracted/extracted_data_test.json', 'r') as f:
    data = json.load(f)

products = data['products'][:10]
images_dir = Path('images/converted')

print("\nChecking image types for test products:")
print("="*80)

for i, product in enumerate(products, 1):
    sku = product['sku']
    diagram_name = product['diagram_file'].replace('.html', '')
    png_file = f"LSFAL11A4PA157987_{diagram_name}.png"
    svg_file = f"LSFAL11A4PA157987_{diagram_name}.svg"
    
    png_path = images_dir / png_file
    svg_path = images_dir / svg_file
    
    has_png = png_path.exists()
    has_svg = svg_path.exists()
    
    if has_png:
        img_type = "PNG"
    elif has_svg:
        img_type = "SVG (vector)"
    else:
        img_type = "NONE"
    
    status = "🔶 VECTOR" if img_type == "SVG (vector)" else "  "
    print(f"{status} [{i:2d}] SKU: {sku:12} | {diagram_name:30} | {img_type}")

print("="*80)
