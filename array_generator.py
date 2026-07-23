import csv
 
INPUT_FILE = "date_updated_all_7days_unique_sku.csv"
OUTPUT_FILE = "codes_output.py"
 
codes = []
 
with open(INPUT_FILE, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        sku = row.get("original_sku", "").strip()
        if sku:
            codes.append(sku)
 
# Print to console
print("codes = [")
for code in codes:
    print(f"    '{code}',")
print("]")
 
# Also save to a .py file so you can import it elsewhere
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("codes = [\n")
    for code in codes:
        f.write(f"    '{code}',\n")
    f.write("]\n")
 
print(f"\n{len(codes)} codes written to {OUTPUT_FILE}")