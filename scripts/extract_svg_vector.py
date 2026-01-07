"""
Extract SVG from HTML and save as clean SVG file for WordPress vector upload
"""
import os
import sys
from pathlib import Path
from bs4 import BeautifulSoup
import re

# Add parent directory to path
base_dir = Path(__file__).parent.parent
sys.path.insert(0, str(base_dir))

def extract_svg_from_html(html_path, output_dir):
    """Extract SVG from HTML file and save as clean SVG"""
    try:
        # Read HTML
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'lxml')
        
        # Get serial number from path
        path_parts = html_path.parts
        serial_number = None
        for part in path_parts:
            if part.startswith('LSF') or (len(part) == 17 and part.isalnum()):
                serial_number = part
                break
        
        # Get diagram name
        diagram_name = html_path.stem.replace(' ', '_')
        
        # Build filename
        if serial_number:
            filename = f"{serial_number}_{diagram_name}.svg"
        else:
            filename = f"{diagram_name}.svg"
        
        # Find SVG element
        svg = soup.find('svg')
        if not svg:
            return None, "No SVG found"
        
        # Get SVG string
        svg_string = str(svg)
        
        # Clean up SVG attributes for better WordPress compatibility
        # Ensure proper XML namespace
        if 'xmlns' not in svg_string:
            svg_string = svg_string.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ')
        
        # Output path
        output_path = output_dir / filename
        
        # Write SVG file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_string)
        
        return output_path, filename
        
    except Exception as e:
        return None, f"Error: {str(e)}"

def main():
    """Extract specific SVG file"""
    
    # The file we want to extract
    html_file = base_dir / 'LSFAL11A4PA157987' / 'body interior & exterior electronics' / 'Body Interior & Exterior Electronics.html'
    output_dir = base_dir / 'images' / 'converted'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print("SVG Vector Extraction")
    print("="*60)
    print(f"\nExtracting from: {html_file.name}")
    
    result_path, info = extract_svg_from_html(html_file, output_dir)
    
    if result_path:
        file_size = result_path.stat().st_size / 1024  # KB
        print(f"\n✓ Success!")
        print(f"  Output: {result_path.name}")
        print(f"  Size: {file_size:.2f} KB")
        print(f"  Location: {result_path}")
        print("\n" + "="*60)
        print("Next Steps:")
        print("="*60)
        print("1. Test the SVG by opening it in a browser")
        print("2. Upload to WordPress Media Library")
        print("3. Use as product image (vectors scale perfectly!)")
        print("="*60 + "\n")
    else:
        print(f"\n✗ Failed: {info}\n")

if __name__ == "__main__":
    main()
