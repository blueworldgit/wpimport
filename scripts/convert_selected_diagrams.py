import json
from pathlib import Path
import cairosvg
import sys

base = Path(__file__).resolve().parent.parent
serial = sys.argv[1] if len(sys.argv) > 1 else None
limit = None
if len(sys.argv) > 2:
    try:
        limit = int(sys.argv[2])
    except Exception:
        pass

if not serial:
    print('Usage: convert_selected_diagrams.py <serial> [limit]')
    sys.exit(2)

data_file = base / serial / 'extracted_data_full.json'
if not data_file.exists():
    print('Data file missing:', data_file)
    sys.exit(2)

with open(data_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

products = data.get('products', [])
if limit:
    products = products[:limit]

out_dir = base / 'images' / 'converted'
converted = []
skipped = []
errors = []

for p in products:
    diag = p.get('diagram_file', '')
    if not diag:
        errors.append((p.get('sku'), 'no diagram_file'))
        continue
    name = Path(diag).stem.replace(' ', '_')
    svg = out_dir / f"{serial}_{name}.svg"
    png = out_dir / f"{serial}_{name}.png"
    if png.exists():
        skipped.append(png.name)
        continue
    if not svg.exists():
        errors.append((p.get('sku'), f'svg missing: {svg.name}'))
        continue
    try:
        cairosvg.svg2png(url=str(svg), write_to=str(png), output_width=2000)
        converted.append(png.name)
    except Exception as e:
        errors.append((p.get('sku'), f'convert error: {e}'))

print('Converted:', len(converted))
for c in converted[:20]:
    print('  ', c)
print('Skipped existing:', len(skipped))
print('Errors:', len(errors))
for e in errors[:20]:
    print('  ', e)
