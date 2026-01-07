"""
Test extraction - 10 products with mix of PNG and SVG diagrams
"""
import sys
sys.path.append('.')

from scripts.extract_data import extract_parts_from_html, detect_variations
from pathlib import Path
import json

def main():
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / 'LSFAL11A4PA157987'
    
    # Select specific diagrams: some with PNG, some SVG-only
    test_diagrams = [
        'air intake system/Air filter.html',  # Has PNG
        'brakes/Front Brakes.html',  # Has PNG
        'antenna/Antenna.html',  # Has PNG
        'body lower structure/body lower stucture.html',  # SVG only (failed PNG)
        'body upper structure/Baffle Plate-Ware.html',  # SVG only (failed PNG)
        'bumpers,fascia & grille/Front Bumper.html',  # SVG only (failed PNG)
        'bumpers,fascia & grille/Grille.html',  # SVG only (failed PNG)
    ]
    
    all_products = []
    
    print("\n" + "="*60)
    print("Test Extraction - Mixed PNG/SVG Diagrams")
    print("="*60 + "\n")
    
    for diagram_path in test_diagrams:
        html_file = data_dir / diagram_path
        
        if not html_file.exists():
            print(f"⚠ Not found: {diagram_path}")
            continue
        
        print(f"Processing: {diagram_path}")
        
        # Extract parts
        parts = extract_parts_from_html(
            html_file,
            serial_number='LSFAL11A4PA157987',
            diagram_code=html_file.stem
        )
        
        if parts:
            # Detect variations
            products = detect_variations(parts)
            all_products.extend(products)
            print(f"  Found {len(products)} products ({len(parts)} parts)")
        
        # Stop once we have at least 10 products
        if len(all_products) >= 10:
            break
    
    # Limit to exactly 10
    all_products = all_products[:10]
    
    # Save to test file
    output_file = base_dir / 'data' / 'extracted' / 'test_mixed_images.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'products': all_products,
            'total_count': len(all_products),
            'extraction_date': '2026-01-06'
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"Extraction Complete!")
    print(f"{'='*60}")
    print(f"Total products: {len(all_products)}")
    print(f"Saved to: {output_file.relative_to(base_dir)}")
    print(f"\nDiagrams processed:")
    
    # Count by diagram
    diagrams = {}
    for p in all_products:
        diag = p.get('diagram_code', 'Unknown')
        diagrams[diag] = diagrams.get(diag, 0) + 1
    
    for diag, count in diagrams.items():
        print(f"  {diag}: {count} products")
    
    print(f"\n{'='*60}\n")

if __name__ == '__main__':
    main()
