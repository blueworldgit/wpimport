"""
Test single SVG diagram import
Process just Body_Interior_&_Exterior_Electronics to verify the process works
"""
import sys
from pathlib import Path
from import_svg_products import process_failed_diagram

# Test with single diagram
test_diagram = 'LSFAL11A4PA157987_Body_Interior_&_Exterior_Electronics.png'
data_dir = Path('LSFAL11A4PA157987')

print("\n" + "="*60)
print("Testing Single SVG Product Import")
print("="*60)
print(f"Diagram: {test_diagram}")
print("="*60 + "\n")

result = process_failed_diagram(test_diagram, data_dir)

print("\n" + "="*60)
print("Result")
print("="*60)

if result['success']:
    print("✓ SUCCESS!")
    print(f"  Media ID: {result['media_id']}")
    print(f"  Product ID: {result['product_id']}")
    print(f"\nView product at:")
    print(f"  https://maxusvanparts.co.uk/wp-admin/post.php?post={result['product_id']}&action=edit")
else:
    print("✗ FAILED")
    print(f"  Error: {result['error']}")

print("="*60 + "\n")
