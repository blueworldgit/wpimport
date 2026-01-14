#!/usr/bin/env python3
"""
Test the fixed PNG conversion on just Instrument Panel files
"""
import sys
from pathlib import Path

# Add parent directory to path
base_dir = Path(__file__).parent.parent if Path(__file__).parent.parent else Path(__file__).parent
sys.path.insert(0, str(base_dir))

# Import the fixed converter
from scripts.convert_svg_to_png import SVGConverter

def test_instrument_panel_conversion():
    """Test conversion of just instrument panel files"""
    
    # Setup paths
    data_dir = Path('LSFAL11A4PA157987')  # Relative path from current directory
    output_dir = Path('images') / 'converted'
    
    print("🧪 Testing Fixed PNG Conversion")
    print("=" * 50)
    print(f"Data: {data_dir}")
    print(f"Output: {output_dir}")
    
    # Create converter
    converter = SVGConverter(data_dir, output_dir)
    
    # Process just the Instrument Panel HTML file
    instrument_panel_file = data_dir / 'instrument panel & console' / 'Instrument Panel(LHD).html'
    
    if not instrument_panel_file.exists():
        print(f"❌ File not found: {instrument_panel_file}")
        return
    
    print(f"\n🎯 Processing: {instrument_panel_file.name}")
    
    # Before - check existing B00004653 files
    existing_files = list(output_dir.glob("B00004653-*.png"))
    print(f"\n📋 Before: {len(existing_files)} existing B00004653 PNG files")
    for file in existing_files:
        print(f"   ✓ {file.name}")
    
    # Process the file
    results, info = converter.process_html_file(instrument_panel_file)
    
    print(f"\n📊 Conversion Results:")
    print(f"   Status: {info}")
    print(f"   Files processed: {len(results)}")
    
    # Show B00004653 specific results
    b00004653_results = [r for r in results if r['sku'] == 'B00004653']
    print(f"\n🔍 B00004653 Results ({len(b00004653_results)} files):")
    for result in b00004653_results:
        action_icon = "🆕" if result['action'] == 'copied' else "✅"
        print(f"   {action_icon} {result['sku']}-{result['title'][:40]}...")
    
    # After - check total B00004653 files
    updated_files = list(output_dir.glob("B00004653-*.png"))
    print(f"\n📋 After: {len(updated_files)} total B00004653 PNG files")
    new_files = [f for f in updated_files if f not in existing_files]
    if new_files:
        print(f"   🆕 {len(new_files)} new files created:")
        for file in new_files[:5]:  # Show first 5
            print(f"      - {file.name}")
        if len(new_files) > 5:
            print(f"      ... and {len(new_files) - 5} more")

if __name__ == "__main__":
    test_instrument_panel_conversion()