from pathlib import Path
from import_svg_products import find_html_file_for_diagram

data_dir = Path('LSFAL11A4PA157987')
diagram = 'LSFAL11A4PA157987_Body_Interior_&_Exterior_Electronics.png'

print(f"Data dir: {data_dir}")
print(f"Data dir exists: {data_dir.exists()}")
print(f"Looking for: {diagram}")

# Check HTML files
html_files = list(data_dir.rglob('*.html'))
print(f"\nFound {len(html_files)} HTML files total")

# Check specific folder
target_folder = data_dir / 'body interior & exterior electronics'
print(f"\nTarget folder: {target_folder}")
print(f"Target folder exists: {target_folder.exists()}")

if target_folder.exists():
    files_in_folder = list(target_folder.glob('*.html'))
    print(f"HTML files in folder: {len(files_in_folder)}")
    for f in files_in_folder:
        print(f"  - {f.name}")

# Test the function
result = find_html_file_for_diagram(diagram, data_dir)
print(f"\nFunction result: {result}")
