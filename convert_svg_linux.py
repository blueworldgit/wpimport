#!/usr/bin/env python3
"""
SVG to PNG Conversion Script for Linux/Ubuntu
Fast and clean conversion using cairosvg
"""
import os
import sys
from pathlib import Path
from tqdm import tqdm

def convert_svg_to_png(svg_path, output_path, width=2000):
    """Convert SVG to PNG using cairosvg"""
    import cairosvg
    
    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(output_path),
        output_width=width
    )
    return output_path

def main():
    # Get script directory
    script_dir = Path(__file__).parent
    svg_dir = script_dir / 'svg_files'
    output_dir = script_dir / 'png_output'
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Find all SVG files
    svg_files = list(svg_dir.glob('*.svg'))
    
    if not svg_files:
        print(f"No SVG files found in: {svg_dir}")
        print("Please copy SVG files to ./svg_files/ directory")
        return
    
    print(f"\n{'='*60}")
    print(f"Converting {len(svg_files)} SVG files to PNG")
    print(f"{'='*60}\n")
    print(f"Input:  {svg_dir}")
    print(f"Output: {output_dir}")
    print(f"Width:  2000px\n")
    
    converted = 0
    errors = []
    
    for svg_file in tqdm(svg_files, desc="Converting"):
        try:
            output_file = output_dir / f"{svg_file.stem}.png"
            convert_svg_to_png(svg_file, output_file, width=2000)
            converted += 1
        except Exception as e:
            errors.append(f"{svg_file.name}: {str(e)}")
    
    print(f"\n{'='*60}")
    print("Conversion Summary")
    print(f"{'='*60}")
    print(f"Total:     {len(svg_files)}")
    print(f"Converted: {converted}")
    print(f"Errors:    {len(errors)}")
    print(f"{'='*60}\n")
    
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ All files converted successfully!")
        print(f"\n✓ PNG files saved to: {output_dir}")

if __name__ == "__main__":
    # Check if cairosvg is installed
    try:
        import cairosvg
    except ImportError:
        print("\n✗ cairosvg not installed!")
        print("\nInstall with:")
        print("  sudo apt-get install libcairo2-dev pkg-config")
        print("  pip3 install cairosvg")
        sys.exit(1)
    
    main()
