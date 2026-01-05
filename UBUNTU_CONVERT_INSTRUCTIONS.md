# SVG to PNG Conversion on Ubuntu

## Quick Setup (5 minutes)

### Step 1: Copy files to Ubuntu
```bash
# Create working directory
mkdir -p ~/svg_converter/svg_files
cd ~/svg_converter
```

Copy these files from Windows:
- `convert_svg_linux.py` (this conversion script)
- All SVG files from `images/converted/` → put in `svg_files/` folder

### Step 2: Install cairosvg
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y libcairo2-dev pkg-config python3-pip

# Install Python packages
pip3 install cairosvg tqdm
```

### Step 3: Run conversion
```bash
# Make script executable
chmod +x convert_svg_linux.py

# Run conversion
python3 convert_svg_linux.py
```

**Output:** PNG files will be in `png_output/` folder

### Step 4: Copy PNGs back to Windows
Copy all PNG files from `png_output/` back to Windows:
`C:\pythonstuff\wpimport\images\converted\`

---

## Expected Results
- **Speed**: ~1-2 seconds per SVG (20 files = ~30 seconds total)
- **Quality**: 2000px width, high quality PNG
- **Size**: ~200-500KB per PNG

---

## Troubleshooting

### If cairosvg install fails:
```bash
sudo apt-get install -y python3-dev build-essential
pip3 install --upgrade pip
pip3 install cairosvg
```

### If no SVG files found:
Make sure SVG files are in `./svg_files/` directory

### If conversion fails:
Check error messages - usually indicates corrupted SVG

---

## Alternative: One-liner conversion
If you prefer command line:
```bash
for f in svg_files/*.svg; do 
  cairosvg "$f" -o "png_output/$(basename "$f" .svg).png" -W 2000
done
```
