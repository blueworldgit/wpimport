"""
WooCommerce Import Script - Phase 3
Imports products from extracted JSON data into WooCommerce
"""
import os
import json
import time
from pathlib import Path
from datetime import datetime
from woocommerce import API
from tqdm import tqdm

class WooCommerceImporter:
    def __init__(self, api_url, consumer_key, consumer_secret, checkpoint_dir, log_dir, wp_username=None, wp_app_password=None):
        self.wcapi = API(
            url=api_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            version="wc/v3",
            timeout=30
        )
        self.wp_username = wp_username
        self.wp_app_password = wp_app_password
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create error log file
        self.error_log_path = self.log_dir / f"import_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        self.stats = {
            'start_time': datetime.now().isoformat(),
            'products_created': 0,
            'products_updated': 0,
            'variations_created': 0,
            'categories_created': 0,
            'images_uploaded': 0,
            'errors': [],
            'skipped': []
        }
        self.category_cache = {}  # name -> ID mapping
        self.placeholder_ids = {}  # Will store uploaded placeholder image IDs
        self.processed_skus = set()  # Track processed SKUs to avoid duplicates
        
        # Try to load existing checkpoint
        self.load_checkpoint()

    def load_checkpoint(self, filename='import_checkpoint.json'):
        """Load previous import progress if it exists and ensure shared parent category.
        Populates `processed_skus`, `category_cache`, `placeholder_ids` and merges stats.
        Also ensures the shared top-level parent category exists and stores its ID.
        """
        checkpoint_path = self.checkpoint_dir / filename
        self.shared_parent_name = 'Maxus'
        self.shared_parent_id = 0

        if not checkpoint_path.exists():
            # Ensure we still create/get the shared parent even without a checkpoint
            try:
                self.shared_parent_id = self.get_or_create_category(self.shared_parent_name, parent_id=0) or 0
            except Exception:
                self.shared_parent_id = 0
            return

        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)

            self.processed_skus = set(checkpoint_data.get('processed_skus', []))
            self.category_cache = checkpoint_data.get('category_cache', {}) or {}
            self.placeholder_ids = checkpoint_data.get('placeholder_ids', {}) or {}

            # Merge stats
            old_stats = checkpoint_data.get('stats', {}) or {}
            if old_stats:
                self.stats['products_created'] = old_stats.get('products_created', 0)
                self.stats['products_updated'] = old_stats.get('products_updated', 0)
                self.stats['variations_created'] = old_stats.get('variations_created', 0)
                self.stats['categories_created'] = old_stats.get('categories_created', 0)
                self.stats['images_uploaded'] = old_stats.get('images_uploaded', 0)
                self.stats['errors'].extend(old_stats.get('errors', []))
                self.stats['skipped'].extend(old_stats.get('skipped', []))

            # Ensure shared parent exists (after loading category cache)
            try:
                self.shared_parent_id = self.get_or_create_category(self.shared_parent_name, parent_id=0) or 0
            except Exception:
                self.shared_parent_id = 0

            print(f"\n✓ Loaded checkpoint: {len(self.processed_skus)} products already imported")
            print(f"  Resuming from where you left off...\n")

        except Exception as e:
            print(f"\n⚠ Could not load checkpoint: {e}")
            print("  Starting fresh import...\n")
    
    def log_error(self, error_msg, product_data=None):
        """Log error to both console and file. Optionally include parsed product data."""
        print(f"\n❌ {error_msg}")
        self.stats['errors'].append(error_msg)
        try:
            with open(self.error_log_path, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().isoformat()}] {error_msg}\n")
                if product_data is not None:
                    try:
                        # write product details as JSON for easier debugging
                        f.write(json.dumps({'product': product_data}, ensure_ascii=False) + "\n")
                    except Exception:
                        # fallback to string repr
                        f.write(repr(product_data) + "\n")
        except Exception:
            # avoid raising from logging
            pass
    
    def test_connection(self):
        """Test API connection"""
        try:
            response = self.wcapi.get("products", params={"per_page": 1})
            if response.status_code == 200:
                print("✓ WooCommerce API connection successful")
                return True
            else:
                print(f"✗ API connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ API connection error: {str(e)}")
            return False
    
    def upload_placeholder_images(self, placeholder_dir):
        """
        Upload placeholder images to WordPress media library
        Returns dict mapping placeholder type to media ID
        """
        print("\n" + "="*60)
        print("Uploading Placeholder Images to WordPress")
        print("="*60 + "\n")
        
        placeholders = {
            'general': placeholder_dir / 'placeholder_general.png',
            'left': placeholder_dir / 'placeholder_left.png',
            'right': placeholder_dir / 'placeholder_right.png'
        }
        
        for key, filepath in placeholders.items():
            if not filepath.exists():
                print(f"⚠ Placeholder not found: {filepath}")
                continue
            
            try:
                # Read image file
                with open(filepath, 'rb') as img:
                    image_content = img.read()
                
                # Use WordPress Application Password authentication
                import requests
                
                # Check if we have WordPress credentials
                if not hasattr(self, 'wp_username') or not hasattr(self, 'wp_app_password'):
                    print(f"⚠ Skipping {key}: No WordPress credentials provided")
                    continue
                
                response = requests.post(
                    f"{self.wcapi.url}/wp-json/wp/v2/media",
                    data=image_content,
                    auth=(self.wp_username, self.wp_app_password),
                    headers={
                        'Content-Disposition': f'attachment; filename={filepath.name}',
                        'Content-Type': 'image/png'
                    }
                )
                
                if response.status_code == 201:
                    media_data = response.json()
                    self.placeholder_ids[key] = media_data['id']
                    print(f"✓ Uploaded {key} placeholder (ID: {media_data['id']})")
                    self.stats['images_uploaded'] += 1
                else:
                    print(f"⚠ Failed to upload {key}: {response.status_code}")
            
            except Exception as e:
                print(f"✗ Error uploading {key}: {str(e)}")
        
        print(f"\n✓ Placeholder IDs: {self.placeholder_ids}\n")
        return self.placeholder_ids
    
    def upload_image_to_wordpress(self, image_path):
        """
        Upload image to WordPress media library using Application Password
        Returns image data dict with media ID or None if upload fails
        """
        import requests
        
        try:
            # Check if we have WordPress credentials
            if not hasattr(self, 'wp_username') or not hasattr(self, 'wp_app_password'):
                return None
            
            # Read image file
            with open(image_path, 'rb') as img:
                image_content = img.read()
            
            # Set headers
            headers = {
                'Content-Disposition': f'attachment; filename={image_path.name}',
                'Content-Type': 'image/png' if image_path.suffix == '.png' else 'image/svg+xml'
            }
            
            # Upload via WordPress REST API media endpoint
            response = requests.post(
                f"{self.wcapi.url}/wp-json/wp/v2/media",
                data=image_content,
                headers=headers,
                auth=(self.wp_username, self.wp_app_password),
                timeout=60  # 60 second timeout for large images
            )
            
            if response.status_code == 201:
                media_data = response.json()
                return {'id': media_data['id']}
            else:
                print(f"    Upload failed: HTTP {response.status_code}")
                return None
        
        except Exception as e:
            print(f"    Upload error: {str(e)}")
            return None
    
    def set_category_mappings(self, category_mappings):
        """Set pre-validated category mappings to avoid redundant API calls"""
        if category_mappings:
            self.category_cache.update({
                f"{name}_0": cat_id for name, cat_id in category_mappings.items()
            })
            print(f"✅ Loaded {len(category_mappings)} pre-validated category mappings")
    
    def get_or_create_category(self, category_name, parent_id=0):
        """
        Get existing category ID or create new one
        Uses cache to avoid repeated API calls
        """
        # Check cache first
        cache_key = f"{category_name}_{parent_id}"
        if cache_key in self.category_cache:
            return self.category_cache[cache_key]
        
        # Search for existing category
        try:
            response = self.wcapi.get("products/categories", params={
                "search": category_name,
                "parent": parent_id,
                "per_page": 100
            })
            
            if response.status_code == 200:
                categories = response.json()
                for cat in categories:
                    if cat['name'].lower() == category_name.lower() and cat['parent'] == parent_id:
                        self.category_cache[cache_key] = cat['id']
                        return cat['id']
        except Exception as e:
            print(f"⚠ Error searching category: {str(e)}")
        
        # Create new category
        try:
            # Create a proper slug for WooCommerce with better special character handling
            slug = category_name.lower()
            
            # Handle special characters that cause database issues
            slug = slug.replace('、', '-')  # Japanese comma
            slug = slug.replace('，', '-')  # Chinese comma
            slug = slug.replace('＆', '-and-')  # Full-width ampersand
            slug = slug.replace(' & ', '-and-').replace('&', '-and-')
            slug = slug.replace(' ', '-').replace('/', '-').replace('\\', '-')
            slug = slug.replace('(', '').replace(')', '').replace(',', '')
            slug = slug.replace('：', '-').replace(':', '-')
            slug = slug.replace('｜', '-').replace('|', '-')
            slug = slug.replace('--', '-').strip('-')
            
            # Remove any remaining problematic characters
            import re
            slug = re.sub(r'[^a-z0-9\-]', '', slug)
            slug = re.sub(r'-+', '-', slug).strip('-')
            
            # Ensure slug is not empty
            if not slug:
                slug = 'category-' + str(hash(category_name) % 10000)
            
            category_data = {
                "name": category_name,
                "parent": parent_id,
                "slug": slug
            }
            
            response = self.wcapi.post("products/categories", category_data)
            
            if response.status_code == 201:
                cat_data = response.json()
                self.category_cache[cache_key] = cat_data['id']
                self.stats['categories_created'] += 1
                return cat_data['id']
            else:
                # Show detailed error response
                try:
                    error_details = response.json()
                    print(f"⚠ Failed to create category '{category_name}': {response.status_code}")
                    print(f"   Error: {error_details}")
                    print(f"   Slug attempted: '{slug}'")
                except:
                    print(f"⚠ Failed to create category '{category_name}': {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            print(f"✗ Error creating category '{category_name}': {str(e)}")
            return None
    
    def build_category_hierarchy(self, categories_list):
        """
        Build category hierarchy and return category IDs
        categories_list: [serial, parent_category, diagram_name]
        Returns: list of category IDs
        """
        category_ids = []
        # Top-level parent for serial categories should be the shared parent
        parent_id = getattr(self, 'shared_parent_id', 0) or 0

        # Avoid duplicating the shared parent if extractor already includes it
        shared_name = getattr(self, 'shared_parent_name', 'Maxus') or 'Maxus'
        if categories_list and categories_list[0].strip().lower() == shared_name.strip().lower():
            categories_iter = categories_list[1:]
        else:
            categories_iter = categories_list

        for category_name in categories_iter:
            # First check if we have a pre-validated mapping (prioritize this to avoid redundant API calls)
            cache_key = f"{category_name}_0"
            if cache_key in self.category_cache:
                cat_id = self.category_cache[cache_key]
                if cat_id:
                    category_ids.append(cat_id)
                    parent_id = cat_id  # Next category is child of this one
                continue
            
            # Fallback to get_or_create_category only if no pre-validated mapping exists
            cat_id = self.get_or_create_category(category_name, parent_id)
            if cat_id:
                category_ids.append(cat_id)
                parent_id = cat_id  # Next category is child of this one
        
        return category_ids
    
    def get_diagram_image_path(self, product_data):
        """
        Find diagram image for product (PNG or SVG)
        Priority: PNG → SVG → placeholder
        Returns: (file_path, file_type) or (None, None)
        """
        base_dir = Path(__file__).resolve().parent.parent
        images_dir = base_dir / 'images' / 'converted'
        
        # Get serial number and diagram name from product data
        diagram_file = product_data.get('diagram_file', '')
        if diagram_file:
            # Extract diagram name from HTML file path
            diagram_name = Path(diagram_file).stem.replace(' ', '_')
            
            # Build expected filename pattern (SerialNumber_DiagramName)
            # Try to extract serial from categories
            categories = product_data.get('categories', [])
            serial_number = None
            for cat in categories:
                if cat.startswith('LSF') and len(cat) == 17:
                    serial_number = cat
                    break
            
            if serial_number:
                base_filename = f"{serial_number}_{diagram_name}"
                
                # Check for PNG first (preferred)
                png_path = images_dir / f"{base_filename}.png"
                if png_path.exists():
                    return (png_path, 'png')
                
                # Check for SVG as fallback
                svg_path = images_dir / f"{base_filename}.svg"
                if svg_path.exists():
                    return (svg_path, 'svg')
        
        return (None, None)
    
    def assign_placeholder_image(self, product_data):
        """
        Assign appropriate placeholder based on orientation
        Returns image ID to use for product
        """
        if product_data['type'] == 'simple':
            orientation = product_data.get('orientation', '').lower() if product_data.get('orientation') else ''
            
            if 'left' in orientation:
                return self.placeholder_ids.get('left', self.placeholder_ids.get('general'))
            elif 'right' in orientation:
                return self.placeholder_ids.get('right', self.placeholder_ids.get('general'))
        
        return self.placeholder_ids.get('general')

    def _get_media_filename(self, media_id):
        """Return filename for a media ID, caching results. Safe to fail."""
        if not media_id:
            return None
        if not hasattr(self, 'media_cache'):
            self.media_cache = {}
        if media_id in self.media_cache:
            return self.media_cache[media_id]
        try:
            resp = self.wcapi.get(f"wp/v2/media/{media_id}")
            if resp.status_code == 200:
                src = resp.json().get('source_url', '')
                filename = src.split('/')[-1] if src else str(media_id)
                self.media_cache[media_id] = filename
                return filename
        except Exception:
            pass
        self.media_cache[media_id] = str(media_id)
        return str(media_id)

    def _merge_image_ids(self, existing_ids, desired_ids):
        """Merge two lists of media IDs, deduping by media filename when possible."""
        merged = []
        seen = set()
        for mid in (existing_ids or []) + (desired_ids or []):
            if mid in merged:
                continue
            fname = self._get_media_filename(mid) or str(mid)
            key = (fname.lower() if isinstance(fname, str) else str(fname))
            if key in seen:
                continue
            seen.add(key)
            merged.append(mid)
        return merged

    def _merge_meta_dicts(self, existing_meta, incoming_meta):
        """Merge two meta dicts with heuristics for JSON strings, lists and dicts.
        existing_meta/incoming_meta are dicts mapping key->value.
        Returns merged dict.
        """
        merged = existing_meta.copy() if existing_meta else {}
        for k, iv in (incoming_meta or {}).items():
            if k in merged:
                ev = merged[k]
                # Attempt JSON decode for stringified JSON
                try:
                    if isinstance(ev, str) and isinstance(iv, str):
                        evj = json.loads(ev)
                        ivj = json.loads(iv)
                        if isinstance(evj, dict) and isinstance(ivj, dict):
                            mm = evj.copy(); mm.update(ivj); merged[k] = json.dumps(mm, ensure_ascii=False); continue
                        if isinstance(evj, list) and isinstance(ivj, list):
                            merged_list = list(dict.fromkeys(evj + ivj)); merged[k] = json.dumps(merged_list, ensure_ascii=False); continue
                except Exception:
                    pass

                # Dict/list merging
                if isinstance(ev, dict) and isinstance(iv, dict):
                    mm = ev.copy(); mm.update(iv); merged[k] = mm
                elif isinstance(ev, list) and isinstance(iv, list):
                    merged[k] = list(dict.fromkeys(ev + iv))
                else:
                    # Prefer incoming value for simple types
                    merged[k] = iv
            else:
                merged[k] = iv
        return merged

    def _repair_existing_product(self, product_id, incoming_wc_product, desired_category_ids, desired_images_list):
        """Fetch product by ID, merge categories/images/meta/stock from incoming, and PATCH the product.
        Returns True on success.
        """
        try:
            resp = self.wcapi.get(f"products/{product_id}")
            if resp.status_code != 200:
                return False
            prod = resp.json()

            existing_cat_ids = [c['id'] for c in prod.get('categories', [])]
            merged_cat_ids = list(dict.fromkeys(existing_cat_ids + (desired_category_ids or [])))

            existing_image_ids = [i.get('id') for i in prod.get('images', []) if i.get('id')]
            desired_image_ids = [i.get('id') for i in (desired_images_list or []) if i.get('id')]
            merged_image_ids = self._merge_image_ids(existing_image_ids, desired_image_ids)

            existing_meta = {m['key']: m.get('value') for m in prod.get('meta_data', [])}
            incoming_meta = {m['key']: m.get('value') for m in incoming_wc_product.get('meta_data', [])}
            merged_meta = self._merge_meta_dicts(existing_meta, incoming_meta)
            merged_meta_list = [{"key": k, "value": v} for k, v in merged_meta.items()]

            update_data = {}
            if set(merged_cat_ids) != set(existing_cat_ids):
                update_data['categories'] = [{"id": cid} for cid in merged_cat_ids]
            if set(merged_image_ids) != set(existing_image_ids):
                update_data['images'] = [{"id": iid} for iid in merged_image_ids]
            if merged_meta_list:
                update_data['meta_data'] = merged_meta_list

            # No stock/price overrides here — avoid clobbering live inventory unless incoming explicitly sets them
            if update_data:
                r = self.wcapi.put(f"products/{product_id}", update_data)
                return r.status_code in (200, 201)
            return True
        except Exception:
            return False

    def _find_product_by_sku(self, sku, retries=3, per_page=100, backoff=0.5, use_cache=True):
        """Robustly query products by SKU with simple retry/backoff and larger page size."""
        import time
        # initialize cache if needed
        if not hasattr(self, 'sku_lookup_cache'):
            self.sku_lookup_cache = {}

        # Return cached result when available (only when allowed)
        if use_cache and sku in self.sku_lookup_cache:
            return self.sku_lookup_cache[sku]

        results = []

        for attempt in range(retries):
            try:
                # Primary lookup by explicit SKU parameter
                resp = self.wcapi.get('products', params={'sku': sku, 'per_page': per_page})
                if resp.status_code == 200:
                    parsed = resp.json()
                    if isinstance(parsed, list) and parsed:
                        results = parsed
                        break
                    if isinstance(parsed, dict) and parsed:
                        results = [parsed]
                        break

                # Fallback: search endpoint (searches title/content and sometimes SKU)
                resp2 = self.wcapi.get('products', params={'search': sku, 'per_page': per_page})
                if resp2.status_code == 200:
                    parsed2 = resp2.json()
                    # filter any returned items by exact SKU match to be safe
                    if isinstance(parsed2, list):
                        filtered = [p for p in parsed2 if str(p.get('sku', '')).strip().upper() == str(sku).strip().upper()]
                        if filtered:
                            results = filtered
                            break
                        # If no exact sku matches but some items contain sku in fields, accept them as partial hit
                        if parsed2:
                            # but only if nothing else found after retries
                            results = parsed2

                # If we got a non-empty results set, break
                if results:
                    break

            except Exception:
                # ignore transient network errors
                pass

            # log this lookup attempt for visibility
            try:
                dbglog = self.log_dir / 'sku_debug.log'
                with open(dbglog, 'a', encoding='utf-8') as df:
                    df.write(f"{datetime.now().isoformat()} SKU_LOOKUP_ATTEMPT sku={sku} attempt={attempt+1}\n")
            except Exception:
                pass

            time.sleep(backoff * (2 ** attempt))

        # Normalize results to list
        results = results or []

        # Cache positive results only (avoid caching empty misses)
        try:
            if results and len(self.sku_lookup_cache) < 5000:
                self.sku_lookup_cache[sku] = results
        except Exception:
            pass

        return results
    
    def create_simple_product(self, product_data):
        """Create a simple WooCommerce product"""
        sku = product_data['sku']
        
        # Check if already processed
        if sku in self.processed_skus:
            self.stats['skipped'].append(f"Duplicate SKU: {sku}")
            return None
        
        # Build product title with diagram code
        diagram_code = product_data.get('diagram_code', '')
        if diagram_code:
            product_title = f"{diagram_code} - {product_data['name']}"
        else:
            product_title = product_data['name']
        
        # Build product description
        description = f"<p><strong>Part Number:</strong> {sku}</p>"
        if diagram_code:
            description += f"<p><strong>Diagram Code:</strong> {diagram_code}</p>"
        description += f"<p><strong>Callout Number:</strong> {product_data['callout']}</p>"
        description += f"<p><strong>Quantity:</strong> {product_data['quantity']}</p>"
        
        if product_data.get('remark'):
            description += f"<p><strong>Remark:</strong> {product_data['remark']}</p>"
        
        # Get category IDs
        category_ids = self.build_category_hierarchy(product_data['categories'])
        
        # Try to find diagram image (PNG or SVG)
        diagram_path, img_type = self.get_diagram_image_path(product_data)
        images_list = []
        
        if diagram_path:
            # Upload diagram image to WordPress
            try:
                image_data = self.upload_image_to_wordpress(diagram_path)
                if image_data:
                    images_list.append(image_data)
                    self.stats['images_uploaded'] += 1
                    print(f"  ✓ Uploaded {img_type.upper()}: {diagram_path.name}")
            except Exception as e:
                print(f"  ⚠ Failed to upload {img_type.upper()}: {e}")
                # Fall back to placeholder
                placeholder_id = self.assign_placeholder_image(product_data)
                if placeholder_id:
                    images_list.append({"id": placeholder_id})
        else:
            # Use placeholder if no diagram image exists
            placeholder_id = self.assign_placeholder_image(product_data)
            if placeholder_id:
                images_list.append({"id": placeholder_id})
        
        # Build product data
        wc_product = {
            "name": product_title,
            "type": "simple",
            "sku": sku,
            "regular_price": "0.00",  # Placeholder price
            "description": description,
            "short_description": product_data.get('remark', ''),
            "categories": [{"id": cat_id} for cat_id in category_ids],
            "images": images_list,
            "manage_stock": True,
            "stock_quantity": 50,
            "stock_status": "instock",
            "meta_data": [
                {"key": "diagram_code", "value": diagram_code},
                {"key": "callout_number", "value": product_data['callout']},
                {"key": "diagram_file", "value": product_data['diagram_file']},
                {"key": "orientation", "value": product_data.get('orientation', 'N/A')},
                {"key": "quantity_per_vehicle", "value": product_data['quantity']},
                {"key": "remark", "value": product_data.get('remark', '')}
            ]
        }
        
        # Determine desired category IDs for this product (model-specific)
        desired_category_ids = category_ids

        # Robustly try to find existing product by SKU before creating
        existing_list = self._find_product_by_sku(sku, use_cache=False)

        if existing_list:
            product = existing_list[0]
            product_id = product['id']

            # Merge categories
            existing_cat_ids = [c['id'] for c in product.get('categories', [])]
            merged_cat_ids = list(dict.fromkeys(existing_cat_ids + desired_category_ids))

            # Merge images (by media ID using filename dedupe)
            existing_image_ids = [i.get('id') for i in product.get('images', []) if i.get('id')]
            desired_image_ids = [i.get('id') for i in images_list if i.get('id')]
            merged_image_ids = self._merge_image_ids(existing_image_ids, desired_image_ids)

            # Merge meta using heuristics for complex values
            existing_meta = {m['key']: m.get('value') for m in product.get('meta_data', [])}
            incoming_meta = {m['key']: m.get('value') for m in wc_product.get('meta_data', [])}
            merged_meta = self._merge_meta_dicts(existing_meta, incoming_meta)
            merged_meta_list = [{"key": k, "value": v} for k, v in merged_meta.items()]

            # Stock fields: prefer incoming values if present
            stock_updates = {}
            if wc_product.get('manage_stock') is not None:
                stock_updates['manage_stock'] = wc_product.get('manage_stock')
            if wc_product.get('stock_quantity') is not None:
                stock_updates['stock_quantity'] = wc_product.get('stock_quantity')
            if wc_product.get('stock_status'):
                stock_updates['stock_status'] = wc_product.get('stock_status')

            update_data = {}
            if set(merged_cat_ids) != set(existing_cat_ids):
                update_data['categories'] = [{"id": cid} for cid in merged_cat_ids]
            if set(merged_image_ids) != set(existing_image_ids):
                update_data['images'] = [{"id": iid} for iid in merged_image_ids]
            if merged_meta_list:
                update_data['meta_data'] = merged_meta_list
            update_data.update(stock_updates)

            if update_data:
                try:
                    resp = self.wcapi.put(f"products/{product_id}", update_data)
                    if resp.status_code in (200, 201):
                        self.stats['products_updated'] += 1
                        self.processed_skus.add(sku)
                        print(f"  ✓ Updated existing product {sku} (id: {product_id})")
                        return product_id
                    else:
                        self.log_error(f"Failed to update product {sku}: {resp.status_code} - {resp.text}", wc_product)
                        return None
                except Exception as e:
                    self.log_error(f"Error updating product {sku}: {str(e)}", wc_product)
                    return None
            else:
                # Nothing to update
                self.processed_skus.add(sku)
                print(f"  - SKU {sku} already up-to-date (id: {product_id})")
                return product_id

        # PRODUCT DOES NOT EXIST: create it fresh (double-check just before POST)
        existing_list = self._find_product_by_sku(sku, use_cache=False)
        # Debug: log immediate SKU lookup result before attempting POST
        try:
            dbg_found = self._find_product_by_sku(sku, use_cache=False)
            dbg_ids = [p.get('id') for p in dbg_found] if dbg_found else []
            print(f"DEBUG SKU_LOOKUP before POST for {sku}: found_count={len(dbg_found)} ids={dbg_ids}")
            try:
                with open(self.log_dir / 'sku_debug.log', 'a', encoding='utf-8') as df:
                    df.write(f"{datetime.now().isoformat()} SKU_LOOKUP {sku} found_count={len(dbg_found)} ids={dbg_ids}\n")
            except Exception:
                pass
        except Exception:
            pass
        if existing_list:
            # Found after retry—perform merge/update instead of create
            product = existing_list[0]
            product_id = product['id']
            existing_cat_ids = [c['id'] for c in product.get('categories', [])]
            merged_cat_ids = list(dict.fromkeys(existing_cat_ids + desired_category_ids))
            update_data = {'categories': [{'id': cid} for cid in merged_cat_ids]} if set(merged_cat_ids) != set(existing_cat_ids) else {}
            if update_data:
                try:
                    resp = self.wcapi.put(f"products/{product_id}", update_data)
                    if resp.status_code in (200,201):
                        self.stats['products_updated'] += 1
                        self.processed_skus.add(sku)
                        print(f"  ✓ Updated existing product {sku} (id: {product_id}) before create")
                        return product_id
                except Exception as e:
                    self.log_error(f"Error updating product {sku} before create: {str(e)}", wc_product)
            # nothing to update, mark processed
            self.processed_skus.add(sku)
            return product_id

        try:
            # Detailed pre-POST debug: record a fresh GET-by-SKU, the exact POST body, and timing
            start_get = time.time()
            try:
                pre_get_resp = self.wcapi.get('products', params={'sku': sku, 'per_page': 100})
                pre_get_elapsed = time.time() - start_get
            except Exception:
                pre_get_resp = None
                pre_get_elapsed = time.time() - start_get

            try:
                dbg_path = self.log_dir / 'prepost_debug.log'
                with open(dbg_path, 'a', encoding='utf-8') as df:
                    df.write(f"{datetime.now().isoformat()} PREPOST START SKU={sku}\n")
                    if pre_get_resp is not None:
                        try:
                            df.write(f"GET /products?sku={sku} status={pre_get_resp.status_code} time={pre_get_elapsed:.3f}s\n")
                            # write a truncated body to avoid huge logs
                            body_snip = (pre_get_resp.text[:4000] + '...') if len(pre_get_resp.text) > 4000 else pre_get_resp.text
                            df.write(f"GET_BODY:\n{body_snip}\n")
                        except Exception:
                            df.write("GET response could not be serialized\n")
                    else:
                        df.write("GET /products failed (exception)\n")

                    # If the direct GET returned an existing product, merge/update instead of creating
                    try:
                        if pre_get_resp is not None and getattr(pre_get_resp, 'status_code', None) == 200:
                            try:
                                parsed_pre = pre_get_resp.json()
                            except Exception:
                                parsed_pre = None

                            if parsed_pre:
                                # Normalize
                                existing_product = parsed_pre[0] if isinstance(parsed_pre, list) else parsed_pre
                                product_id = existing_product.get('id')
                                if product_id:
                                    # Merge categories/images/meta similar to earlier logic
                                    existing_cat_ids = [c['id'] for c in existing_product.get('categories', [])]
                                    merged_cat_ids = list(dict.fromkeys(existing_cat_ids + desired_category_ids))

                                    existing_image_ids = [i.get('id') for i in existing_product.get('images', []) if i.get('id')]
                                    desired_image_ids = [i.get('id') for i in images_list if i.get('id')]
                                    merged_image_ids = self._merge_image_ids(existing_image_ids, desired_image_ids)

                                    existing_meta = {m['key']: m.get('value') for m in existing_product.get('meta_data', [])}
                                    incoming_meta = {m['key']: m.get('value') for m in wc_product.get('meta_data', [])}
                                    merged_meta = self._merge_meta_dicts(existing_meta, incoming_meta)
                                    merged_meta_list = [{"key": k, "value": v} for k, v in merged_meta.items()]

                                    update_data = {}
                                    if set(merged_cat_ids) != set(existing_cat_ids):
                                        update_data['categories'] = [{"id": cid} for cid in merged_cat_ids]
                                    if set(merged_image_ids) != set(existing_image_ids):
                                        update_data['images'] = [{"id": iid} for iid in merged_image_ids]
                                    if merged_meta_list:
                                        update_data['meta_data'] = merged_meta_list

                                    if update_data:
                                        try:
                                            resp = self.wcapi.put(f"products/{product_id}", update_data)
                                            if resp.status_code in (200, 201):
                                                self.stats['products_updated'] += 1
                                                self.processed_skus.add(sku)
                                                print(f"  ✓ Updated existing product {sku} (id: {product_id}) [pre-GET merge]")
                                                return product_id
                                        except Exception:
                                            pass
                                    else:
                                        # nothing to update; mark processed
                                        self.processed_skus.add(sku)
                                        print(f"  - SKU {sku} already up-to-date (id: {product_id}) [pre-GET]")
                                        return product_id
                    except Exception:
                        pass

                    df.write("POST /products BODY:\n")
                    try:
                        df.write(json.dumps(wc_product, ensure_ascii=False, indent=2) + "\n")
                    except Exception:
                        df.write(repr(wc_product) + "\n")
            except Exception:
                pass

            post_start = time.time()
            response = self.wcapi.post("products", wc_product)
            post_elapsed = time.time() - post_start

            # Log the POST result (status and truncated body)
            try:
                dbg_path = self.log_dir / 'prepost_debug.log'
                with open(dbg_path, 'a', encoding='utf-8') as df:
                    df.write(f"POST /products status={getattr(response, 'status_code', 'ERR')} time={post_elapsed:.3f}s\n")
                    try:
                        rtext = response.text if hasattr(response, 'text') else str(response)
                        r_snip = (rtext[:4000] + '...') if len(rtext) > 4000 else rtext
                        df.write(f"POST_BODY:\n{r_snip}\n")
                    except Exception:
                        df.write("POST response could not be serialized\n")
                    df.write(f"PREPOST END SKU={sku}\n\n")
            except Exception:
                pass

            if response.status_code == 201:
                self.processed_skus.add(sku)
                self.stats['products_created'] += 1
                return response.json()['id']
            else:
                # If WooCommerce reports invalid/duplicated SKU, attempt safe repair by PATCHing
                try:
                    body = response.json()
                except Exception:
                    body = None

                if body and body.get('code') == 'product_invalid_sku':
                    resource_id = body.get('data', {}).get('resource_id')
                    if resource_id:
                        # Attempt to merge categories/images/meta into existing product
                        repaired = self._repair_existing_product(resource_id, wc_product, category_ids, images_list)
                        if repaired:
                            self.stats['products_updated'] += 1
                            self.processed_skus.add(sku)
                            return resource_id
                        else:
                            # Even if repair failed, mark processed to avoid repeated POSTs
                            self.processed_skus.add(sku)
                            self.log_error(f"Could not repair existing product {resource_id} for SKU {sku}; marking SKU processed to avoid retries.", wc_product)
                            return resource_id

                error_msg = f"Failed to create product {sku}: {response.status_code} - {response.text}"
                # log product details for debugging
                self.log_error(error_msg, wc_product)
                # mark processed to avoid retry storms
                self.processed_skus.add(sku)
                return None

        except Exception as e:
            error_msg = f"Error creating product {sku}: {str(e)}"
            self.log_error(error_msg, wc_product)
            return None
    
    def create_variable_product(self, product_data):
        """Create a variable WooCommerce product with variations"""
        # Get category IDs
        category_ids = self.build_category_hierarchy(product_data['categories'])
        
        # Build product title with diagram code
        diagram_code = product_data.get('diagram_code', '')
        if diagram_code:
            product_title = f"{diagram_code} - {product_data['name']}"
        else:
            product_title = product_data['name']
        
        # Build description
        description = ""
        if diagram_code:
            description += f"<p><strong>Diagram Code:</strong> {diagram_code}</p>"
        description += f"<p><strong>Callout Number:</strong> {product_data['callout']}</p>"
        description += f"<p>This product has {len(product_data['variations'])} variations.</p>"
        
        # Try to find diagram image (PNG or SVG)
        diagram_path, img_type = self.get_diagram_image_path(product_data)
        images_list = []
        
        if diagram_path:
            # Upload diagram image to WordPress
            try:
                image_data = self.upload_image_to_wordpress(diagram_path)
                if image_data:
                    images_list.append(image_data)
                    self.stats['images_uploaded'] += 1
                    print(f"  ✓ Prepared {img_type.upper()}: {diagram_path.name}")
            except Exception as e:
                print(f"  ⚠ Failed to prepare {img_type.upper()}: {e}")
                # Fall back to placeholder
                placeholder_id = self.placeholder_ids.get('general')
                if placeholder_id:
                    images_list.append({"id": placeholder_id})
        else:
            # Use placeholder if no diagram image exists
            placeholder_id = self.placeholder_ids.get('general')
            if placeholder_id:
                images_list.append({"id": placeholder_id})
        
        # Build parent product
        wc_product = {
            "name": product_title,
            "type": "variable",
            "description": description,
            "categories": [{"id": cat_id} for cat_id in category_ids],
            "images": images_list,
            "attributes": [
                {
                    "name": "Orientation",
                    "visible": True,
                    "variation": True,
                    "options": [v['orientation'] for v in product_data['variations'] if v['orientation']]
                }
            ],
            "meta_data": [
                {"key": "diagram_code", "value": diagram_code},
                {"key": "callout_number", "value": product_data['callout']},
                {"key": "diagram_file", "value": product_data['diagram_file']}
            ]
        }
        
        try:
            # Try to find an existing variable parent by title and diagram_code
            parent_id = None
            try:
                search_resp = self.wcapi.get("products", params={"search": product_title, "type": "variable", "per_page": 100})
                if search_resp.status_code == 200:
                    for p in search_resp.json():
                        # match by meta diagram_code when available
                        metas = {m['key']: m.get('value') for m in p.get('meta_data', [])}
                        if metas.get('diagram_code') == diagram_code:
                            parent_id = p['id']
                            product = p
                            break
            except Exception:
                parent_id = None

            if parent_id:
                # Merge parent categories/images/meta similar to simple product
                existing_cat_ids = [c['id'] for c in product.get('categories', [])]
                merged_cat_ids = list(dict.fromkeys(existing_cat_ids + category_ids))

                existing_image_ids = [i.get('id') for i in product.get('images', []) if i.get('id')]
                desired_image_ids = [i.get('id') for i in images_list if i.get('id')]
                merged_image_ids = self._merge_image_ids(existing_image_ids, desired_image_ids)

                existing_meta = {m['key']: m.get('value') for m in product.get('meta_data', [])}
                incoming_meta = {m['key']: m.get('value') for m in wc_product.get('meta_data', [])}
                merged_meta = self._merge_meta_dicts(existing_meta, incoming_meta)
                merged_meta_list = [{"key": k, "value": v} for k, v in merged_meta.items()]

                update_data = {}
                if set(merged_cat_ids) != set(existing_cat_ids):
                    update_data['categories'] = [{"id": cid} for cid in merged_cat_ids]
                if set(merged_image_ids) != set(existing_image_ids):
                    update_data['images'] = [{"id": iid} for iid in merged_image_ids]
                if merged_meta_list:
                    update_data['meta_data'] = merged_meta_list

                if update_data:
                    try:
                        resp = self.wcapi.put(f"products/{parent_id}", update_data)
                        if resp.status_code in (200, 201):
                            self.stats['products_updated'] += 1
                            print(f"  ✓ Updated existing variable parent (id: {parent_id})")
                        else:
                            self.log_error(f"Failed to update variable parent {parent_id}: {resp.status_code} - {resp.text}", wc_product)
                    except Exception as e:
                        self.log_error(f"Error updating variable parent {parent_id}: {str(e)}", wc_product)
            else:
                # Debug: log parent lookup before creating variable parent
                try:
                    p_dbg = self._find_product_by_sku(product_title)
                    # product_title search via sku finder will likely return [], but log for visibility
                    print(f"DEBUG PARENT_LOOKUP before POST for parent title '{product_title}': found_count={len(p_dbg)}")
                    try:
                        with open(self.log_dir / 'sku_debug.log', 'a', encoding='utf-8') as df:
                            df.write(f"{datetime.now().isoformat()} PARENT_LOOKUP {product_title} found_count={len(p_dbg)}\n")
                    except Exception:
                        pass
                except Exception:
                    pass

                # Create parent product with pre/post debug logging
                try:
                    pre_get_resp = None
                    get_start = time.time()
                    try:
                        pre_get_resp = self.wcapi.get('products', params={'search': product_title, 'type': 'variable', 'per_page': 100})
                        get_elapsed = time.time() - get_start
                    except Exception:
                        pre_get_resp = None
                        get_elapsed = time.time() - get_start

                    try:
                        dbg_path = self.log_dir / 'prepost_debug.log'
                        with open(dbg_path, 'a', encoding='utf-8') as df:
                            df.write(f"{datetime.now().isoformat()} PREPOST START PARENT title={product_title}\n")
                            if pre_get_resp is not None:
                                df.write(f"GET /products?search={product_title} status={pre_get_resp.status_code} time={get_elapsed:.3f}s\n")
                                body_snip = (pre_get_resp.text[:4000] + '...') if len(pre_get_resp.text) > 4000 else pre_get_resp.text
                                df.write(f"GET_BODY:\n{body_snip}\n")
                            df.write("POST /products BODY:\n")
                            try:
                                df.write(json.dumps(wc_product, ensure_ascii=False, indent=2) + "\n")
                            except Exception:
                                df.write(repr(wc_product) + "\n")
                    except Exception:
                        pass

                    post_start = time.time()
                    response = self.wcapi.post("products", wc_product)
                    post_elapsed = time.time() - post_start

                    try:
                        dbg_path = self.log_dir / 'prepost_debug.log'
                        with open(dbg_path, 'a', encoding='utf-8') as df:
                            df.write(f"POST /products status={getattr(response, 'status_code', 'ERR')} time={post_elapsed:.3f}s\n")
                            rtext = response.text if hasattr(response, 'text') else str(response)
                            r_snip = (rtext[:4000] + '...') if len(rtext) > 4000 else rtext
                            df.write(f"POST_BODY:\n{r_snip}\n")
                            df.write(f"PREPOST END PARENT title={product_title}\n\n")
                    except Exception:
                        pass

                    if response.status_code != 201:
                        error_msg = f"Failed to create variable product {product_data['name']}: {response.status_code}"
                        self.log_error(error_msg, wc_product)
                        return None
                    parent_id = response.json()['id']
                    self.stats['products_created'] += 1
                except Exception as e:
                    self.log_error(f"Exception creating variable parent {product_title}: {str(e)}", wc_product)
                    return None

            # Create or update variations
            for variation in product_data['variations']:
                sku = variation['sku']

                # Prepare variation payload
                var_image_id = self.placeholder_ids.get('left') if 'left' in (variation.get('orientation') or '').lower() \
                    else self.placeholder_ids.get('right') if 'right' in (variation.get('orientation') or '').lower() \
                    else self.placeholder_ids.get('general')

                variation_data = {
                    "sku": sku,
                    "regular_price": "0.00",
                    "manage_stock": True,
                    "stock_quantity": variation.get('quantity', 0),
                    "stock_status": "instock",
                    "attributes": [
                        {"name": "Orientation", "option": variation.get('orientation')}
                    ],
                    "image": {"id": var_image_id} if var_image_id else None,
                    "meta_data": [
                        {"key": "quantity_per_vehicle", "value": variation.get('quantity')},
                        {"key": "remark", "value": variation.get('remark')}
                    ]
                }

                # Check if SKU exists anywhere
                try:
                    sku_resp = self.wcapi.get("products", params={"sku": sku})
                    sku_list = sku_resp.json() if sku_resp.status_code == 200 else []
                except Exception:
                    sku_list = []

                if sku_list:
                    existing_prod = sku_list[0]
                    existing_prod_id = existing_prod['id']

                    if existing_prod_id == parent_id:
                        # The SKU is already assigned under this parent — find variation id and update
                        try:
                            vars_resp = self.wcapi.get(f"products/{parent_id}/variations", params={"per_page": 100})
                            if vars_resp.status_code == 200:
                                var_id = None
                                for v in vars_resp.json():
                                    if v.get('sku') == sku:
                                        var_id = v['id']
                                        break
                                if var_id:
                                    resp = self.wcapi.put(f"products/{parent_id}/variations/{var_id}", variation_data)
                                    if resp.status_code in (200, 201):
                                        self.processed_skus.add(sku)
                                        self.stats['variations_created'] += 1
                                    else:
                                        self.log_error(f"Failed to update variation {sku}: {resp.status_code} - {resp.text}", {'parent_id': parent_id, 'variation': variation})
                                else:
                                    # Create variation under parent (pre/post debug)
                                    try:
                                        v_get_start = time.time()
                                        try:
                                            v_pre_get = self.wcapi.get('products', params={'sku': sku, 'per_page': 100})
                                            v_get_elapsed = time.time() - v_get_start
                                        except Exception:
                                            v_pre_get = None
                                            v_get_elapsed = time.time() - v_get_start

                                        try:
                                            dbg_path = self.log_dir / 'prepost_debug.log'
                                            with open(dbg_path, 'a', encoding='utf-8') as df:
                                                df.write(f"{datetime.now().isoformat()} PREPOST START VAR_CREATE sku={sku} parent={parent_id}\n")
                                                if v_pre_get is not None:
                                                    df.write(f"GET /products?sku={sku} status={v_pre_get.status_code} time={v_get_elapsed:.3f}s\n")
                                                    b = (v_pre_get.text[:4000] + '...') if len(v_pre_get.text) > 4000 else v_pre_get.text
                                                    df.write(f"GET_BODY:\n{b}\n")
                                                df.write("POST /products/{parent_id}/variations BODY:\n")
                                                try:
                                                    df.write(json.dumps(variation_data, ensure_ascii=False, indent=2) + "\n")
                                                except Exception:
                                                    df.write(repr(variation_data) + "\n")
                                        except Exception:
                                            pass

                                        v_post_start = time.time()
                                        var_create = self.wcapi.post(f"products/{parent_id}/variations", variation_data)
                                        v_post_elapsed = time.time() - v_post_start

                                        try:
                                            dbg_path = self.log_dir / 'prepost_debug.log'
                                            with open(dbg_path, 'a', encoding='utf-8') as df:
                                                df.write(f"POST /products/{parent_id}/variations status={getattr(var_create, 'status_code', 'ERR')} time={v_post_elapsed:.3f}s\n")
                                                try:
                                                    vt = var_create.text if hasattr(var_create, 'text') else str(var_create)
                                                    vts = (vt[:4000] + '...') if len(vt) > 4000 else vt
                                                    df.write(f"POST_BODY:\n{vts}\n")
                                                except Exception:
                                                    df.write("POST response could not be serialized\n")
                                                df.write(f"PREPOST END VAR_CREATE sku={sku} parent={parent_id}\n\n")
                                        except Exception:
                                            pass

                                        if var_create.status_code == 201:
                                            self.processed_skus.add(sku)
                                            self.stats['variations_created'] += 1
                                        else:
                                            self.log_error(f"Failed to create variation {sku}: {var_create.status_code} - {var_create.text}", {'parent_id': parent_id, 'variation': variation})
                                    except Exception as e:
                                        self.log_error(f"Exception creating variation {sku} under parent {parent_id}: {str(e)}", {'parent_id': parent_id, 'variation': variation})
                        except Exception as e:
                            self.log_error(f"Error handling variation {sku} for parent {parent_id}: {str(e)}", {'parent_id': parent_id, 'variation': variation})
                    else:
                        # SKU exists on different product — add this model's category to that product
                        try:
                            existing_cats = [c['id'] for c in existing_prod.get('categories', [])]
                            merged = list(dict.fromkeys(existing_cats + category_ids))
                            if set(merged) != set(existing_cats):
                                upd = {"categories": [{"id": cid} for cid in merged]}
                                resp = self.wcapi.put(f"products/{existing_prod_id}", upd)
                                if resp.status_code in (200, 201):
                                    print(f"  ✓ Added model category to existing SKU {sku} (product id: {existing_prod_id})")
                                    self.processed_skus.add(sku)
                                else:
                                    self.log_error(f"Failed to add category to existing SKU {sku}: {resp.status_code} - {resp.text}", {'sku': sku, 'target_cats': category_ids})
                        except Exception as e:
                            self.log_error(f"Error updating existing SKU {sku}: {str(e)}", {'sku': sku})
                else:
                    # SKU not present anywhere — create variation under parent
                    try:
                        # Pre/post debug for variation create when SKU not present anywhere
                        v_get_start = time.time()
                        try:
                            v_pre_get = self.wcapi.get('products', params={'sku': sku, 'per_page': 100})
                            v_get_elapsed = time.time() - v_get_start
                        except Exception:
                            v_pre_get = None
                            v_get_elapsed = time.time() - v_get_start

                        try:
                            dbg_path = self.log_dir / 'prepost_debug.log'
                            with open(dbg_path, 'a', encoding='utf-8') as df:
                                df.write(f"{datetime.now().isoformat()} PREPOST START VAR_CREATE sku={sku} parent={parent_id}\n")
                                if v_pre_get is not None:
                                    df.write(f"GET /products?sku={sku} status={v_pre_get.status_code} time={v_get_elapsed:.3f}s\n")
                                    b = (v_pre_get.text[:4000] + '...') if len(v_pre_get.text) > 4000 else v_pre_get.text
                                    df.write(f"GET_BODY:\n{b}\n")
                                df.write("POST /products/{parent_id}/variations BODY:\n")
                                try:
                                    df.write(json.dumps(variation_data, ensure_ascii=False, indent=2) + "\n")
                                except Exception:
                                    df.write(repr(variation_data) + "\n")
                        except Exception:
                            pass

                        v_post_start = time.time()
                        var_create = self.wcapi.post(f"products/{parent_id}/variations", variation_data)
                        v_post_elapsed = time.time() - v_post_start

                        try:
                            dbg_path = self.log_dir / 'prepost_debug.log'
                            with open(dbg_path, 'a', encoding='utf-8') as df:
                                df.write(f"POST /products/{parent_id}/variations status={getattr(var_create, 'status_code', 'ERR')} time={v_post_elapsed:.3f}s\n")
                                try:
                                    vt = var_create.text if hasattr(var_create, 'text') else str(var_create)
                                    vts = (vt[:4000] + '...') if len(vt) > 4000 else vt
                                    df.write(f"POST_BODY:\n{vts}\n")
                                except Exception:
                                    df.write("POST response could not be serialized\n")
                                df.write(f"PREPOST END VAR_CREATE sku={sku} parent={parent_id}\n\n")
                        except Exception:
                            pass

                        if var_create.status_code == 201:
                            self.processed_skus.add(sku)
                            self.stats['variations_created'] += 1
                        else:
                            # Debug: immediate SKU lookup before handling create failure
                            try:
                                v_dbg = self._find_product_by_sku(sku, use_cache=False)
                                v_ids = [p.get('id') for p in v_dbg] if v_dbg else []
                                print(f"DEBUG VAR_SKU_LOOKUP after failed variation POST for {sku}: found_count={len(v_dbg)} ids={v_ids}")
                                try:
                                    with open(self.log_dir / 'sku_debug.log', 'a', encoding='utf-8') as df:
                                        df.write(f"{datetime.now().isoformat()} VAR_SKU_LOOKUP {sku} found_count={len(v_dbg)} ids={v_ids}\n")
                                except Exception:
                                    pass
                            except Exception:
                                pass
                            # Attempt repair if WooCommerce signals duplicate SKU pointing to existing product
                            try:
                                vbody = var_create.json()
                            except Exception:
                                vbody = None

                            repaired = False

                            if vbody and vbody.get('code') == 'product_invalid_sku':
                                resource_id = vbody.get('data', {}).get('resource_id')
                                if resource_id:
                                    # Add this model's categories to that existing product
                                    try:
                                        existing_resp = self.wcapi.get(f"products/{resource_id}")
                                        if existing_resp.status_code == 200:
                                            existing_prod = existing_resp.json()
                                            existing_cats = [c['id'] for c in existing_prod.get('categories', [])]
                                            merged = list(dict.fromkeys(existing_cats + category_ids))
                                            if set(merged) != set(existing_cats):
                                                upd = {"categories": [{"id": cid} for cid in merged]}
                                                resp = self.wcapi.put(f"products/{resource_id}", upd)
                                                if resp.status_code in (200,201):
                                                    self.processed_skus.add(sku)
                                                    print(f"  ✓ Added model category to existing SKU {sku} (product id: {resource_id})")
                                                    repaired = True
                                    except Exception as e:
                                        self.log_error(f"Error repairing existing SKU {sku}: {str(e)}")

                            # If not repaired yet, try a final SKU search and (if found) update that product
                            if not repaired:
                                fallback = self._find_product_by_sku(sku, use_cache=False)
                                if fallback:
                                    fid = fallback[0]['id']
                                    try:
                                        existing_prod = fallback[0]
                                        existing_cats = [c['id'] for c in existing_prod.get('categories', [])]
                                        merged = list(dict.fromkeys(existing_cats + category_ids))
                                        if set(merged) != set(existing_cats):
                                            upd = {"categories": [{"id": cid} for cid in merged]}
                                            resp = self.wcapi.put(f"products/{fid}", upd)
                                            if resp.status_code in (200,201):
                                                self.processed_skus.add(sku)
                                                print(f"  ✓ Added model category to existing SKU {sku} (product id: {fid}) [fallback]")
                                                repaired = True
                                    except Exception as e:
                                        self.log_error(f"Fallback repair error for SKU {sku}: {str(e)}")

                            if not repaired:
                                self.log_error(f"Failed to create variation {sku}: {var_create.status_code} - {var_create.text}", {'parent_id': parent_id, 'variation': variation})
                                # Mark SKU as processed to avoid retrying repeatedly
                                self.processed_skus.add(sku)
                    except Exception as e:
                        self.log_error(f"Error creating variation {sku}: {str(e)}", {'parent_id': parent_id, 'variation': variation})

            return parent_id

        except Exception as e:
            error_msg = f"Error creating variable product {product_data['name']}: {str(e)}"
            self.log_error(error_msg)
            return None
    
    def import_products(self, products_data, test_mode=False):
        """
        Import products from extracted data
        
        Args:
            products_data: List of product dictionaries
            test_mode: If True, ask for confirmation after each product
        """
        print(f"\n{'='*60}")
        print(f"Importing {len(products_data)} products to WooCommerce")
        print(f"{'='*60}\n")
        
        skipped_count = 0
        
        for product in tqdm(products_data, desc="Importing products"):
            # Skip if already processed
            if product['sku'] in self.processed_skus:
                skipped_count += 1
                continue
            
            if product['type'] == 'simple':
                self.create_simple_product(product)
            elif product['type'] == 'variable':
                self.create_variable_product(product)
            
            # Save checkpoint every 10 products
            if len(self.processed_skus) % 10 == 0:
                self.save_checkpoint()
            
            # Rate limiting (WooCommerce API: ~60 requests/minute)
            time.sleep(0.5)
        
        if skipped_count > 0:
            print(f"\n✓ Skipped {skipped_count} already imported products")
        
        self.stats['end_time'] = datetime.now().isoformat()
    
    def save_checkpoint(self, filename='import_checkpoint.json'):
        """Save import progress for resumability"""
        checkpoint_path = self.checkpoint_dir / filename
        
        checkpoint_data = {
            'processed_skus': list(self.processed_skus),
            'stats': self.stats,
            'category_cache': self.category_cache,
            'placeholder_ids': self.placeholder_ids
        }
        
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        return checkpoint_path
    
    def print_summary(self):
        """Print import summary"""
        print(f"\n{'='*60}")
        print("Import Summary")
        print(f"{'='*60}")
        print(f"Products created:        {self.stats['products_created']}")
        print(f"Variations created:      {self.stats['variations_created']}")
        print(f"Categories created:      {self.stats['categories_created']}")
        print(f"Images uploaded:         {self.stats['images_uploaded']}")
        print(f"Skipped (duplicates):    {len(self.stats['skipped'])}")
        print(f"Errors:                  {len(self.stats['errors'])}")
        print(f"{'='*60}\n")
        
        if self.stats['errors']:
            print("\n⚠ Errors encountered:")
            for error in self.stats['errors'][:10]:
                print(f"  - {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more")
            print(f"\n📄 Full error log: {self.error_log_path}")
        
        if self.stats['skipped']:
            print(f"\n⚠ Skipped {len(self.stats['skipped'])} items (see logs for details)")


def main():
    """Main import function. Supports multiple source folders or data files.

    Usage:
      python import_to_woocommerce.py                # uses default data file
      python import_to_woocommerce.py --source path  # single folder or JSON file
      python import_to_woocommerce.py --source a b c  # multiple sources
    """
    import argparse
    base_dir = Path(__file__).parent.parent

    parser = argparse.ArgumentParser()
    parser.add_argument('--source', '-s', nargs='*', help='Source folder(s) or JSON file(s) to import')
    args = parser.parse_args()

    # Load keys
    keys_file = base_dir / 'keys.txt'
    with open(keys_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
        consumer_key = None
        consumer_secret = None
        for i, line in enumerate(lines):
            if 'Consumer key' in line and i + 1 < len(lines):
                consumer_key = lines[i + 1]
            elif 'Consumer secret' in line and i + 1 < len(lines):
                consumer_secret = lines[i + 1]

    # Load WordPress credentials from productioncreds.txt
    creds_file = base_dir / 'productioncreds.txt'
    wp_username = None
    wp_password = None
    if creds_file.exists():
        with open(creds_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            if len(lines) >= 6:
                wp_username = lines[3]
                wp_password = lines[5]

    # Load config
    import sys
    sys.path.insert(0, str(base_dir))
    from config import WORDPRESS_URL
    wp_url = WORDPRESS_URL

    log_dir = base_dir / 'logs'
    placeholder_dir = base_dir / 'images' / 'placeholders'

    # Determine sources
    sources = args.source if args.source else []
    if not sources:
        # default existing behavior
        default_file = base_dir / 'data' / 'extracted' / 'extracted_data_full.json'
        sources = [str(default_file)]

    print("\n" + "="*60)
    print("WooCommerce EPC Import - Phase 3")
    print("="*60)
    print(f"\nWordPress URL: {wp_url}")

    for src in sources:
        src_path = Path(src)
        # If src is a folder, try to find the extracted JSON inside it
        if src_path.is_dir():
            data_file = src_path / 'data' / 'extracted' / 'extracted_data_full.json'
            # fallback to extracted_data_full.json in folder root
            if not data_file.exists():
                data_file = src_path / 'extracted_data_full.json'
        else:
            data_file = src_path

        if not data_file.exists():
            print(f"⚠ Data file not found for source '{src}': looked for {data_file}")
            continue

        # Use a per-source checkpoint directory when possible
        checkpoint_dir = data_file.parent.parent / 'checkpoints' if (data_file.parent.parent).exists() else base_dir / 'data' / 'checkpoints'
        checkpoint_dir = checkpoint_dir if checkpoint_dir.exists() else base_dir / 'data' / 'checkpoints'

        print(f"\nProcessing source: {data_file}")

        # Create importer for this source (so checkpoints/logs are kept per run)
        importer = WooCommerceImporter(wp_url, consumer_key, consumer_secret, checkpoint_dir, log_dir, wp_username, wp_password)

        # Test connection
        if not importer.test_connection():
            print("\n✗ Cannot proceed - API connection failed")
            return

        # Upload placeholders (only once but safe to call)
        importer.upload_placeholder_images(placeholder_dir)

        if not importer.placeholder_ids:
            print("\n⚠ No placeholder images uploaded - continuing without images")

        # Load extracted data
        with open(data_file, 'r', encoding='utf-8') as f:
            extracted_data = json.load(f)

        print(f"\n✓ Loaded {len(extracted_data.get('products', []))} products from {data_file}")

        # Import products
        importer.import_products(extracted_data.get('products', []))

        # Save checkpoint
        checkpoint_path = importer.save_checkpoint()
        print(f"\n✓ Checkpoint saved to: {checkpoint_path}")

        # Print summary
        importer.print_summary()

    print("\nAll sources processed.")


if __name__ == "__main__":
    main()
