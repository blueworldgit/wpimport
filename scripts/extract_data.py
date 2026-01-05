"""
Data Extraction Script - Phase 2
Extracts parts data from HTML files and prepares for WooCommerce import
"""
import os
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime
from tqdm import tqdm
from collections import defaultdict

class EPCDataExtractor:
    def __init__(self, data_dir, output_dir, log_dir):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.log_dir = Path(log_dir)
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'total_parts': 0,
            'unique_skus': 0,
            'variable_products': 0,
            'simple_products': 0,
            'excluded_dn': 0,
            'errors': []
        }
    
    def extract_parts_from_html(self, html_path):
        """
        Extract all parts from a single HTML file
        Excludes parts with class='dn' (hidden/inactive)
        """
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'lxml')
            
            # Extract diagram code from legend-title (e.g., "JE140A001 - Air filter")
            diagram_code = ''
            legend_title = soup.find('span', id='legend-title')
            if legend_title:
                title_text = legend_title.text.strip()
                # Extract code before the dash (e.g., "JE140A001")
                if ' - ' in title_text:
                    diagram_code = title_text.split(' - ')[0].strip()
                else:
                    diagram_code = title_text.strip()
            
            parts = []
            
            # Find all parts-item divs (both tables have same structure)
            parts_items = soup.find_all('div', class_='parts-item')
            
            for item in parts_items:
                # CRITICAL: Exclude parts with class="dn" (hidden/inactive)
                if 'dn' in item.get('class', []):
                    self.stats['excluded_dn'] += 1
                    continue
                
                # Extract data attributes
                sku = item.get('data-part-id', '').strip()
                callout = item.get('data-callout', '').strip()
                data_id = item.get('data-id', '').strip()
                
                if not sku:
                    continue  # Skip if no SKU
                
                # Extract columns
                columns = item.find_all('span', class_='column')
                
                # L/R field (first column in float table)
                lr = ''
                for col in columns:
                    if col.get('style', '').startswith('width:70px'):
                        lr = col.text.strip()
                        break
                
                # Remark field (second column in float table with text-column-note)
                remark = ''
                remark_cols = item.find_all('span', class_='text-column-note')
                if remark_cols:
                    for rcol in remark_cols:
                        span_text = rcol.find('span')
                        if span_text and span_text.get('title'):
                            remark = span_text.get('title').strip()
                            break
                
                # Part name (describe column)
                name_elem = item.find('span', class_='describe')
                name = name_elem.text.strip() if name_elem else ''
                
                # Quantity
                qty_elem = item.find('span', class_='quantity')
                quantity = qty_elem.text.strip() if qty_elem else '1.0'
                
                if name:  # Only add if we have a name
                    parts.append({
                        'sku': sku,
                        'name': name,
                        'lr': lr,
                        'callout': callout,
                        'quantity': quantity,
                        'remark': remark,
                        'data_id': data_id,
                        'diagram_code': diagram_code
                    })
                    self.stats['total_parts'] += 1
            
            return parts
            
        except Exception as e:
            error_msg = f"Error parsing {html_path}: {str(e)}"
            self.stats['errors'].append(error_msg)
            return []
    
    def detect_orientation(self, part):
        """
        Detect part orientation from L/R field and remarks
        Returns: 'Left', 'Right', 'Front', 'Rear', or None
        """
        lr_field = part.get('lr', '').strip()
        
        # Primary source: L/R column
        if lr_field:
            if re.search(r'\b(left|lh|l\.h\.)\b', lr_field, re.IGNORECASE):
                return 'Left'
            elif re.search(r'\b(right|rh|r\.h\.)\b', lr_field, re.IGNORECASE):
                return 'Right'
            elif re.search(r'\b(front|fr)\b', lr_field, re.IGNORECASE):
                return 'Front'
            elif re.search(r'\b(rear|rr)\b', lr_field, re.IGNORECASE):
                return 'Rear'
        
        # Fallback: Check remarks
        text = f"{part.get('remark', '')}".lower()
        if re.search(r'\b(left|lh|l\.h\.)\b', text):
            return 'Left'
        elif re.search(r'\b(right|rh|r\.h\.)\b', text):
            return 'Right'
        elif re.search(r'\b(front|fr)\b', text):
            return 'Front'
        elif re.search(r'\b(rear|rr)\b', text):
            return 'Rear'
        
        return None
    
    def detect_variations(self, parts):
        """
        Group parts by (name + callout) to detect variations
        Returns: dict of variation groups and list of simple products
        """
        # Group by (name, callout)
        groups = defaultdict(list)
        
        for part in parts:
            # Add orientation info to part
            part['orientation'] = self.detect_orientation(part)
            key = (part['name'], part['callout'])
            groups[key].append(part)
        
        # Identify variation groups and simple products
        variation_groups = {}
        simple_products = []
        
        for key, group_parts in groups.items():
            name, callout = key
            
            # Check if this is a variation group (multiple parts with different orientations)
            orientations = [p['orientation'] for p in group_parts if p['orientation']]
            
            if len(group_parts) > 1 and len(orientations) > 1:
                # This is a variable product
                variation_groups[key] = {
                    'base_name': name,
                    'callout': callout,
                    'variations': group_parts
                }
                self.stats['variable_products'] += 1
            else:
                # These are simple products
                simple_products.extend(group_parts)
                self.stats['simple_products'] += len(group_parts)
        
        return variation_groups, simple_products
    
    def extract_category_data(self, serial_dir, test_limit=None):
        """
        Extract data from all HTML files in a serial directory
        
        Args:
            serial_dir: Path to serial directory (e.g., LSFAL11A4PA157987)
            test_limit: Optional limit for number of products (for testing)
        """
        serial_path = Path(serial_dir)
        serial_number = serial_path.name
        
        print(f"\n{'='*60}")
        print(f"Extracting data from: {serial_number}")
        print(f"{'='*60}\n")
        
        # Find all HTML files
        html_files = list(serial_path.rglob('*.html'))
        self.stats['total_files'] = len(html_files)
        
        print(f"Found {len(html_files)} HTML files")
        
        all_products = []
        categories_structure = {}
        product_count = 0
        
        # Process each HTML file
        for html_file in tqdm(html_files, desc="Processing files"):
            # Get category hierarchy from path
            relative_path = html_file.relative_to(serial_path)
            parent_category = relative_path.parent.name  # e.g., "front lamp"
            diagram_name = html_file.stem  # e.g., "Front Lamp"
            
            # Extract parts
            parts = self.extract_parts_from_html(html_file)
            
            if not parts:
                continue
            
            # Detect variations
            variation_groups, simple_products = self.detect_variations(parts)
            
            # Build category structure
            if parent_category not in categories_structure:
                categories_structure[parent_category] = []
            categories_structure[parent_category].append(diagram_name)
            
            # Add variable products
            for key, var_group in variation_groups.items():
                # Get diagram_code from first variation
                diagram_code = var_group['variations'][0].get('diagram_code', '') if var_group['variations'] else ''
                
                product = {
                    'type': 'variable',
                    'name': var_group['base_name'],
                    'parent_sku': None,  # Parent has no SKU (WooCommerce best practice)
                    'variations': [],
                    'categories': ['Maxus', serial_number, parent_category, diagram_name],
                    'callout': var_group['callout'],
                    'diagram_file': str(html_file.relative_to(self.data_dir)),
                    'diagram_code': diagram_code
                }
                
                for variation in var_group['variations']:
                    product['variations'].append({
                        'sku': variation['sku'],
                        'orientation': variation['orientation'],
                        'quantity': variation['quantity'],
                        'remark': variation['remark'],
                        'lr_field': variation['lr']
                    })
                
                all_products.append(product)
                product_count += 1
                
                if test_limit and product_count >= test_limit:
                    break
            
            # Add simple products
            for part in simple_products:
                product = {
                    'type': 'simple',
                    'name': part['name'],
                    'sku': part['sku'],
                    'orientation': part['orientation'],
                    'categories': ['Maxus', serial_number, parent_category, diagram_name],
                    'callout': part['callout'],
                    'quantity': part['quantity'],
                    'remark': part['remark'],
                    'lr_field': part['lr'],
                    'diagram_file': str(html_file.relative_to(self.data_dir)),
                    'diagram_code': part.get('diagram_code', '')
                }
                
                all_products.append(product)
                product_count += 1
                
                if test_limit and product_count >= test_limit:
                    break
            
            self.stats['processed_files'] += 1
            
            if test_limit and product_count >= test_limit:
                print(f"\n⚠ Test limit reached: {test_limit} products")
                break
        
        # Count unique SKUs
        all_skus = set()
        for product in all_products:
            if product['type'] == 'variable':
                all_skus.update(v['sku'] for v in product['variations'])
            else:
                all_skus.add(product['sku'])
        
        self.stats['unique_skus'] = len(all_skus)
        
        # Build output data structure
        output_data = {
            'serial_number': serial_number,
            'vehicle_brand': 'Maxus',
            'extraction_date': datetime.now().isoformat(),
            'categories_structure': categories_structure,
            'products': all_products,
            'stats': self.stats
        }
        
        return output_data
    
    def save_extracted_data(self, data, filename='extracted_data.json'):
        """Save extracted data to JSON file"""
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Data saved to: {output_path}")
        return output_path
    
    def print_summary(self):
        """Print extraction summary"""
        print(f"\n{'='*60}")
        print("Extraction Summary")
        print(f"{'='*60}")
        print(f"Total HTML files:        {self.stats['total_files']}")
        print(f"Processed files:         {self.stats['processed_files']}")
        print(f"Total parts found:       {self.stats['total_parts']}")
        print(f"Excluded (class='dn'):   {self.stats['excluded_dn']}")
        print(f"Unique SKUs:             {self.stats['unique_skus']}")
        print(f"Variable products:       {self.stats['variable_products']}")
        print(f"Simple products:         {self.stats['simple_products']}")
        print(f"Errors:                  {len(self.stats['errors'])}")
        print(f"{'='*60}\n")
        
        if self.stats['errors']:
            print("\n⚠ Errors encountered:")
            for error in self.stats['errors'][:10]:  # Show first 10
                print(f"  - {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more")


def main():
    """Main extraction function"""
    # Paths
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / 'LSFAL11A4PA157987'
    output_dir = base_dir / 'data' / 'extracted'
    log_dir = base_dir / 'logs'
    
    # Create extractor
    extractor = EPCDataExtractor(data_dir, output_dir, log_dir)
    
    # Extract data (TEST MODE: limit to 20 products)
    print("\n🔧 TEST MODE: Extracting first 20 products only")
    data = extractor.extract_category_data(data_dir, test_limit=20)
    
    # Save data
    extractor.save_extracted_data(data, filename='extracted_data_test.json')
    
    # Print summary
    extractor.print_summary()
    
    print("✓ Extraction complete! Ready for WooCommerce import.")
    print(f"✓ Next step: Run the import script with extracted_data_test.json")


if __name__ == "__main__":
    main()
