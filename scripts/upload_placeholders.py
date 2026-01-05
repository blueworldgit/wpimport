"""
Upload Placeholder Images to WordPress Media Library
Handles authentication properly for WordPress REST API
"""
import sys
import requests
from pathlib import Path
import base64

# Add parent directory to path for config
base_dir = Path(__file__).parent.parent
sys.path.insert(0, str(base_dir))

from config import WORDPRESS_URL

def upload_placeholder_images():
    """Upload placeholder images using WordPress REST API"""
    
    # Load keys
    keys_file = base_dir / 'keys.txt'
    with open(keys_file, 'r') as f:
        content = f.read().strip()
        lines = content.split('\n')
        consumer_key = None
        consumer_secret = None
        
        for i, line in enumerate(lines):
            if 'ck_' in line:
                consumer_key = line.strip()
            elif 'cs_' in line:
                consumer_secret = line.strip()
    
    print("\n" + "="*60)
    print("Uploading Placeholder Images to WordPress")
    print("="*60)
    print(f"WordPress URL: {WORDPRESS_URL}\n")
    
    placeholder_dir = base_dir / 'images' / 'placeholders'
    placeholders = {
        'general': placeholder_dir / 'placeholder_general.png',
        'left': placeholder_dir / 'placeholder_left.png',
        'right': placeholder_dir / 'placeholder_right.png'
    }
    
    uploaded_ids = {}
    media_url = f"{WORDPRESS_URL}/wp-json/wp/v2/media"
    
    for key, filepath in placeholders.items():
        if not filepath.exists():
            print(f"⚠ Placeholder not found: {filepath}")
            continue
        
        print(f"Uploading {key} placeholder...")
        
        try:
            # Read image file
            with open(filepath, 'rb') as img:
                image_data = img.read()
            
            # Prepare headers
            headers = {
                'Content-Disposition': f'attachment; filename="{filepath.name}"',
                'Content-Type': 'image/png'
            }
            
            # Upload using WooCommerce API authentication
            response = requests.post(
                media_url,
                headers=headers,
                data=image_data,
                auth=(consumer_key, consumer_secret),
                timeout=30
            )
            
            if response.status_code == 201:
                media_data = response.json()
                uploaded_ids[key] = media_data['id']
                print(f"  ✓ Uploaded successfully (Media ID: {media_data['id']})")
                print(f"    URL: {media_data['source_url']}")
            else:
                print(f"  ✗ Upload failed: {response.status_code}")
                print(f"    Response: {response.text[:200]}")
        
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
    
    print("\n" + "="*60)
    print("Upload Summary")
    print("="*60)
    print(f"Successfully uploaded: {len(uploaded_ids)}/3")
    print(f"Placeholder IDs: {uploaded_ids}")
    print("="*60 + "\n")
    
    if len(uploaded_ids) == 3:
        print("✓ All placeholders uploaded successfully!")
        print("\nSave these IDs for the import script:")
        for key, media_id in uploaded_ids.items():
            print(f"  {key}: {media_id}")
        
        # Save IDs to a file for the import script
        ids_file = base_dir / 'placeholder_ids.txt'
        with open(ids_file, 'w') as f:
            for key, media_id in uploaded_ids.items():
                f.write(f"{key}={media_id}\n")
        
        print(f"\n✓ IDs saved to: {ids_file}")
    else:
        print("⚠️ Some placeholders failed to upload.")
        print("\nTroubleshooting:")
        print("  1. Check if WordPress allows file uploads")
        print("  2. Verify WooCommerce API permissions")
        print("  3. Check WordPress file size limits")
    
    return uploaded_ids

if __name__ == "__main__":
    upload_placeholder_images()
