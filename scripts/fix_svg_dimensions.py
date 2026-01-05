"""
Fix SVG files that are missing width/height attributes
"""
from pathlib import Path
from bs4 import BeautifulSoup
import re

def fix_svg_dimensions(svg_path, default_width=2000, default_height=1500):
    """Add width/height attributes to SVG if missing"""
    try:
        with open(svg_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'xml')
        svg = soup.find('svg')
        
        if not svg:
            return False, "No SVG element found"
        
        # Check if width/height already exist
        if svg.get('width') and svg.get('height'):
            return False, "Already has dimensions"
        
        # Try to get dimensions from viewBox
        viewbox = svg.get('viewBox')
        if viewbox:
            parts = viewbox.split()
            if len(parts) == 4:
                width = parts[2]
                height = parts[3]
            else:
                width = default_width
                height = default_height
        else:
            # Use default dimensions
            width = default_width
            height = default_height
        
        # Add width and height attributes
        svg['width'] = str(width)
        svg['height'] = str(height)
        
        # Save fixed SVG
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        return True, f"Fixed: {width}x{height}"
        
    except Exception as e:
        return False, f"Error: {e}"

def main():
    """Fix all SVG files in converted directory"""
    base_dir = Path(__file__).resolve().parent.parent
    svg_dir = base_dir / 'images' / 'converted'
    
    # Get all SVG files
    svg_files = list(svg_dir.glob('*.svg'))
    
    if not svg_files:
        print("\n⚠ No SVG files found!")
        return
    
    print(f"\n{'='*60}")
    print(f"Fixing {len(svg_files)} SVG files")
    print(f"{'='*60}\n")
    
    fixed = 0
    skipped = 0
    errors = 0
    
    for svg_file in svg_files:
        success, message = fix_svg_dimensions(svg_file)
        
        if success:
            print(f"✓ {svg_file.name}: {message}")
            fixed += 1
        elif "Already has dimensions" in message:
            skipped += 1
        else:
            print(f"✗ {svg_file.name}: {message}")
            errors += 1
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Fixed: {fixed}")
    print(f"  Skipped (already OK): {skipped}")
    print(f"  Errors: {errors}")
    print(f"{'='*60}\n")
    
    if fixed > 0:
        print("Now run: python scripts/convert_svg_cairosvg.py")
        print("to convert the fixed SVG files to PNG\n")

if __name__ == '__main__':
    main()
