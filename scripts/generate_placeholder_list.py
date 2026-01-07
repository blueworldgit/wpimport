"""
Generate list of failed diagram conversions for placeholder assignment
"""
from pathlib import Path
import json

def main():
    """Create list of diagrams that need placeholder images"""
    base_dir = Path(__file__).resolve().parent.parent
    html_dir = base_dir / 'LSFAL11A4PA157987'
    png_dir = base_dir / 'images' / 'converted'
    output_file = base_dir / 'data' / 'failed_conversions.json'
    
    # Get all HTML files
    html_files = []
    for html_file in html_dir.rglob('*.html'):
        html_files.append(html_file)
    
    # Get all PNG files
    png_files = set()
    for png_file in png_dir.glob('*.png'):
        png_files.add(png_file.stem)
    
    # Find missing files
    failed_diagrams = []
    for html_file in html_files:
        diagram_name = html_file.stem.replace(' ', '_')
        expected_png = f"LSFAL11A4PA157987_{diagram_name}"
        
        if expected_png not in png_files:
            category = html_file.parent.name
            failed_diagrams.append({
                'html_file': html_file.name,
                'diagram_name': html_file.stem,
                'category': category,
                'png_filename': f"{expected_png}.png"
            })
    
    # Sort by category
    failed_diagrams.sort(key=lambda x: (x['category'], x['diagram_name']))
    
    # Save to JSON
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(failed_diagrams, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"Failed Conversions Report")
    print(f"{'='*60}\n")
    print(f"Total failed: {len(failed_diagrams)}")
    print(f"Output saved to: {output_file.relative_to(base_dir)}\n")
    
    # Create a simple text list for easy reference
    text_file = base_dir / 'data' / 'failed_diagrams_list.txt'
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write("DIAGRAMS NEEDING PLACEHOLDER IMAGES\n")
        f.write("="*60 + "\n\n")
        
        current_category = None
        for item in failed_diagrams:
            if item['category'] != current_category:
                current_category = item['category']
                f.write(f"\n{current_category.upper()}\n")
                f.write("-" * 60 + "\n")
            
            f.write(f"  • {item['diagram_name']}\n")
        
        f.write(f"\n{'='*60}\n")
        f.write(f"Total: {len(failed_diagrams)} diagrams need placeholders\n")
    
    print(f"Text list saved to: {text_file.relative_to(base_dir)}\n")
    
    # Print summary by category
    print("Failed diagrams by category:")
    categories = {}
    for item in failed_diagrams:
        cat = item['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")
    
    print(f"\n{'='*60}")
    print("\nNext steps:")
    print("1. These 24 diagrams will use placeholder images")
    print("2. Run full product import")
    print("3. Products will be created with placeholder images")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
