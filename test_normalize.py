from pathlib import Path

def normalize_name(name):
    """Normalize name for comparison"""
    return name.lower().replace('_', ' ').replace('&', 'and').replace(',', '').strip()

# Test normalization
diagram_filename = 'LSFAL11A4PA157987_Body_Interior_&_Exterior_Electronics.png'
parts = diagram_filename.replace('.png', '').replace('.svg', '').split('_', 1)

serial_number = parts[0]
diagram_name = parts[1]

print(f"Serial: {serial_number}")
print(f"Diagram name raw: {diagram_name}")

normalized_target = normalize_name(diagram_name)
print(f"Normalized target: '{normalized_target}'")

# Check HTML file
html_path = Path('LSFAL11A4PA157987/body interior & exterior electronics/Body Interior & Exterior Electronics.html')
html_name = normalize_name(html_path.stem)
print(f"\nHTML stem: '{html_path.stem}'")
print(f"HTML normalized: '{html_name}'")

print(f"\nDo they match? {html_name == normalized_target}")

# Try with data_dir logic
data_dir = Path('LSFAL11A4PA157987')
serial_dir = data_dir / serial_number
print(f"\nSerial dir: {serial_dir}")
print(f"Serial dir exists: {serial_dir.exists()}")

# This is the problem - data_dir already IS the serial dir!
print(f"\nAHA! data_dir is ALREADY the serial dir")
print(f"So serial_dir becomes: {data_dir / serial_number}")
print(f"Which is: LSFAL11A4PA157987/LSFAL11A4PA157987 - WRONG!")
