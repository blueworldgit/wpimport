import pandas as pd
import json

# Load Excel
df = pd.read_excel('PRCJUL25.xlsx')
df['Part Number'] = df['Part Number'].astype(str).str.strip()

# Load imported SKUs
with open('data/extracted/extracted_data_test.json', 'r') as f:
    data = json.load(f)

imported_skus = []
for p in data['products']:
    if p['type'] == 'simple':
        imported_skus.append(p['sku'])
    else:
        for v in p['variations']:
            imported_skus.append(v['sku'])

print(f"Total imported SKUs: {len(imported_skus)}")
print(f"\nChecking if they exist in Excel:\n")

found = 0
not_found = []

for sku in imported_skus[:10]:  # Check first 10
    match = df[df['Part Number'] == sku]
    if not match.empty:
        price = match['Retail Price'].values[0]
        print(f"✓ {sku}: £{price:.2f}")
        found += 1
    else:
        print(f"✗ {sku}: NOT FOUND")
        not_found.append(sku)

print(f"\nFound: {found}/{len(imported_skus[:10])}")
