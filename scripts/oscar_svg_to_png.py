#!/usr/bin/env python3
"""
Convert SVG diagrams from Oscar database directly to PNG files
This creates the PNG files needed for WordPress import

Usage:
    python scripts/oscar_svg_to_png.py

Output:
    - PNG files in images/converted/
    - Lookup file: data/svg_to_png_mapping.json
"""
import sys
import json
import hashlib
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
from tqdm import tqdm
import cairosvg
from PIL import Image
import io

# Add parent directory to path
base_dir = Path(__file__).parent.parent
sys.path.insert(0, str(base_dir))

# Database connection
DB_CONFIG = {
    'dbname': 'parts_store',
    'user': 'postgres',
    'password': 'N0rwich!',
    'host': '80.95.207.42',
    'port': '5432'
}

class OscarSVGConverter:
    def __init__(self):
        self.output_dir = base_dir / 'images' / 'converted'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.mapping_file = base_dir / 'data' / 'svg_to_png_mapping.json'
        self.mapping_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            'unique_svgs': 0,
            'converted': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
    def get_unique_svgs_from_oscar(self):
        """Extract unique SVG diagrams from Oscar database"""
        print("🔍 Extracting unique SVGs from Oscar database...")
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get unique SVGs with metadata - simplified working query
            query = """
            SELECT DISTINCT 
                ct.svg_code,
                ct.title as diagram_name,
                pt.title as main_category,
                sn.serial,
                sn.vehicle_brand as brand,
                MIN(p.id) as sample_part_id,
                COUNT(*) as part_count
            FROM motorpartsdata_childtitle ct
            JOIN motorpartsdata_part p ON p.child_title_id = ct.id
            JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id
            JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
            WHERE ct.svg_code IS NOT NULL 
            AND ct.svg_code != ''
            AND LENGTH(ct.svg_code) > 1000
            GROUP BY ct.svg_code, ct.title, pt.title, sn.serial, sn.vehicle_brand
            ORDER BY sn.serial, pt.title, ct.title;
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            unique_svgs = []
            for row in results:
                # Create unique identifier for this SVG
                svg_hash = hashlib.md5(row['svg_code'].encode()).hexdigest()[:8]
                
                # Build filename: Serial_MainCategory_DiagramName_Hash.png
                filename_parts = [
                    row['serial'],
                    self.sanitize_filename(row['main_category']),
                    self.sanitize_filename(row['diagram_name']),
                    svg_hash
                ]
                filename = '_'.join(filename_parts) + '.png'
                
                unique_svgs.append({
                    'svg_code': row['svg_code'],
                    'filename': filename,
                    'serial': row['serial'],
                    'brand': row['brand'],
                    'main_category': row['main_category'],
                    'diagram_name': row['diagram_name'],
                    'svg_hash': svg_hash,
                    'part_count': row['part_count'],
                    'sample_part_id': row['sample_part_id']
                })
            
            cursor.close()
            conn.close()
            
            self.stats['unique_svgs'] = len(unique_svgs)
            print(f"✅ Found {len(unique_svgs)} unique SVG diagrams")
            return unique_svgs
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            return []
    
    def sanitize_filename(self, name):
        """Convert category name to safe filename"""
        if not name:
            return 'Unknown'
        # Replace problematic characters
        safe_name = name.replace(' ', '_').replace('&', 'and').replace(',', '').replace('/', '_')
        # Remove special characters but keep alphanumeric, underscore, hyphen
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c in ['_', '-'])
        return safe_name[:50]  # Limit length
    
    def fix_svg_for_conversion(self, svg_code):
        """Fix common SVG issues before conversion"""
        try:
            # Add namespace if missing
            if 'xmlns' not in svg_code:
                svg_code = svg_code.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ')
            
            # Ensure it starts with <?xml or <svg
            svg_code = svg_code.strip()
            if not (svg_code.startswith('<?xml') or svg_code.startswith('<svg')):
                # Find the actual SVG tag start
                svg_start = svg_code.find('<svg')
                if svg_start > 0:
                    svg_code = svg_code[svg_start:]
            
            return svg_code
            
        except Exception as e:
            return svg_code
    
    def convert_svg_to_png(self, svg_code, output_path, width=2000):
        """Convert SVG code to PNG file"""
        try:
            # Fix SVG formatting
            fixed_svg = self.fix_svg_for_conversion(svg_code)
            
            # Convert with cairosvg (best quality)
            cairosvg.svg2png(
                bytestring=fixed_svg.encode('utf-8'),
                write_to=str(output_path),
                output_width=width
            )
            
            # Verify file was created and has reasonable size
            if output_path.exists() and output_path.stat().st_size > 1000:
                return True
            else:
                return False
                
        except Exception as e:
            # Try PIL fallback (less reliable but might work)
            try:
                from PIL import Image
                import cairosvg
                
                # Convert to bytes first
                png_bytes = cairosvg.svg2png(
                    bytestring=fixed_svg.encode('utf-8'),
                    output_width=width
                )
                
                # Save with PIL
                image = Image.open(io.BytesIO(png_bytes))
                image.save(output_path, 'PNG', optimize=True)
                
                return output_path.exists() and output_path.stat().st_size > 1000
                
            except Exception as e2:
                self.stats['errors'].append(f"Conversion failed: {e} | {e2}")
                return False
    
    def create_part_lookup_table(self, unique_svgs):
        """Create lookup table: part_id -> PNG filename"""
        print("🔗 Creating part-to-PNG lookup table...")
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            lookup_table = {}
            
            # For each unique SVG, find all parts that use it
            for svg_data in tqdm(unique_svgs, desc="Building lookup"):
                # Find all parts with this exact SVG (via child_title_id)
                query = """
                SELECT p.id as part_id, p.part_number as sku, p.usage_name as name
                FROM motorpartsdata_part p
                JOIN motorpartsdata_childtitle ct ON p.child_title_id = ct.id
                WHERE ct.svg_code = %s
                """
                cursor.execute(query, (svg_data['svg_code'],))
                parts = cursor.fetchall()
                
                # Map each part to the PNG filename
                for part in parts:
                    lookup_table[part['part_id']] = {
                        'png_filename': svg_data['filename'],
                        'sku': part['sku'],
                        'part_name': part['name'],
                        'diagram_category': f"{svg_data['main_category']} - {svg_data['diagram_name']}",
                        'serial_number': svg_data['serial']
                    }
            
            cursor.close()
            conn.close()
            
            # Save lookup table
            with open(self.mapping_file, 'w') as f:
                json.dump(lookup_table, f, indent=2)
            
            print(f"✅ Created lookup table for {len(lookup_table)} parts")
            return lookup_table
            
        except Exception as e:
            print(f"❌ Lookup table creation failed: {e}")
            return {}
    
    def convert_all_svgs(self):
        """Main conversion process"""
        print("\\n" + "="*70)
        print("🎨 OSCAR SVG TO PNG CONVERTER")
        print("="*70)
        
        # Get unique SVGs
        unique_svgs = self.get_unique_svgs_from_oscar()
        if not unique_svgs:
            print("❌ No SVGs found to convert")
            return
        
        print(f"\\n📊 Processing {len(unique_svgs)} unique diagrams...")
        
        # Convert each unique SVG
        for svg_data in tqdm(unique_svgs, desc="Converting SVGs"):
            output_path = self.output_dir / svg_data['filename']
            
            # Skip if already exists (unless forced)
            if output_path.exists():
                self.stats['skipped'] += 1
                continue
            
            # Convert SVG to PNG
            if self.convert_svg_to_png(svg_data['svg_code'], output_path):
                self.stats['converted'] += 1
                # Add file size info to svg_data for lookup table
                svg_data['file_size'] = output_path.stat().st_size
            else:
                self.stats['failed'] += 1
                self.stats['errors'].append(f"Failed: {svg_data['filename']}")
        
        # Create part lookup table
        lookup_table = self.create_part_lookup_table(unique_svgs)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print conversion summary"""
        print("\\n" + "="*70)
        print("📊 CONVERSION SUMMARY")
        print("="*70)
        print(f"Unique SVGs found:    {self.stats['unique_svgs']}")
        print(f"Successfully converted: {self.stats['converted']}")
        print(f"Already existed:       {self.stats['skipped']}")
        print(f"Failed conversions:    {self.stats['failed']}")
        print(f"Total errors:          {len(self.stats['errors'])}")
        print("="*70)
        
        if self.stats['errors']:
            print("\\n❌ First 5 errors:")
            for error in self.stats['errors'][:5]:
                print(f"   • {error}")
        
        if self.stats['converted'] > 0:
            print("\\n✅ PNG files ready for WordPress import!")
            print(f"   📁 Location: {self.output_dir}")
            print(f"   🗺️  Lookup file: {self.mapping_file}")
        
        print("\\n📝 Next steps:")
        print("   1. Run enhanced bulk_import_optimizer.py")
        print("   2. Products will automatically use PNG images")
        print("   3. No separate image assignment needed!")

def main():
    """Main function"""
    converter = OscarSVGConverter()
    converter.convert_all_svgs()

if __name__ == "__main__":
    main()