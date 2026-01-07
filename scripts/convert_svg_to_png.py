"""
SVG to PNG Conversion Script - Phase 5
Extracts SVG from HTML files and converts to PNG images
"""
import os
import sys
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
import io
import re
from tqdm import tqdm

# Add parent directory to path
base_dir = Path(__file__).parent.parent
sys.path.insert(0, str(base_dir))

class SVGConverter:
    def __init__(self, data_dir, output_dir, error_log='conversion_errors.txt'):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.error_log_path = Path(error_log)
        self.stats = {
            'total_files': 0,
            'converted': 0,
            'skipped': 0,
            'errors': [],
            'failed_files': []  # Store filenames that failed
        }
    
    def extract_diagram_code(self, soup):
        """Extract diagram code (e.g., JE140A001) from HTML"""
        try:
            # Look for legend-header with diagram code
            legend_header = soup.find('div', class_='legend-header')
            if legend_header:
                legend_title = legend_header.find('div', class_='legend-title')
                if legend_title:
                    text = legend_title.get_text(strip=True)
                    # Extract code like JE140A001
                    match = re.search(r'([A-Z]{2}\d+[A-Z]?\d+)', text)
                    if match:
                        return match.group(1)
            
            return None
        except Exception as e:
            return None
    
    def svg_to_png_pillow(self, svg_string, output_path, width=2000):
        """
        Convert SVG to PNG using svglib + reportlab
        """
        try:
            from svglib.svglib import svg2rlg
            from reportlab.graphics import renderPM
            import warnings
            
            # Suppress warnings and stderr (font errors)
            warnings.filterwarnings('ignore')
            
            # Save SVG temporarily
            svg_temp = output_path.with_suffix('.svg')
            with open(svg_temp, 'w', encoding='utf-8') as f:
                f.write(svg_string)
            
            # Suppress stderr to hide font errors
            import contextlib
            with contextlib.redirect_stderr(io.StringIO()):
                # Convert SVG to ReportLab drawing
                drawing = svg2rlg(str(svg_temp))
                
                if drawing:
                    # Calculate scale to achieve target width
                    scale = width / drawing.width if drawing.width > 0 else 1
                    drawing.width = width
                    drawing.height = drawing.height * scale
                    drawing.scale(scale, scale)
                    
                    # Render to PNG
                    renderPM.drawToFile(drawing, str(output_path), fmt='PNG', dpi=150)
            
            # Remove temp SVG
            svg_temp.unlink()
            
            if drawing:
                return output_path
            else:
                raise Exception("Failed to parse SVG")
            
        except Exception as e:
            raise Exception(f"Error converting SVG: {str(e)}")
    
    def process_html_file(self, html_path):
        """Extract SVG from HTML and convert to PNG"""
        filename = None  # Initialize to track intended filename
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'lxml')
            
            # Get serial number from path (e.g., LSFAL11A4PA157987)
            # Path structure: LSFAL11A4PA157987/category/diagram.html
            path_parts = html_path.parts
            serial_number = None
            for part in path_parts:
                # Look for folder that starts with LSFAL or similar VIN pattern
                if part.startswith('LSF') or (len(part) == 17 and part.isalnum()):
                    serial_number = part
                    break
            
            # Get diagram name
            diagram_name = html_path.stem.replace(' ', '_')
            
            # Build filename: SerialNumber_DiagramName
            if serial_number:
                filename = f"{serial_number}_{diagram_name}.png"
            else:
                filename = f"{diagram_name}.png"
            
            # Find SVG element
            svg = soup.find('svg')
            if not svg:
                self.stats['skipped'] += 1
                return None, "No SVG found"
            
            # Get SVG string
            svg_string = str(svg)
            
            # Output filename with serial
            output_file = self.output_dir / filename
            
            # Check if already exists
            if output_file.exists():
                self.stats['skipped'] += 1
                return None, "Already exists"
            
            # Convert to PNG (or save SVG for now)
            result_path = self.svg_to_png_pillow(svg_string, output_file)
            
            self.stats['converted'] += 1
            return result_path, filename.replace('.png', '')
            
        except Exception as e:
            error_msg = f"Error processing {html_path.name}: {str(e)}"
            self.stats['errors'].append(error_msg)
            # Log the intended filename even though conversion failed
            if filename:
                self.stats['failed_files'].append(filename)
            return None, str(e)
    
    def convert_batch(self, limit=None):
        """Convert SVG files in batch"""
        # Find all HTML files
        html_files = list(self.data_dir.rglob('*.html'))
        self.stats['total_files'] = len(html_files)
        
        if limit:
            html_files = html_files[:limit]
            print(f"\n🔧 Converting first {limit} diagrams only")
        
        print(f"\n{'='*60}")
        print(f"Converting {len(html_files)} SVG Diagrams to PNG")
        print(f"{'='*60}")
        print(f"Output directory: {self.output_dir}\n")
        
        results = []
        
        for html_file in tqdm(html_files, desc="Converting diagrams"):
            result_path, info = self.process_html_file(html_file)
            if result_path:
                results.append({
                    'html_file': str(html_file),
                    'output_file': str(result_path),
                    'diagram_code': info
                })
        
        return results
    
    def print_summary(self):
        """Print conversion summary"""
        print(f"\n{'='*60}")
        print("Conversion Summary")
        print(f"{'='*60}")
        print(f"Total HTML files:        {self.stats['total_files']}")
        print(f"Converted:               {self.stats['converted']}")
        print(f"Skipped:                 {self.stats['skipped']}")
        print(f"Errors:                  {len(self.stats['errors'])}")
        print(f"{'='*60}\n")
        
        if self.stats['errors']:
            print("⚠ Errors:")
        
        # Write failed filenames to log file
        if self.stats['failed_files']:
            with open(self.error_log_path, 'w', encoding='utf-8') as f:
                f.write("# Failed Image Conversions\n")
                f.write(f"# Total failed: {len(self.stats['failed_files'])}\n")
                f.write(f"# Generated: {Path(__file__).name}\n\n")
                for failed_file in self.stats['failed_files']:
                    f.write(f"{failed_file}\n")
            print(f"\n📝 Failed filenames written to: {self.error_log_path}")
            print(f"   Total failed: {len(self.stats['failed_files'])}")
            for error in self.stats['errors'][:10]:
                print(f"  - {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more")


def main():
    """Main conversion function"""
    
    # Add GTK3 to PATH for Windows PNG conversion
    import os
    gtk3_path = r"C:\Program Files\GTK3-Runtime Win64\bin"
    if os.path.exists(gtk3_path):
        os.environ['PATH'] = gtk3_path + os.pathsep + os.environ.get('PATH', '')
        print(f"✓ Added GTK3 to PATH: {gtk3_path}")
    
    # Paths
    data_dir = base_dir / 'LSFAL11A4PA157987'
    output_dir = base_dir / 'images' / 'converted'
    
    print("\n" + "="*60)
    print("SVG to PNG Conversion - Phase 5")
    print("="*60)
    print("\nUsing svglib + reportlab for PNG conversion")
    print("="*60)
    
    # Create converter
    converter = SVGConverter(data_dir, output_dir)
    
    # Convert all diagrams
    results = converter.convert_batch(limit=None)
    
    # Print summary
    converter.print_summary()
    
    if results:
        print("\n✓ Sample converted files:")
        for result in results[:5]:
            print(f"  {result['diagram_code']}: {Path(result['output_file']).name}")
    
    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    print("1. Check converted files in: images/converted/")
    print("2. Install cairosvg for full PNG conversion:")
    print("   pip install cairosvg")
    print("3. Re-run script for PNG conversion")
    print("4. Upload PNGs to WordPress and update products")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
