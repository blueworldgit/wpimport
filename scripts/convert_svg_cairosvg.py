"""
Convert SVG files to PNG using cairosvg
"""
import cairosvg
from pathlib import Path
from tqdm import tqdm
import xml.etree.ElementTree as ET
import re

def get_svg_dimensions(svg_path):
    """Extract SVG dimensions from viewBox or width/height attributes"""
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        
        # Try to get viewBox
        viewbox = root.get('viewBox')
        if viewbox:
            # viewBox format: "minX minY width height"
            parts = re.split(r'[,\s]+', viewbox.strip())
            if len(parts) >= 4:
                width = float(parts[2])
                height = float(parts[3])
                return width, height
        
        # Try width/height attributes
        width_str = root.get('width')
        height_str = root.get('height')
        if width_str and height_str:
            # Remove units like 'px', 'pt', etc.
            width = float(re.sub(r'[^0-9.]', '', width_str))
            height = float(re.sub(r'[^0-9.]', '', height_str))
            return width, height
            
    except Exception as e:
        pass
    
    return None, None

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
        error_msg = str(e)
        if 'size is undefined' in error_msg.lower():
            # Try to extract dimensions and add them to SVG
            svg_width, svg_height = get_svg_dimensions(svg_path)
            
            if svg_width and svg_height:
                try:
                    # Read SVG content
                    svg_content = svg_path.read_text(encoding='utf-8')
                    
                    # Calculate output dimensions maintaining aspect ratio
                    aspect_ratio = svg_height / svg_width
                    output_height = int(width * aspect_ratio)
                    
                    # Convert with explicit dimensions
                    cairosvg.svg2png(
                        bytestring=svg_content.encode('utf-8'),
                        write_to=str(png_path),
                        output_width=width,
                        output_height=output_height
                    )
                    return True
                except Exception as e2:
                    print(f"\n❌ Error converting {svg_path.name} (retry failed): {e2}")
                    return False
            else:
                # Use default dimensions as last resort
                try:
                    svg_content = svg_path.read_text(encoding='utf-8')
                    cairosvg.svg2png(
                        bytestring=svg_content.encode('utf-8'),
                        write_to=str(png_path),
                        output_width=width,
                        output_height=width  # Square default
                    )
                    return True
                except Exception as e3:
                    print(f"\n❌ Error converting {svg_path.name}: {e}")
                    return False
        else:
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
