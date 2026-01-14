#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from scripts.bulk_import_optimizer import BulkImportOptimizer

opt = BulkImportOptimizer()
opt.preload_categories()

# Test normalization
test_cat = 'Hvac & Powertrain Coolingin'
actual_cat = 'Hvac and Powertrain Coolingin'

print("Normalization test:")
print(f'Search: "{test_cat}"')
print(f'  Normalized: "{opt.normalize_category_name(test_cat)}"')
print(f'Actual: "{actual_cat}"')
print(f'  Normalized: "{opt.normalize_category_name(actual_cat)}"')
print(f'Match: {opt.normalize_category_name(test_cat) == opt.normalize_category_name(actual_cat)}')

result = opt.find_category_id(test_cat)
print(f'\nResult: {result}')