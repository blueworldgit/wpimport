"""
Identify which diagrams failed to convert to PNG
"""
from pathlib import Path

def main():
    """Compare HTML files with PNG files to find missing conversions"""
    base_dir = Path(__file__).resolve().parent.parent
    html_dir = base_dir / 'LSFAL11A4PA157987'
    png_dir = base_dir / 'images' / 'converted'
    
    # Get all HTML files
    html_files = []
    for html_file in html_dir.rglob('*.html'):
        html_files.append(html_file)
    
    # Get all PNG files
    png_files = set()
    for png_file in png_dir.glob('*.png'):
        png_files.add(png_file.stem)  # filename without extension
    
    print(f"\n{'='*60}")
    print(f"Conversion Status Report")
    print(f"{'='*60}\n")
    print(f"Total HTML files: {len(html_files)}")
    print(f"Total PNG files: {len(png_files)}")
    print(f"Missing: {len(html_files) - len(png_files)}")
    print(f"\n{'='*60}")
    
    # Find missing files
    missing = []
    for html_file in html_files:
        diagram_name = html_file.stem.replace(' ', '_')
        expected_png = f"LSFAL11A4PA157987_{diagram_name}"
        
        if expected_png not in png_files:
            category = html_file.parent.name
            missing.append({
                'file': html_file.name,
                'category': category,
                'expected_png': f"{expected_png}.png"
            })
    
    if missing:
        print(f"\n⚠ {len(missing)} diagrams failed to convert:\n")
        for item in sorted(missing, key=lambda x: x['category']):
            print(f"  [{item['category']}]")
            print(f"    HTML: {item['file']}")
            print(f"    Expected PNG: {item['expected_png']}")
            print()
    else:
        print("\n✓ All diagrams successfully converted!\n")
    
    print(f"{'='*60}\n")
    
    # Summary by category
    if missing:
        print("Categories affected:")
        categories = {}
        for item in missing:
            cat = item['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in sorted(categories.items()):
            print(f"  {cat}: {count} missing")
        print()

if __name__ == '__main__':
    main()
