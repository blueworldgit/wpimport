from pathlib import Path
import sys
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))
from scripts.convert_svg_to_png import SVGConverter

if len(sys.argv) < 2:
    print('Usage: convert_one_serial.py <serial_folder> [limit]')
    sys.exit(2)

serial = sys.argv[1]
limit = None
if len(sys.argv) >= 3:
    try:
        limit = int(sys.argv[2])
    except Exception:
        pass

serial_dir = base_dir / serial
if not serial_dir.exists():
    print('Serial folder not found:', serial_dir)
    sys.exit(2)

output_dir = base_dir / 'images' / 'converted'
converter = SVGConverter(serial_dir, output_dir)
converter.convert_batch(limit=limit)
converter.print_summary()
