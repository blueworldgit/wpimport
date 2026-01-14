#!/usr/bin/env python3
"""
Test script to debug the Instrument Panel(LHD).html conversion
"""
from pathlib import Path
from bs4 import BeautifulSoup

def extract_skus_from_html(html_path):
    """Extract all SKUs and their titles from the HTML file"""
    print(f"\nAnalyzing: {html_path.name}")
    print("-" * 50)
    
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'lxml')
    
    # Use the same extraction logic as the convert script
    parts_items = soup.find_all(lambda tag: tag.name == "div" and 
                            "parts-item" in tag.get("class", []) and 
                            tag.has_attr("data-callout"))
    
    # Filter out items with 'dn' class (same as original)
    filtered_items = [item for item in parts_items if 'dn' not in item.get('class', [])]
    
    print(f"Found {len(parts_items)} total parts-item divs")
    print(f"After filtering 'dn' class: {len(filtered_items)} items")
    
    sku_title_combinations = []  # NEW: Use list to store all combinations
    skipped_items = []
    
    for i, item in enumerate(filtered_items):
        try:
            # Extract part number (SKU) - same logic as original
            part_number_elem = item.select_one('.part-number a.text-link')
            part_number = part_number_elem.text.strip() if part_number_elem else None
            
            # Extract description (title/usage_name) - same logic as original  
            description_elem = item.select_one('.column.describe')
            description = description_elem.text.strip() if description_elem else None
            
            # Only add if both part number and description are found
            if part_number and description and description != "N/A":
                combination = (part_number, description)
                if combination not in sku_title_combinations:  # Avoid exact duplicates
                    sku_title_combinations.append(combination)
                
                # Check if this is the specific SKU we're looking for
                if part_number == "B00004653":
                    print(f"✓ Found B00004653: '{description}'")
                    
            else:
                skipped_items.append({
                    'index': i,
                    'part_number': part_number,
                    'description': description,
                    'reason': 'Missing part_number or description or description is N/A'
                })
                
        except Exception as e:
            skipped_items.append({
                'index': i,
                'error': str(e),
                'reason': 'Exception during processing'
            })
    
    print(f"\n📊 Results:")
    print(f"   Valid SKU+title combinations: {len(sku_title_combinations)}")
    print(f"   Skipped items: {len(skipped_items)}")
    
    # Show all B00004653 combinations found
    b00004653_combinations = [(sku, title) for sku, title in sku_title_combinations if sku == "B00004653"]
    print(f"\n🔍 All B00004653 combinations found ({len(b00004653_combinations)}):")
    for sku, title in b00004653_combinations:
        print(f"   {sku}: {title}")
    
    # Check if our target combination exists
    target_title = "SCREW-INSTRUMENT PANEL SHINING STRIP ASSEMBLY"
    target_combination = ("B00004653", target_title)
    if target_combination in sku_title_combinations:
        print(f"\n✅ TARGET FOUND: B00004653 + '{target_title}'")
    else:
        print(f"\n❌ TARGET NOT FOUND: B00004653 + '{target_title}'")
    
    if skipped_items:
        print(f"\n⚠️  First 5 skipped items:")
        for item in skipped_items[:5]:
            print(f"   {item}")
    
    return sku_title_combinations

if __name__ == "__main__":
    # Test the specific HTML file
    html_file = Path("LSFAL11A4PA157987/instrument panel & console/Instrument Panel(LHD).html")
    
    if html_file.exists():
        sku_combinations = extract_skus_from_html(html_file)
        print(f"\n🎯 Summary: Found {len(sku_combinations)} unique SKU+title combinations")
    else:
        print(f"❌ File not found: {html_file}")