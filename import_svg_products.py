"""
Import Failed Diagrams as SVG Products
Process the conversion_errors.txt file and import each as SVG with WooCommerce product
"""
import sys
from pathlib import Path
from bs4 import BeautifulSoup
import requests
import time
import json
from tqdm import tqdm

# Add parent directory to path
base_dir = Path(__file__).parent
sys.path.insert(0, str(base_dir))

# WordPress credentials
WP_URL = "https://maxusvanparts.co.uk"
WP_USERNAME = "developer"
WP_APP_PASSWORD = "nIbM 6KlW sft3 hQyj OG4P ZYeI"
WC_CONSUMER_KEY = "ck_1be77215f05ca7f848ac0ec16a6b68e76ced9302"
WC_CONSUMER_SECRET = "cs_b2c2be6911c85fe9abc62b4ec5170b9ab746392e"

from woocommerce import API

# Initialize WooCommerce API
wcapi = API(
    url=WP_URL,
    consumer_key=WC_CONSUMER_KEY,
    consumer_secret=WC_CONSUMER_SECRET,
    version="wc/v3",
    timeout=60
)

def find_html_file_for_diagram(diagram_filename, data_dir):
    """
    Find the HTML file that corresponds to a diagram filename
    diagram_filename: e.g., "LSFAL11A4PA157987_Body_Interior_&_Exterior_Electronics.png"
    data_dir: The directory containing the HTML files (e.g., LSFAL11A4PA157987/)
    Returns: Path to HTML file or None
    """
    # Remove serial number and extension to get diagram name
    # Expected format: SERIALNUMBER_DiagramName.png
    parts = diagram_filename.replace('.png', '').replace('.svg', '').split('_', 1)
    
    if len(parts) < 2:
        return None
    
    serial_number = parts[0]
    diagram_name = parts[1]
    
    # data_dir is already the serial directory, so use it directly
    serial_dir = data_dir
    if not serial_dir.exists():
        return None
    
    # Normalize the diagram name for comparison
    def normalize_name(name):
        """Normalize name for comparison - handle underscores, spaces, and special chars"""
        return name.lower().replace('_', ' ').replace('&', 'and').replace(',', '').strip()
    
    normalized_target = normalize_name(diagram_name)
    
    # Search all subdirectories for matching HTML file
    for html_file in serial_dir.rglob('*.html'):
        # Check filename match
        html_name = normalize_name(html_file.stem)
        
        # Try exact match first
        if html_name == normalized_target:
            return html_file
        
        # Try with original & character
        if normalize_name(diagram_name.replace('&', ' and ')) == html_name:
            return html_file
    
    # If still not found, try a fuzzy match - check if most words match
    target_words = set(normalized_target.split())
    best_match = None
    best_score = 0
    
    for html_file in serial_dir.rglob('*.html'):
        html_name = normalize_name(html_file.stem)
        html_words = set(html_name.split())
        
        # Calculate word match score
        if target_words and html_words:
            common_words = target_words & html_words
            score = len(common_words) / max(len(target_words), len(html_words))
            
            # Require at least 70% word match
            if score > best_score and score >= 0.7:
                best_score = score
                best_match = html_file
    
    return best_match

def extract_svg_from_html(html_path):
    """Extract SVG from HTML file and return SVG string"""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'lxml')
        
        # Find SVG element
        svg = soup.find('svg')
        if not svg:
            return None
        
        # Get SVG string and ensure proper namespace
        svg_string = str(svg)
        if 'xmlns' not in svg_string:
            svg_string = svg_string.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ')
        
        return svg_string
        
    except Exception as e:
        print(f"    Error extracting SVG: {str(e)}")
        return None

def upload_svg_to_wordpress(svg_content, filename):
    """
    Upload SVG content to WordPress media library
    Returns: media ID or None
    """
    try:
        headers = {
            'Content-Disposition': f'attachment; filename={filename}',
            'Content-Type': 'image/svg+xml'
        }
        
        response = requests.post(
            f"{WP_URL}/wp-json/wp/v2/media",
            data=svg_content.encode('utf-8'),
            headers=headers,
            auth=(WP_USERNAME, WP_APP_PASSWORD),
            timeout=60
        )
        
        if response.status_code == 201:
            media_data = response.json()
            return media_data['id']
        else:
            print(f"    Upload failed: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"    Upload error: {str(e)}")
        return None

def get_or_create_category(category_name, parent_id=0, cache={}):
    """Get existing category ID or create new one"""
    cache_key = f"{category_name}_{parent_id}"
    if cache_key in cache:
        return cache[cache_key]
    
    try:
        # Search for existing category
        response = wcapi.get("products/categories", params={
            "search": category_name,
            "parent": parent_id,
            "per_page": 100
        })
        
        if response.status_code == 200:
            categories = response.json()
            for cat in categories:
                if cat['name'].lower() == category_name.lower() and cat['parent'] == parent_id:
                    cache[cache_key] = cat['id']
                    return cat['id']
        
        # Create new category
        category_data = {
            "name": category_name,
            "parent": parent_id,
            "slug": category_name.lower().replace(' ', '-').replace('&', 'and')
        }
        
        response = wcapi.post("products/categories", category_data)
        if response.status_code == 201:
            cat_data = response.json()
            cache[cache_key] = cat_data['id']
            return cat_data['id']
            
    except Exception as e:
        print(f"    Category error: {str(e)}")
    
    return None

def extract_diagram_info_from_html(html_path):
    """Extract product info from HTML file"""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'lxml')
        
        # Try to extract diagram code from legend-header
        diagram_code = None
        legend_header = soup.find('div', class_='legend-header')
        if legend_header:
            legend_title = legend_header.find('div', class_='legend-title')
            if legend_title:
                import re
                text = legend_title.get_text(strip=True)
                match = re.search(r'([A-Z]{2}\d+[A-Z]?\d+)', text)
                if match:
                    diagram_code = match.group(1)
        
        return diagram_code
        
    except Exception as e:
        return None

def create_woocommerce_product(diagram_filename, html_path, image_id):
    """
    Create WooCommerce product with uploaded image
    """
    try:
        # Extract info from filename
        parts = diagram_filename.replace('.png', '').replace('.svg', '').split('_', 1)
        serial_number = parts[0]
        diagram_name = parts[1].replace('_', ' ')
        
        # Extract diagram code from HTML
        diagram_code = extract_diagram_info_from_html(html_path)
        
        # Build product title
        if diagram_code:
            product_title = f"{diagram_code} - {diagram_name}"
        else:
            product_title = diagram_name
        
        # Build categories: Serial Number → Category → Diagram Name
        category_path = html_path.parent.name
        
        # Create category hierarchy
        category_ids = []
        parent_id = 0
        
        # Serial number category
        cat_id = get_or_create_category(serial_number, parent_id)
        if cat_id:
            category_ids.append(cat_id)
            parent_id = cat_id
        
        # Folder/category name
        cat_id = get_or_create_category(category_path, parent_id)
        if cat_id:
            category_ids.append(cat_id)
        
        # Build product description
        description = f"<p><strong>Diagram:</strong> {diagram_name}</p>"
        if diagram_code:
            description += f"<p><strong>Diagram Code:</strong> {diagram_code}</p>"
        description += f"<p><strong>Serial Number:</strong> {serial_number}</p>"
        description += f"<p>Technical diagram for {diagram_name}.</p>"
        
        # Build product data
        product_data = {
            "name": product_title,
            "type": "simple",
            "sku": f"{serial_number}-{diagram_name.replace(' ', '-')}",
            "regular_price": "0.00",
            "description": description,
            "short_description": f"Diagram: {diagram_name}",
            "categories": [{"id": cat_id} for cat_id in category_ids],
            "images": [{"id": image_id}],
            "manage_stock": False,
            "stock_status": "instock",
            "meta_data": [
                {"key": "diagram_code", "value": diagram_code or ""},
                {"key": "serial_number", "value": serial_number},
                {"key": "diagram_name", "value": diagram_name},
                {"key": "image_type", "value": "svg"}
            ]
        }
        
        # Create product
        response = wcapi.post("products", product_data)
        
        if response.status_code == 201:
            product = response.json()
            return product['id']
        else:
            print(f"    Product creation failed: HTTP {response.status_code}")
            print(f"    Response: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"    Product error: {str(e)}")
        return None

def process_failed_diagram(diagram_filename, data_dir):
    """
    Process a single failed diagram:
    1. Find HTML file
    2. Extract SVG
    3. Upload SVG to WordPress
    4. Create WooCommerce product with SVG
    """
    result = {
        'filename': diagram_filename,
        'success': False,
        'error': None,
        'media_id': None,
        'product_id': None
    }
    
    # Find HTML file
    html_path = find_html_file_for_diagram(diagram_filename, data_dir)
    if not html_path:
        result['error'] = "HTML file not found"
        return result
    
    # Extract SVG
    svg_content = extract_svg_from_html(html_path)
    if not svg_content:
        result['error'] = "No SVG found in HTML"
        return result
    
    # Create SVG filename
    svg_filename = diagram_filename.replace('.png', '.svg')
    
    # Upload SVG
    media_id = upload_svg_to_wordpress(svg_content, svg_filename)
    if not media_id:
        result['error'] = "SVG upload failed"
        return result
    
    result['media_id'] = media_id
    
    # Create product
    product_id = create_woocommerce_product(diagram_filename, html_path, media_id)
    if not product_id:
        result['error'] = "Product creation failed"
        return result
    
    result['product_id'] = product_id
    result['success'] = True
    
    return result

def main():
    """Process all failed diagrams from conversion_errors.txt"""
    
    # Read failed diagrams list
    errors_file = base_dir / 'conversion_errors.txt'
    if not errors_file.exists():
        print(f"✗ Error file not found: {errors_file}")
        return
    
    with open(errors_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Extract diagram filenames (skip header lines)
    failed_diagrams = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
    
    print("\n" + "="*60)
    print("Import Failed Diagrams as SVG Products")
    print("="*60)
    print(f"Total failed diagrams: {len(failed_diagrams)}")
    print(f"WordPress: {WP_URL}")
    print("="*60 + "\n")
    
    # Data directory
    data_dir = base_dir / 'LSFAL11A4PA157987'
    
    # Process each diagram
    stats = {'success': 0, 'failed': 0, 'errors': []}
    
    for diagram_file in tqdm(failed_diagrams, desc="Processing diagrams"):
        print(f"\n{diagram_file}")
        
        result = process_failed_diagram(diagram_file, data_dir)
        
        if result['success']:
            print(f"  ✓ Media ID: {result['media_id']}")
            print(f"  ✓ Product ID: {result['product_id']}")
            stats['success'] += 1
        else:
            print(f"  ✗ Failed: {result['error']}")
            stats['failed'] += 1
            stats['errors'].append(f"{diagram_file}: {result['error']}")
        
        # Rate limiting
        time.sleep(0.5)
    
    # Print summary
    print("\n" + "="*60)
    print("Import Complete")
    print("="*60)
    print(f"✓ Successful: {stats['success']}")
    print(f"✗ Failed: {stats['failed']}")
    print("="*60 + "\n")
    
    if stats['errors']:
        print("Errors:")
        for error in stats['errors'][:10]:
            print(f"  - {error}")
        if len(stats['errors']) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more")

if __name__ == "__main__":
    main()
