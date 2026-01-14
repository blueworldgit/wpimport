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
        
        # Add mapping file for SKU-to-vector tracking
        self.mapping_file = self.output_dir / 'sku_to_vector_mapping.json'
        self.vector_mapping = {}
        
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
    
    def fix_svg_dimensions(self, svg_string):
        """Fix SVG that has undefined dimensions"""
        try:
            from bs4 import BeautifulSoup
            import re
            
            # Parse SVG
            soup = BeautifulSoup(svg_string, 'xml')
            svg_tag = soup.find('svg')
            
            if not svg_tag:
                return svg_string
            
            # Check if SVG already has proper dimensions
            has_width = svg_tag.get('width') is not None
            has_height = svg_tag.get('height') is not None
            has_viewbox = svg_tag.get('viewBox') is not None
            
            if has_width and has_height:
                return str(soup)  # Already has dimensions
            
            # Try to extract dimensions from viewBox
            if has_viewbox:
                viewbox = svg_tag.get('viewBox')
                viewbox_parts = re.findall(r'[\d.]+', viewbox)
                if len(viewbox_parts) >= 4:
                    width = float(viewbox_parts[2])
                    height = float(viewbox_parts[3])
                    svg_tag['width'] = f"{width}px"
                    svg_tag['height'] = f"{height}px"
                    return str(soup)
            
            # Try to find dimensions in style or from content bounds
            # Look for any numeric values that might be dimensions
            content = str(svg_tag)
            
            # Extract potential coordinates to estimate size
            x_coords = re.findall(r'\bx[12]?="?(\d+(?:\.\d+)?)', content)
            y_coords = re.findall(r'\by[12]?="?(\d+(?:\.\d+)?)', content)
            width_attrs = re.findall(r'\bwidth="?(\d+(?:\.\d+)?)', content)
            height_attrs = re.findall(r'\bheight="?(\d+(?:\.\d+)?)', content)
            
            # Estimate dimensions based on content
            estimated_width = 800  # Default fallback
            estimated_height = 600  # Default fallback
            
            if x_coords:
                max_x = max(float(x) for x in x_coords)
                estimated_width = max(estimated_width, max_x + 50)
            
            if y_coords:
                max_y = max(float(y) for y in y_coords)
                estimated_height = max(estimated_height, max_y + 50)
                
            if width_attrs:
                avg_width = sum(float(w) for w in width_attrs) / len(width_attrs)
                estimated_width = max(estimated_width, avg_width * 2)
                
            if height_attrs:
                avg_height = sum(float(h) for h in height_attrs) / len(height_attrs)
                estimated_height = max(estimated_height, avg_height * 2)
            
            # Set reasonable limits
            estimated_width = min(2000, max(400, estimated_width))
            estimated_height = min(1500, max(300, estimated_height))
            
            # Add dimensions and viewBox
            svg_tag['width'] = f"{estimated_width}px"
            svg_tag['height'] = f"{estimated_height}px"
            
            if not has_viewbox:
                svg_tag['viewBox'] = f"0 0 {estimated_width} {estimated_height}"
                
            return str(soup)
            
        except Exception as e:
            # If all fails, add basic dimensions
            svg_string = svg_string.replace('<svg ', '<svg width="800px" height="600px" viewBox="0 0 800 600" ', 1)
            return svg_string

    def svg_to_png_cairosvg(self, svg_string, output_path, width=2000):
        """Convert SVG to PNG using cairosvg with dimension fixing"""
        try:
            import cairosvg
            
            # Fix SVG namespace if missing
            if 'xmlns' not in svg_string:
                svg_string = svg_string.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ')
            
            # Try conversion first
            try:
                cairosvg.svg2png(
                    bytestring=svg_string.encode('utf-8'),
                    write_to=str(output_path),
                    output_width=width
                )
            except Exception as first_error:
                # If it fails due to size issues, fix dimensions and retry
                if "size is undefined" in str(first_error) or "viewBox" in str(first_error):
                    print(f"    🔧 Fixing SVG dimensions...")
                    fixed_svg = self.fix_svg_dimensions(svg_string)
                    
                    cairosvg.svg2png(
                        bytestring=fixed_svg.encode('utf-8'),
                        write_to=str(output_path),
                        output_width=width
                    )
                else:
                    raise first_error
            
            # Verify file was created
            if output_path.exists() and output_path.stat().st_size > 1000:
                return output_path
            else:
                raise Exception("PNG file not created or too small")
                
        except Exception as e:
            raise Exception(f"CairoSVG conversion error: {str(e)}")
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
    
    def extract_skus_and_titles_from_html(self, soup):
        """Extract all SKUs and their corresponding titles from HTML diagram using same logic as original scraper"""
        sku_title_combinations = []  # Changed to list to store all combinations
        
        # Use the same extraction logic as the original scraper
        parts_items = soup.find_all(lambda tag: tag.name == "div" and 
                                "parts-item" in tag.get("class", []) and 
                                tag.has_attr("data-callout"))
        
        # Filter out items with 'dn' class (same as original)
        filtered_items = [item for item in parts_items if 'dn' not in item.get('class', [])]
        
        for item in filtered_items:
            try:
                # Extract part number (SKU) - same logic as original
                part_number_elem = item.select_one('.part-number a.text-link')
                part_number = part_number_elem.text.strip() if part_number_elem else None
                
                # Extract description (title/usage_name) - same logic as original  
                description_elem = item.select_one('.column.describe')
                description = description_elem.text.strip() if description_elem else None
                
                # Only add if both part number and description are found
                if part_number and description and description != "N/A":
                    # Store as tuple to preserve all SKU+title combinations
                    combination = (part_number, description)
                    if combination not in sku_title_combinations:  # Avoid exact duplicates
                        sku_title_combinations.append(combination)
                    
            except Exception as e:
                # Skip problematic items
                continue
        
        return sku_title_combinations
    
    def process_html_file(self, html_path):
        """Extract SVG from HTML, create one PNG, then copy for each SKU"""
        results = []
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'lxml')
            
            # Extract all SKUs and their titles from this diagram
            sku_title_combinations = self.extract_skus_and_titles_from_html(soup)
            
            if not sku_title_combinations:
                self.stats['skipped'] += 1
                return [], "No SKU+title combinations found"
            
            # Convert to dictionary for mapping purposes (keep last occurrence for mapping)
            sku_title_map = {}
            for sku, title in sku_title_combinations:
                sku_title_map[sku] = title  # For mapping purposes, but we'll process all combinations
            
            # Find SVG element
            svg = soup.find('svg')
            if not svg:
                self.stats['skipped'] += 1
                return [], "No SVG found"
            
            # Create a master PNG filename for this diagram
            diagram_name = html_path.stem.replace(' ', '_').replace('&', 'and')
            master_filename = f"master_{diagram_name}.png"
            master_path = self.output_dir / master_filename
            
            # Generate master PNG only if it doesn't exist
            if not master_path.exists():
                try:
                    svg_string = str(svg)
                    self.svg_to_png_cairosvg(svg_string, master_path)
                    print(f"  🎨 Generated master: {master_filename}")
                except Exception as e:
                    error_msg = f"Error creating master PNG for {html_path.name}: {str(e)}"
                    self.stats['errors'].append(error_msg)
                    return [], str(e)
            
            # Create mapping entry for this diagram
            relative_html_path = str(html_path.relative_to(self.data_dir.parent))
            category = html_path.parent.name
            
            mapping_key = master_filename
            self.vector_mapping[mapping_key] = {
                'source_html': relative_html_path,
                'skus': [sku for sku, title in sku_title_combinations],  # All SKUs from combinations
                'sku_titles': dict(sku_title_combinations),  # Convert to dict for JSON serialization
                'diagram_name': html_path.stem,
                'category': category,
                'master_png': master_filename,
                'total_parts': len(sku_title_combinations)  # Count all combinations
            }
            
            # Now copy the master PNG for each SKU+title combination
            copied_count = 0
            skipped_count = 0
            
            for sku, title in sku_title_combinations:  # Process ALL combinations
                # Create filename using SKU + sanitized title
                safe_title = title.replace(' ', '_').replace('&', 'and').replace('/', '-').replace('\\', '-')
                safe_title = ''.join(c for c in safe_title if c.isalnum() or c in '_-')  # Remove special chars
                sku_filename = f"{sku}-{safe_title}.png"
                sku_path = self.output_dir / sku_filename
                
                # Check if this specific SKU+title PNG already exists
                if sku_path.exists():
                    results.append({
                        'output_path': sku_path,
                        'sku': sku,
                        'title': title,
                        'diagram_name': html_path.stem,
                        'action': 'already_exists'
                    })
                    skipped_count += 1
                    continue
                
                try:
                    # Copy master PNG to SKU+title-named file
                    import shutil
                    shutil.copy2(master_path, sku_path)
                    
                    results.append({
                        'output_path': sku_path,
                        'sku': sku,
                        'title': title,
                        'diagram_name': html_path.stem,
                        'action': 'copied',
                        'sku_filename': sku_filename
                    })
                    
                    self.stats['converted'] += 1
                    copied_count += 1
                    
                except Exception as e:
                    error_msg = f"Error copying PNG for {sku}-{safe_title}: {str(e)}"
                    self.stats['errors'].append(error_msg)
                    self.stats['failed_files'].append(sku_filename)
            
            if copied_count > 0 or skipped_count > 0:
                print(f"    📋 {copied_count} copied, {skipped_count} already existed")
            
            return results, f"Processed {len(sku_title_combinations)} SKU+title combinations ({copied_count} copied, {skipped_count} skipped)"
            
        except Exception as e:
            error_msg = f"Error processing {html_path.name}: {str(e)}"
            self.stats['errors'].append(error_msg)
            return [], str(e)
    
    def convert_batch(self, limit=None):
        """Convert SVG files in batch - creates SKU-named PNG files"""
        # Find all HTML files
        html_files = list(self.data_dir.rglob('*.html'))
        self.stats['total_files'] = len(html_files)
        
        if limit:
            html_files = html_files[:limit]
            print(f"\n🔧 Converting first {limit} diagrams only")
        
        print(f"\n{'='*60}")
        print(f"Converting {len(html_files)} diagrams to SKU-named PNG files")
        print(f"{'='*60}")
        print(f"Output directory: {self.output_dir}")
        print(f"Strategy: One PNG per SKU (SKUs across diagrams reuse existing files)")
        print(f"{'='*60}\n")
        
        all_results = []
        unique_skus = set()
        
        for html_file in tqdm(html_files, desc="Processing diagrams"):
            results, info = self.process_html_file(html_file)
            
            if results:
                all_results.extend(results)
                # Track unique SKUs
                for result in results:
                    unique_skus.add(result['sku'])
        
        print(f"\n📊 Summary:")
        print(f"   Total unique SKUs: {len(unique_skus)}")
        print(f"   Total PNG files: {self.stats['converted']}")
        
        # Save mapping file
        self.save_mapping_file()
        
        return all_results
    
    def print_summary(self):
        """Print conversion summary"""
        print(f"\n{'='*60}")
        print("Conversion Summary")
        print(f"{'='*60}")
        print(f"Total HTML files:        {self.stats['total_files']}")
        print(f"PNG files created:       {self.stats['converted']}")
        print(f"Skipped:                 {self.stats['skipped']}")
        print(f"Errors:                  {len(self.stats['errors'])}")
        print(f"{'='*60}\n")
        
        if self.stats['errors']:
            print("⚠ Errors:")
            for error in self.stats['errors'][:10]:
                print(f"  - {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more")
        
        # Write failed filenames to log file
        if self.stats['failed_files']:
            with open(self.error_log_path, 'w', encoding='utf-8') as f:
                f.write("# Failed Image Conversions (SKU-named)\n")
                f.write(f"# Total failed: {len(self.stats['failed_files'])}\n")
                f.write(f"# Generated: {Path(__file__).name}\n\n")
                for failed_file in self.stats['failed_files']:
                    f.write(f"{failed_file}\n")
            print(f"\n📝 Failed filenames written to: {self.error_log_path}")
            print(f"   Total failed: {len(self.stats['failed_files'])}")
        
        print(f"\n✅ PNG files are now named with SKUs for easy import matching!")
        print(f"   Example: C00041192.png, C00017370.png, etc.")
        print(f"   These can be directly matched during bulk import.")
        
        if hasattr(self, 'mapping_file') and self.mapping_file.exists():
            print(f"\n📋 SKU-to-Vector mapping saved: {self.mapping_file.name}")
            print(f"   Use this for troubleshooting failed image uploads.")
    
    def save_mapping_file(self):
        """Save SKU-to-vector mapping for troubleshooting"""
        try:
            import json
            with open(self.mapping_file, 'w', encoding='utf-8') as f:
                json.dump(self.vector_mapping, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Mapping saved: {self.mapping_file}")
            print(f"   📊 {len(self.vector_mapping)} diagrams mapped")
            
        except Exception as e:
            print(f"\n⚠️  Could not save mapping file: {e}")
    
    def load_existing_mapping(self):
        """Load existing mapping file if it exists"""
        try:
            if self.mapping_file.exists():
                import json
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    self.vector_mapping = json.load(f)
                print(f"📋 Loaded existing mapping: {len(self.vector_mapping)} entries")
        except Exception as e:
            print(f"⚠️  Could not load existing mapping: {e}")
            self.vector_mapping = {}


def main():
    """Main conversion function"""
    import argparse
    
    # Add GTK3 to PATH for Windows PNG conversion
    import os
    gtk3_path = r"C:\Program Files\GTK3-Runtime Win64\bin"
    if os.path.exists(gtk3_path):
        os.environ['PATH'] = gtk3_path + os.pathsep + os.environ.get('PATH', '')
        print(f"✓ Added GTK3 to PATH: {gtk3_path}")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Convert SVG diagrams to SKU-named PNG files')
    parser.add_argument('--serial', type=str, help='Process specific serial number (e.g., LSFAL11A4PA157987)')
    parser.add_argument('--limit', type=int, help='Limit number of HTML files to process')
    
    args = parser.parse_args()
    
    # Determine data directory
    if args.serial:
        data_dir = base_dir / args.serial
        if not data_dir.exists():
            print(f"❌ Serial directory not found: {data_dir}")
            print(f"Available directories:")
            for item in base_dir.iterdir():
                if item.is_dir() and item.name.startswith('LSF'):
                    print(f"  - {item.name}")
            return
    else:
        data_dir = base_dir / 'LSFAL11A4PA157987'  # Default
    
    # Output directory
    output_dir = base_dir / 'images' / 'converted'
    
    print("\n" + "="*60)
    print("SVG to SKU-named PNG Conversion")
    print("="*60)
    print(f"Serial: {data_dir.name}")
    print(f"Output: {output_dir}")
    print("="*60)
    
    # Create converter
    converter = SVGConverter(data_dir, output_dir)
    
    # Load existing mapping if available
    converter.load_existing_mapping()
    
    # Convert diagrams
    results = converter.convert_batch(limit=args.limit)
    
    # Print summary
    converter.print_summary()
    
    if results:
        print(f"\n✓ Sample SKU files created:")
        for result in results[:5]:
            print(f"  - {result['sku']}.png (from {result['diagram_name']})")
        if len(results) > 5:
            print(f"  ... and {len(results) - 5} more")

if __name__ == "__main__":
    main()
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
