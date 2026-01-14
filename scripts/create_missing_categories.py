#!/usr/bin/env python3
"""
Missing Category Creator
Creates missing categories identified in bulk import error logs
"""
import requests
import json
from pathlib import Path
import sys

# Add parent directory for imports
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))
from config import WORDPRESS_URL

def load_credentials():
    """Load WooCommerce credentials"""
    keys_file = base_dir / 'keys.txt'
    if not keys_file.exists():
        raise FileNotFoundError("keys.txt not found")
    
    with open(keys_file, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
        
    consumer_key = None
    consumer_secret = None
    
    for i, line in enumerate(lines):
        if 'Consumer key' in line and i+1 < len(lines): 
            consumer_key = lines[i+1]
        if 'Consumer secret' in line and i+1 < len(lines): 
            consumer_secret = lines[i+1]
    
    return consumer_key, consumer_secret

def create_missing_categories():
    """Create missing categories from error analysis"""
    consumer_key, consumer_secret = load_credentials()
    
    # Missing categories identified in logs
    missing_categories = [
        'Hvac & Powertrain Coolingin',
        'JE312A001 - Refrigerant Plumbing & Hardware',
        'JE421AE001 - Seat Arrangement of Shang Jie\'s 11 12and 14 Seats (Australia)',
        'JE152A001 - Transmission Shift Actuation-MT'
    ]
    
    print(f"🔧 Creating {len(missing_categories)} missing categories...")
    
    created = 0
    errors = 0
    
    for category_name in missing_categories:
        try:
            # Create category
            category_data = {
                'name': category_name,
                'description': f'Auto-created category for {category_name}',
                'display': 'default',
                'image': None,
                'menu_order': 0,
                'parent': 0
            }
            
            url = f"{WORDPRESS_URL}/wp-json/wc/v3/products/categories"
            response = requests.post(
                url,
                json=category_data,
                auth=(consumer_key, consumer_secret),
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 201:
                result = response.json()
                print(f"   ✅ Created: '{category_name}' (ID: {result['id']})")
                created += 1
            else:
                print(f"   ❌ Failed: '{category_name}' - {response.status_code}: {response.text[:100]}")
                errors += 1
                
        except Exception as e:
            print(f"   ❌ Exception: '{category_name}' - {e}")
            errors += 1
    
    print(f"\n📊 Results:")
    print(f"   Categories created: {created}")
    print(f"   Errors: {errors}")
    
    return created, errors

if __name__ == "__main__":
    create_missing_categories()