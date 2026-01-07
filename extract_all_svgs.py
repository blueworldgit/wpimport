"""
Extract SVG files for failed PNG conversions
Only extracts SVG files to images/converted/ - does NOT create products
"""
from pathlib import Path
from bs4 import BeautifulSoup
from tqdm import tqdm

def find_html_file_for_diagram(diagram_filename, data_dir):
    """Find HTML file for a diagram"""
    parts = diagram_filename.replace('.png', '').replace('.svg', '').split('_', 1)
    if len(parts) < 2:
        return None
    
    serial_number = parts[0]
    diagram_name = parts[1]
    
    serial_dir = data_dir
    if not serial_dir.exists():
        return None
    
    def normalize_name(name):
        return name.lower().replace('_', ' ').replace('&', 'and').replace(',', '').strip()
    
    normalized_target = normalize_name(diagram_name)
    
    for html_file in serial_dir.rglob('*.html'):
        html_name = normalize_name(html_file.stem)
        if html_name == normalized_target:
            return html_file
    
    # Fuzzy match
    target_words = set(normalized_target.split())
    best_match = None
    best_score = 0
    
    for html_file in serial_dir.rglob('*.html'):
        html_name = normalize_name(html_file.stem)
        html_words = set(html_name.split())
        
        if target_words and html_words:
            common_words = target_words & html_words
            score = len(common_words) / max(len(target_words), len(html_words))
            
            if score > best_score and score >= 0.7:
                best_score = score
                best_match = html_file
    
    return best_match

def extract_svg_from_html(html_path):
    """Extract SVG from HTML file"""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'lxml')
        
        svg = soup.find('svg')
        if not svg:
            return None
        
        svg_string = str(svg)
        if 'xmlns' not in svg_string:
            svg_string = svg_string.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ')
        
        return svg_string
    except Exception as e:
        return None

def main():
    base_dir = Path(__file__).parent
    data_dir = base_dir / 'LSFAL11A4PA157987'
    output_dir = base_dir / 'images' / 'converted'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Read failed diagrams
    errors_file = base_dir / 'conversion_errors.txt'
    with open(errors_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    failed_diagrams = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
    
    print("\n" + "="*60)
    print("Extract SVG Files for Failed PNG Conversions")
    print("="*60)
    print(f"Total diagrams: {len(failed_diagrams)}")
    print(f"Output: {output_dir}")
    print("="*60 + "\n")
    
    stats = {'success': 0, 'failed': 0, 'skipped': 0}
    
    for diagram_file in tqdm(failed_diagrams, desc="Extracting SVGs"):
        svg_filename = diagram_file.replace('.png', '.svg')
        svg_path = output_dir / svg_filename
        
        # Skip if already exists
        if svg_path.exists():
            stats['skipped'] += 1
            continue
        
        # Find HTML
        html_path = find_html_file_for_diagram(diagram_file, data_dir)
        if not html_path:
            stats['failed'] += 1
            continue
        
        # Extract SVG
        svg_content = extract_svg_from_html(html_path)
        if not svg_content:
            stats['failed'] += 1
            continue
        
        # Save SVG
        try:
            with open(svg_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            stats['success'] += 1
        except Exception as e:
            stats['failed'] += 1
    
    print("\n" + "="*60)
    print("Extraction Complete")
    print("="*60)
    print(f"Success: {stats['success']}")
    print(f"Skipped (already exists): {stats['skipped']}")
    print(f"Failed: {stats['failed']}")
    print("="*60 + "\n")
    
    print("Next: Run scripts/import_to_woocommerce.py")
    print("It will automatically use PNG when available, SVG when not\n")

if __name__ == "__main__":
    main()
