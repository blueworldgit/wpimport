#!/usr/bin/env python3
"""
Debug script to test category search for diagram code categories
"""
from pathlib import Path
import sys
import unicodedata

base_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(base_dir))

from config import WORDPRESS_URL
from woocommerce import API

# Load credentials
keys_file = base_dir / 'keys.txt'
consumer_key = consumer_secret = None
if keys_file.exists():
    with open(keys_file, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
        for i, line in enumerate(lines):
            if 'Consumer key' in line and i+1 < len(lines): 
                consumer_key = lines[i+1]
            if 'Consumer secret' in line and i+1 < len(lines): 
                consumer_secret = lines[i+1]

wcapi = API(url=WORDPRESS_URL, consumer_key=consumer_key, consumer_secret=consumer_secret, version='wc/v3')

def normalize_category_name(name):
    """Strip punctuation and normalize for comparison"""
    import string
    import unicodedata
    
    # Convert to lowercase
    normalized = name.lower()
    
    # Remove all punctuation (including Unicode punctuation like Japanese comma)
    # This handles both ASCII and Unicode punctuation
    normalized = ''.join(char for char in normalized 
                       if unicodedata.category(char)[0] != 'P')
    
    # Remove extra whitespace
    normalized = ' '.join(normalized.split())
    
    return normalized

# The problematic diagram code categories
search_terms = [
    "JE11CQ001 - AccessoryandAccessoryDrive",
    "JE11CR001 - SensorandHarness", 
    "JE11CU001 - LP-EGR intake pipeandAccessory",
    "JE11CL001 - Coolant Pump And InlandOtltTubeandThermostat"
]

for search_term in search_terms:
    print(f"\n🔍 Testing category search for: {search_term}")
    print(f"📝 Normalized search: {normalize_category_name(search_term)}")
    print("="*70)
    
    # Test different search strategies
    test_searches = [
        search_term,  # Full term
        search_term.split(' - ')[0] if ' - ' in search_term else search_term.split()[0],  # Just the code part: "JE11CQ001"
        search_term.split(' - ')[1] if ' - ' in search_term else ' '.join(search_term.split()[1:]),  # Just description part
        ' '.join(search_term.split()[:2]),  # Current strategy: "JE11CQ001 -"
    ]
    
    found_match = False
    
    for i, test_search in enumerate(test_searches, 1):
        print(f"\n{i}. Searching for: '{test_search}'")
        response = wcapi.get('products/categories', params={
            'search': test_search,
            'per_page': 100
        })
        
        if response.status_code == 200:
            categories = response.json()
            print(f"   📦 Found {len(categories)} categories")
            
            for cat in categories:
                cat_name = cat['name']
                normalized_existing = normalize_category_name(cat_name)
                normalized_search = normalize_category_name(search_term)
                
                # Check if this could be our target
                if normalized_existing == normalized_search:
                    print(f"      🎯 EXACT MATCH: ID {cat['id']}: '{cat_name}'")
                    found_match = True
                elif search_term.split()[0] in cat_name:  # Check for code match
                    print(f"      📝 POTENTIAL: ID {cat['id']}: '{cat_name}'")
        else:
            print(f"   ❌ API Error: {response.status_code}")
    
    if not found_match:
        print(f"\n❌ NO EXACT MATCH FOUND FOR: {search_term}")
    print("\n" + "="*70)