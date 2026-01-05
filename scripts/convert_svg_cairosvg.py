"""
Convert SVG files to PNG using cairosvg
"""
import cairosvg
from pathlib import Path
from tqdm import tqdm

def convert_svg_to_png(svg_path, png_path, width=2000):
    """Convert single SVG file to PNG"""
    try:
        cairosvg.svg2png(
            url=str(svg_path),
            write_to=str(png_path),
            output_width=width
        )
        return True
    except Exception as e:
        print(f"\n❌ Error converting {svg_path.name}: {e}")
        return False

def main():
    """Convert all SVG files in images/converted to PNG"""
    base_dir = Path(__file__).resolve().parent.parent
    svg_dir = base_dir / 'images' / 'converted'
    
    # Get all SVG files
    svg_files = list(svg_dir.glob('*.svg'))
    
    if not svg_files:
        print("\n⚠ No SVG files found!")
        return
    
    print(f"\n{'='*60}")
    print(f"Converting {len(svg_files)} SVG files to PNG using cairosvg")
    print(f"{'='*60}\n")
    
    converted = 0
    errors = 0
    
    for svg_file in tqdm(svg_files, desc="Converting"):
        png_file = svg_file.with_suffix('.png')
        
        if convert_svg_to_png(svg_file, png_file):
            converted += 1
        else:
            errors += 1
    
    print(f"\n{'='*60}")
    print(f"Conversion Complete!")
    print(f"{'='*60}")
    print(f"✓ Converted: {converted}")
    print(f"✗ Errors: {errors}")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
