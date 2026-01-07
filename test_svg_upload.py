"""
Test SVG Upload to WordPress
Upload a single SVG file to test WordPress SVG support
"""
import sys
from pathlib import Path
import requests

# Base directory (script is in root)
base_dir = Path(__file__).parent
sys.path.insert(0, str(base_dir))

# Import credentials
import config

def upload_svg_to_wordpress(svg_path, wp_url, wp_username, wp_app_password):
    """
    Upload SVG file to WordPress media library
    """
    try:
        print(f"\nUploading: {svg_path.name}")
        print(f"Size: {svg_path.stat().st_size / 1024:.2f} KB")
        
        # Read SVG file
        with open(svg_path, 'rb') as svg_file:
            svg_content = svg_file.read()
        
        # Prepare headers
        headers = {
            'Content-Disposition': f'attachment; filename={svg_path.name}',
            'Content-Type': 'image/svg+xml'
        }
        
        # Upload via WordPress REST API
        print(f"\nUploading to: {wp_url}/wp-json/wp/v2/media")
        
        response = requests.post(
            f"{wp_url}/wp-json/wp/v2/media",
            data=svg_content,
            headers=headers,
            auth=(wp_username, wp_app_password),
            timeout=60
        )
        
        # Check response
        if response.status_code == 201:
            media_data = response.json()
            print("\n" + "="*60)
            print("✓ SVG Upload Successful!")
            print("="*60)
            print(f"Media ID: {media_data['id']}")
            print(f"Title: {media_data['title']['rendered']}")
            print(f"URL: {media_data['source_url']}")
            print(f"MIME Type: {media_data['mime_type']}")
            print(f"File Size: {media_data.get('media_details', {}).get('filesize', 'N/A')} bytes")
            print("="*60 + "\n")
            
            print("✓ SVG support is working!")
            print(f"✓ View image at: {media_data['source_url']}")
            
            return media_data
        else:
            print("\n" + "="*60)
            print("✗ Upload Failed")
            print("="*60)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            print("="*60 + "\n")
            
            if response.status_code == 400:
                print("⚠ Possible issues:")
                print("  1. SVG file type not allowed")
                print("  2. Safe SVG plugin not installed/activated")
                print("  3. File contains invalid SVG content")
            elif response.status_code == 401:
                print("⚠ Authentication failed - check credentials")
            
            return None
            
    except Exception as e:
        print(f"\n✗ Error uploading SVG: {str(e)}")
        return None

def main():
    """Test upload SVG to WordPress"""
    
    # SVG file to upload - use the correct base_dir which is already parent of scripts
    svg_file = base_dir / 'images' / 'converted' / 'LSFAL11A4PA157987_Body_Interior_&_Exterior_Electronics.svg'
    
    # Debug: show the path we're looking for
    print(f"Looking for: {svg_file}")
    print(f"Base dir: {base_dir}")
    
    if not svg_file.exists():
        print(f"\n✗ SVG file not found: {svg_file}")
        print("Run extract_svg_vector.py first to extract the SVG")
        return
    
    print("\n" + "="*60)
    print("WordPress SVG Upload Test")
    print("="*60)
    
    # WordPress credentials
    wp_url = "https://maxusvanparts.co.uk"
    wp_username = "developer"
    wp_app_password = "nIbM 6KlW sft3 hQyj OG4P ZYeI"
    
    print(f"\nWordPress URL: {wp_url}")
    print(f"Username: {wp_username}")
    
    # Upload SVG
    result = upload_svg_to_wordpress(
        svg_file,
        wp_url,
        wp_username,
        wp_app_password
    )
    
    if result:
        print("\n" + "="*60)
        print("Next Steps")
        print("="*60)
        print("1. Open WordPress Media Library to verify SVG displays")
        print("2. Try adding the SVG to a WooCommerce product")
        print("3. Check if it displays on the frontend")
        print("4. If successful, we can batch upload all 152 failed diagrams as SVGs")
        print("="*60 + "\n")

if __name__ == "__main__":
    main()
