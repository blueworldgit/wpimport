#!/usr/bin/env python3
"""
Quick SVG to PNG test - Convert just a few SVGs to verify the concept works
"""
import sys
import hashlib
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
import cairosvg

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

def test_svg_conversion():
    """Test converting a few SVGs"""
    print("🧪 Testing SVG to PNG conversion...")
    
    # Create output directory
    output_dir = base_dir / 'images' / 'converted'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get just 3 SVGs for testing
        query = """
        SELECT 
            ct.id,
            ct.title,
            ct.svg_code,
            LENGTH(ct.svg_code) as svg_length
        FROM motorpartsdata_childtitle ct
        WHERE ct.svg_code IS NOT NULL 
        AND ct.svg_code != ''
        AND LENGTH(ct.svg_code) > 1000
        LIMIT 3
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        print(f"Found {len(results)} SVGs to test")
        
        for i, row in enumerate(results, 1):
            print(f"\\n{i}. {row['title']} ({row['svg_length']} chars)")
            
            # Generate filename
            title_safe = row['title'].replace(' ', '_').replace('-', '_').replace('&', 'and')
            filename = f"test_{i}_{title_safe}.png"
            output_path = output_dir / filename
            
            try:
                # Fix SVG for conversion
                svg_code = row['svg_code'].strip()
                if 'xmlns' not in svg_code:
                    svg_code = svg_code.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ')
                
                # Convert SVG to PNG
                cairosvg.svg2png(
                    bytestring=svg_code.encode('utf-8'),
                    write_to=str(output_path),
                    output_width=2000
                )
                
                # Check if file was created
                if output_path.exists() and output_path.stat().st_size > 1000:
                    file_size = output_path.stat().st_size / 1024  # KB
                    print(f"   ✅ SUCCESS: {filename} ({file_size:.1f} KB)")
                else:
                    print(f"   ❌ FAILED: File not created or too small")
                
            except Exception as e:
                print(f"   ❌ CONVERSION ERROR: {e}")
        
        cursor.close()
        conn.close()
        
        print("\\n🎯 Test completed!")
        print(f"Check files in: {output_dir}")
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    test_svg_conversion()