"""
Check which diagrams have SVG vs PNG
"""
import json
from pathlib import Path

# Load test data
with open('data/extracted/extracted_data_test.json', 'r') as f:
    products = json.load(f)

# Check image availability
images_dir = Path('images/converted')
diagram_info = {}

for product in products[:20]:
    diagram_name = product['diagram_file'].replace('.html', '')
    diagram_code = product['diagram_code']
    
    if diagram_name not in diagram_info:
        # Check for PNG
        png_path = images_dir / f"LSFAL11A4PA157987_{diagram_name}.png"
        svg_path = images_dir / f"LSFAL11A4PA157987_{diagram_name}.svg"
        
        if png_path.exists():
            img_type = 'PNG'
        elif svg_path.exists():
            img_type = 'SVG'
        else:
            img_type = 'NONE'
        
        diagram_info[diagram_name] = {
            'code': diagram_code,
            'type': img_type,
            'file': diagram_name
        }

print("\nDiagram Image Types:")
print("-" * 60)
for name, info in diagram_info.items():
    print(f"{info['code']:15} {info['type']:5} {name}")
