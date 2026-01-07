"""
Test WordPress Application Password Authentication
"""
import requests

# WordPress credentials
WP_URL = "https://maxusvanparts.co.uk"
WP_USERNAME = "developer"
WP_APP_PASSWORD = "nIbM 6KlW sft3 hQyj OG4P ZYeI"

print("="*60)
print("Testing WordPress Application Password")
print("="*60)
print(f"URL: {WP_URL}")
print(f"Username: {WP_USERNAME}")
print(f"App Password: {WP_APP_PASSWORD[:10]}...")
print()

# Test 1: Get current user info
print("Test 1: Checking authentication with /wp-json/wp/v2/users/me")
print("-"*60)
response = requests.get(
    f"{WP_URL}/wp-json/wp/v2/users/me",
    auth=(WP_USERNAME, WP_APP_PASSWORD)
)
print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    user_data = response.json()
    print(f"✓ Authentication successful!")
    print(f"  User ID: {user_data.get('id')}")
    print(f"  User Name: {user_data.get('name')}")
    print(f"  User Roles: {user_data.get('roles')}")
else:
    print(f"✗ Authentication failed!")
    print(f"  Response: {response.text[:200]}")

print()

# Test 2: Try to upload a small test image
print("Test 2: Attempting image upload to /wp-json/wp/v2/media")
print("-"*60)

# Create a tiny 1x1 PNG in memory
import io
from PIL import Image

img = Image.new('RGB', (1, 1), color='red')
img_bytes = io.BytesIO()
img.save(img_bytes, format='PNG')
img_bytes.seek(0)
image_data = img_bytes.read()

response = requests.post(
    f"{WP_URL}/wp-json/wp/v2/media",
    data=image_data,
    auth=(WP_USERNAME, WP_APP_PASSWORD),
    headers={
        'Content-Disposition': 'attachment; filename=test.png',
        'Content-Type': 'image/png'
    }
)

print(f"Status Code: {response.status_code}")
if response.status_code == 201:
    media_data = response.json()
    print(f"✓ Image upload successful!")
    print(f"  Media ID: {media_data.get('id')}")
    print(f"  URL: {media_data.get('source_url')}")
elif response.status_code == 401:
    print(f"✗ Authentication failed (401 Unauthorized)")
    print(f"  Response: {response.text[:300]}")
else:
    print(f"✗ Upload failed with status {response.status_code}")
    print(f"  Response: {response.text[:300]}")

print()
print("="*60)
