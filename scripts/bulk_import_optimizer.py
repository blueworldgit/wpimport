#!/usr/bin/env python3
"""
Bulk Import Optimizer
High-performance import from Oscar to WooCommerce using batch processing and async concurrency
"""
import asyncio
import aiohttp
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import json
from pathlib import Path
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from tqdm import tqdm
import base64

# Add parent directory to path for imports
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))
from config import WORDPRESS_URL

# Database connection parameters
DB_CONFIG = {
    'dbname': 'parts_store',
    'user': 'postgres',
    'password': 'N0rwich!',
    'host': '80.95.207.42',
    'port': '5432'
}

class BulkImportOptimizer:
    def __init__(self, batch_size=50, concurrent_requests=10):
        # Set base directory
        self.base_dir = Path(__file__).resolve().parent.parent
        
        self.batch_size = batch_size  # WooCommerce batch API can handle 100 items
        self.concurrent_requests = concurrent_requests
        self.processed_skus = set()
        self.category_cache = {}
        self.stats = {
            'products_created': 0,
            'products_updated': 0,
            'products_skipped': 0,
            'errors': 0,
            'start_time': datetime.now().isoformat()
        }
        
        # Enhanced logging and tracking
        self.checkpoint_dir = self.base_dir / 'data' / 'checkpoints'
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir = self.base_dir / 'logs'
        self.log_dir.mkdir(exist_ok=True)
        
        # Create detailed log files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.import_log = self.log_dir / f'bulk_import_{timestamp}.log'
        self.progress_log = self.log_dir / f'bulk_progress_{timestamp}.json'
        self.error_log = self.log_dir / f'bulk_errors_{timestamp}.log'
        
        # Load credentials
        self.load_credentials()
        
        # Load previous checkpoint if exists
        self.load_checkpoint()
    
    def load_credentials(self):
        """Load WooCommerce and WordPress credentials"""
        keys_file = self.base_dir / 'keys.txt'
        if not keys_file.exists():
            raise FileNotFoundError("keys.txt not found")
        
        with open(keys_file, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
            
        for i, line in enumerate(lines):
            if 'Consumer key' in line and i+1 < len(lines): 
                self.consumer_key = lines[i+1]
            if 'Consumer secret' in line and i+1 < len(lines): 
                self.consumer_secret = lines[i+1]
        
        # WordPress credentials
        creds_file = self.base_dir / 'productioncreds.txt'
        if creds_file.exists():
            with open(creds_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                self.wp_username = lines[0].strip()
                self.wp_app_password = lines[1].strip()

    def log_message(self, message, level="INFO"):
        """Log messages to file and console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        
        # Write to log file
        with open(self.import_log, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
        
        # Print to console for important messages
        if level in ["INFO", "ERROR", "SUCCESS"]:
            print(message)
    
    def log_error(self, error_message, batch_data=None):
        """Log errors with detailed context"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(self.error_log, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] ERROR: {error_message}\n")
            if batch_data:
                f.write(f"Batch data: {json.dumps(batch_data, indent=2)}\n")
            f.write("-" * 80 + "\n")
    
    def save_checkpoint(self, completed_products=None):
        """Save progress checkpoint for resumability"""
        checkpoint_data = {
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'processed_skus': list(self.processed_skus),
            'category_cache': self.category_cache,
            'completed_products': completed_products or []
        }
        
        checkpoint_file = self.checkpoint_dir / 'bulk_import_checkpoint.json'
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        # Also save progress log
        with open(self.progress_log, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        self.log_message(f"Checkpoint saved: {len(self.processed_skus)} SKUs processed")
    
    def load_checkpoint(self):
        """Load previous checkpoint to resume import"""
        checkpoint_file = self.checkpoint_dir / 'bulk_import_checkpoint.json'
        
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    checkpoint_data = json.load(f)
                
                self.processed_skus = set(checkpoint_data.get('processed_skus', []))
                self.stats.update(checkpoint_data.get('stats', {}))
                self.category_cache.update(checkpoint_data.get('category_cache', {}))
                
                self.log_message(f"Checkpoint loaded: {len(self.processed_skus)} SKUs already processed")
                return True
                
            except Exception as e:
                self.log_message(f"Failed to load checkpoint: {e}", "ERROR")
        
        return False
    
    def normalize_category_name(self, name):
        """Normalize category name for matching (same logic as fast_create_categories.py)"""
        if not name:
            return ""
        
        import re
        
        # Remove diagram codes (JE123A001 - ) from category names  
        name = re.sub(r'^[A-Z]{2}\d+[A-Z]?\d+\s*-\s*', '', name)
        
        # Replace problematic characters but keep full length
        sanitized = name.replace('&', 'and').replace('/', '-').replace('\\', '-')
        sanitized = sanitized.replace('(', '').replace(')', '').replace(',', '')
        
        # Clean up extra spaces and dashes
        sanitized = re.sub(r'\s+', ' ', sanitized)
        sanitized = re.sub(r'-+', '-', sanitized)
        
        return sanitized.strip(' -').lower()

    def find_category_id(self, category_name):
        """Find category ID with smart search logic"""
        if not category_name:
            return None
        
        # First try exact match
        if category_name in self.category_cache:
            return self.category_cache[category_name]
        
        # Try normalized matching
        normalized_search = self.normalize_category_name(category_name)
        
        for cached_name, cat_ids in self.category_cache.items():
            if self.normalize_category_name(cached_name) == normalized_search:
                self.log_message(f"   📍 Matched '{category_name}' -> '{cached_name}'")
                # Handle multiple IDs
                if isinstance(cat_ids, list):
                    return cat_ids[0]
                else:
                    return cat_ids
        
        # Check if it's a diagram code (starts with letters + numbers)
        import re
        if re.match(r'^[A-Z]+\d+[A-Z]*\d*', category_name):
            # Try partial matching for diagram codes
            for cached_name, cat_ids in self.category_cache.items():
                if category_name.split(' - ')[0].strip() in cached_name:
                    self.log_message(f"   📍 Diagram match '{category_name}' -> '{cached_name}'")
                    if isinstance(cat_ids, list):
                        return cat_ids[0]
                    else:
                        return cat_ids
            
            # For diagram codes, try the base code without description
            base_code = category_name.split(' - ')[0].strip()
            for cached_name, cat_ids in self.category_cache.items():
                if base_code in cached_name:
                    self.log_message(f"   📍 Diagram code match '{base_code}' -> '{cached_name}'")
                    if isinstance(cat_ids, list):
                        return cat_ids[0]
                    else:
                        return cat_ids
        
        return None
    
    def get_all_serials(self):
        """Get list of all vehicle serials for processing"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
            SELECT DISTINCT sn.serial, sn.vehicle_brand,
                   COUNT(DISTINCT p.part_number) as unique_skus,
                   COUNT(p.id) as total_parts
            FROM motorpartsdata_serialnumber sn
            JOIN motorpartsdata_parenttitle pt ON sn.id = pt.serial_number_id
            JOIN motorpartsdata_childtitle ct ON pt.id = ct.parent_id
            JOIN motorpartsdata_part p ON ct.id = p.child_title_id
            GROUP BY sn.serial, sn.vehicle_brand
            ORDER BY unique_skus DESC, sn.serial
            """
            
            cursor.execute(query)
            serials = cursor.fetchall()
            
            cursor.close()
            conn.close()
            return serials
            
        except Exception as e:
            self.log_message(f"❌ Failed to get serials: {e}", "ERROR")
            return []

    def extract_unique_skus(self, serial_filter=None, limit=None):
        """Extract unique SKUs from Oscar database optimized for bulk import"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            self.log_message(f"🔍 Extracting unique SKUs from serial: {serial_filter}")
            
            # Build optimized query for single serial
            where_conditions = []
            params = []
            
            if serial_filter:
                where_conditions.append("sn.serial = %s")
                params.append(serial_filter)
            
            # Exclude already processed SKUs from database query
            # NOTE: processed_skus contains WordPress SKUs (with suffixes), not original_skus
            # We need to extract original_skus from processed WordPress SKUs
            processed_original_skus = set()
            if self.processed_skus:
                for wp_sku in self.processed_skus:
                    # Extract original SKU by removing the hash suffix (e.g., "B00001234-A1B2" -> "B00001234")
                    if '-' in wp_sku:
                        original_sku = wp_sku.rsplit('-', 1)[0]  # Remove last part after final dash
                        processed_original_skus.add(original_sku)
                
                if processed_original_skus:
                    placeholders = ','.join(['%s'] * len(processed_original_skus))
                    where_conditions.append(f"p.part_number NOT IN ({placeholders})")
                    params.extend(list(processed_original_skus))
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            limit_clause = f"LIMIT {limit}" if limit else ""
            
            # Modified query to create separate products for each usage context (Oscar-style)
            # Each part record becomes a separate WordPress product
            query = f"""
            SELECT 
                p.id as part_id,
                p.part_number as original_sku,
                p.usage_name as name,
                p.call_out_order as callout_number,
                p.unit_qty,
                p.lr,
                p.remark,
                p.nn_note,
                ct.title as sub_category,
                pt.title as main_category,
                sn.vehicle_brand as brand,
                sn.serial
            FROM motorpartsdata_part p
            JOIN motorpartsdata_childtitle ct ON p.child_title_id = ct.id
            JOIN motorpartsdata_parenttitle pt ON ct.parent_id = pt.id
            JOIN motorpartsdata_serialnumber sn ON pt.serial_number_id = sn.id
            {where_clause}
            ORDER BY p.part_number, p.call_out_order
            {limit_clause}
            """
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            excluded_count = len(processed_original_skus) if processed_original_skus else 0
            self.log_message(f"✅ Found {len(results)} individual parts for serial {serial_filter}")
            if excluded_count > 0:
                self.log_message(f"   ⏭️ Excluded {excluded_count} already processed original SKUs from database query")
            
            # Convert to WooCommerce format - each part becomes separate product
            products = []
            for row in results:
                # Generate unique SKU using hash
                import hashlib
                hash_input = f"{row['original_sku']}-{row['part_id']}"
                sku_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:4].upper()
                unique_sku = f"{row['original_sku']}-{sku_suffix}"
                
                product = {
                    'sku': unique_sku,
                    'name': row['name'] or f"Part {row['original_sku']}",
                    'type': 'simple',
                    'status': 'publish',
                    'categories': [
                        {'name': row['brand']},
                        {'name': row['serial']},
                        {'name': row['main_category']},
                        {'name': row['sub_category']}
                    ],
                    'meta_data': [
                        {'key': 'original_sku', 'value': row['original_sku']},
                        {'key': 'oscar_part_id', 'value': str(row['part_id'])},
                        {'key': 'callout_number', 'value': str(row['callout_number'] or '')},
                        {'key': 'unit_qty', 'value': row['unit_qty'] or ''},
                        {'key': 'lr', 'value': row['lr'] or ''},
                        {'key': 'remark', 'value': row['remark'] or ''},
                        {'key': 'nn_note', 'value': row['nn_note'] or ''},
                        {'key': 'vehicle_serial', 'value': row['serial']},
                        {'key': 'oscar_imported', 'value': 'true'},
                        {'key': 'images_pending', 'value': 'true'}
                    ],
                    'description': f'Part for {row["serial"]} - {row["main_category"]}. Usage: {row["name"]}',
                    'short_description': f'Callout: {row["callout_number"] or "N/A"} | Qty: {row["unit_qty"] or "1"}'
                }
                products.append(product)
            
            cursor.close()
            conn.close()
            return products
            
        except Exception as e:
            self.log_message(f"❌ Database extraction failed: {e}", "ERROR")
            return []
    
    def preload_categories(self):
        """Preload all categories to avoid API calls during import"""
        print("📂 Preloading category mappings...")
        
        # Use requests session for connection pooling
        session = requests.Session()
        session.auth = (self.consumer_key, self.consumer_secret)
        
        try:
            # Get all categories in batches
            page = 1
            all_categories = []
            
            while True:
                url = f"{WORDPRESS_URL}/wp-json/wc/v3/products/categories"
                params = {'per_page': 100, 'page': page}
                
                response = session.get(url, params=params)
                print(f"   📄 Page {page}: Status {response.status_code}")
                
                if response.status_code != 200:
                    print(f"   ❌ Page {page} failed with status {response.status_code}")
                    break
                
                categories = response.json()
                if not categories:
                    print(f"   ✅ Page {page} empty, pagination complete")
                    break
                
                print(f"   📦 Page {page}: {len(categories)} categories")
                all_categories.extend(categories)
                page += 1
            
            # Build category cache - simple mapping without duplicate handling
            for cat in all_categories:
                cat_name = cat['name']
                # Always use the latest ID found (should be only one per name)
                self.category_cache[cat_name] = cat['id']
            
            print(f"✅ Cached {len(self.category_cache)} unique categories")
            
            print(f"✅ Cached {len(all_categories)} categories")
            
        except Exception as e:
            print(f"⚠️ Category preloading failed: {e}")
        finally:
            session.close()
    
    async def check_existing_sku(self, session, sku):
        """Check if SKU already exists and return product data"""
        try:
            url = f"{WORDPRESS_URL}/wp-json/wc/v3/products"
            params = {'sku': sku, 'per_page': 10}
            auth = aiohttp.BasicAuth(self.consumer_key, self.consumer_secret)
            
            async with session.get(url, params=params, auth=auth) as response:
                if response.status == 200:
                    products = await response.json()
                    if products and len(products) > 0:
                        # Find exact SKU match (WooCommerce sometimes returns partial matches)
                        for product in products:
                            if product.get('sku', '').upper() == sku.upper():
                                return product
        except Exception as e:
            self.log_message(f"⚠️ Error checking SKU {sku}: {e}")
        return None
    
    async def merge_product_categories(self, session, existing_product, new_categories):
        """Merge new categories into existing product"""
        try:
            product_id = existing_product['id']
            existing_cats = [cat['name'] for cat in existing_product.get('categories', [])]
            new_cat_names = [cat['name'] for cat in new_categories]
            
            # Find categories to add
            categories_to_add = []
            for cat_name in new_cat_names:
                if cat_name not in existing_cats:
                    cat_id = self.find_category_id(cat_name)
                    if cat_id:
                        categories_to_add.append({'id': cat_id})
            
            if categories_to_add:
                # Merge with existing categories
                all_categories = existing_product.get('categories', []) + categories_to_add
                
                update_data = {'categories': all_categories}
                
                url = f"{WORDPRESS_URL}/wp-json/wc/v3/products/{product_id}"
                auth = aiohttp.BasicAuth(self.consumer_key, self.consumer_secret)
                
                async with session.put(url, json=update_data, auth=auth) as response:
                    if response.status in [200, 201]:
                        return True
                    else:
                        error_text = await response.text()
                        self.log_message(f"⚠️ Failed to update categories for {existing_product['sku']}: {error_text}")
        except Exception as e:
            self.log_message(f"❌ Error merging categories: {e}")
        return False
    
    async def async_batch_create_products(self, session, products_batch, batch_id):
        """Create products using async WooCommerce batch API with existing SKU handling"""
        
        # Step 1: Check for existing SKUs and separate into create vs update
        products_to_create = []
        products_to_update = []
        
        skus_in_batch = [p['sku'] for p in products_batch]
        self.log_message(f"Starting batch {batch_id+1}: {len(products_batch)} products {skus_in_batch[:3]}...")
        
        # Check each SKU for existing products
        for product in products_batch:
            existing_product = await self.check_existing_sku(session, product['sku'])
            if existing_product:
                # SKU exists - merge categories
                self.log_message(f"   🔄 SKU {product['sku']} exists, merging categories")
                await self.merge_product_categories(session, existing_product, product['categories'])
                products_to_update.append(product['sku'])
            else:
                # SKU doesn't exist - create new
                products_to_create.append(product)
        
        # Step 2: Only proceed with batch create if we have products to create
        if not products_to_create:
            self.log_message(f"Batch {batch_id+1} SKIPPED: All {len(products_to_update)} SKUs already exist")
            # Mark all as "processed" since we updated their categories
            for sku in products_to_update:
                self.processed_skus.add(sku)
            return batch_id, 0, 0  # batch_id, created_count, failed_count
        
        # Step 3: Process category mappings for new products only
        batch_data = {'create': []}  # Start with empty list
        
        missing_categories = []
        skipped_products = []
        
        for product in products_to_create:
            category_ids = []
            original_categories = [cat['name'] for cat in product.get('categories', [])]
            has_missing_categories = False
            
            for cat in product.get('categories', []):
                cat_name = cat['name']
                cat_id = self.find_category_id(cat_name)  # Use smart matching
                if cat_id:
                    category_ids.append({'id': cat_id})
                else:
                    missing_categories.append(f"SKU {product['sku']}: missing category '{cat_name}'")
                    has_missing_categories = True
            
            # Only add products that have ALL categories found
            if not has_missing_categories:
                product['categories'] = category_ids
                product['_original_categories'] = original_categories
                batch_data['create'].append(product)
            else:
                skipped_products.append(product['sku'])
        
        # Log missing categories and skipped products
        if missing_categories:
            self.log_message(f"⚠️ Batch {batch_id+1} has missing categories:")
            for missing in missing_categories[:10]:  # Log first 10
                self.log_message(f"   {missing}")
                self.log_error(f"Missing category: {missing}")
                
        if skipped_products:
            self.log_message(f"⚠️ Skipped {len(skipped_products)} products due to missing categories:")
            for sku in skipped_products[:5]:
                self.log_message(f"   ❌ {sku}")
            if len(skipped_products) > 5:
                self.log_message(f"   ... and {len(skipped_products)-5} more")
        
        # Only proceed if we have valid products to create
        if not batch_data['create']:
            self.log_message(f"Batch {batch_id+1} SKIPPED: No valid products to create after category check")
            # Mark skipped products as processed to avoid retries
            for sku in skipped_products:
                self.processed_skus.add(sku)
            # Mark updated products as processed
            for sku in products_to_update:
                self.processed_skus.add(sku)
            return batch_id, len(products_to_update), len(skipped_products)
        
        self.log_message(f"   Creating {len(batch_data['create'])} new products, updated {len(products_to_update)} existing")
        
        try:
            url = f"{WORDPRESS_URL}/wp-json/wc/v3/products/batch"
            auth = aiohttp.BasicAuth(self.consumer_key, self.consumer_secret)
            
            async with session.post(
                url,
                json=batch_data,
                auth=auth,
                headers={'Content-Type': 'application/json'},
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Process successful creations
                    created_products = result.get('create', [])
                    successful_skus = []
                    failed_skus = []
                    
                    for i, product_result in enumerate(created_products):
                        original_sku = products_to_create[i]['sku'] if i < len(products_to_create) else 'unknown'
                        
                        if 'error' in product_result:
                            # Product failed
                            error_info = product_result['error']
                            error_msg = f"SKU {original_sku}: {error_info.get('code', 'unknown')} - {error_info.get('message', 'No message')}"
                            failed_skus.append((original_sku, error_msg))
                            self.log_error(f"Product creation failed: {error_msg}", products_to_create[i])
                        else:
                            # Product succeeded
                            successful_skus.append(original_sku)
                            self.processed_skus.add(original_sku)
                    
                    # Add updated SKUs to processed list
                    for sku in products_to_update:
                        self.processed_skus.add(sku)
                    
                    created_count = len(successful_skus)
                    updated_count = len(products_to_update)
                    failed_count = len(failed_skus)
                    
                    self.stats['products_created'] += created_count
                    if failed_count > 0:
                        self.stats['errors'] += failed_count
                    
                    # Log detailed results
                    if successful_skus or products_to_update:
                        self.log_message(f"Batch {batch_id+1} SUCCESS: Created {created_count}, Updated {updated_count} products")
                        if successful_skus:
                            self.log_message(f"   ✅ Created: {successful_skus[:3]}" + (f" and {len(successful_skus)-3} more" if len(successful_skus) > 3 else ""))
                        if products_to_update:
                            self.log_message(f"   🔄 Updated: {products_to_update[:3]}" + (f" and {len(products_to_update)-3} more" if len(products_to_update) > 3 else ""))
                    
                    if failed_skus:
                        self.log_message(f"Batch {batch_id+1} PARTIAL: {failed_count} products failed")
                        for sku, error in failed_skus[:3]:  # Show first 3 failures
                            self.log_message(f"   ❌ {sku}: {error}")
                        if len(failed_skus) > 3:
                            self.log_message(f"   ... and {len(failed_skus)-3} more failures")
                    
                    # Save checkpoint every few batches
                    if batch_id % 3 == 0:
                        self.save_checkpoint(created_products)
                    
                    return batch_id, created_count + updated_count, failed_count
                    
                else:
                    error_text = await response.text()
                    error_msg = f"HTTP {response.status}: {error_text[:200]}"
                    
                    # Log all SKUs as failed for this batch
                    for sku in skus_in_batch:
                        self.log_error(f"Batch failure - SKU {sku}: {error_msg}")
                    
                    self.log_error(f"Batch {batch_id+1} failed: {error_msg}", skus_in_batch)
                    return batch_id, 0, len(skus_in_batch)
                    
        except Exception as e:
            error_msg = str(e)
            
            # Log all SKUs as failed for this batch
            for sku in skus_in_batch:
                self.log_error(f"Batch exception - SKU {sku}: {error_msg}")
            
            self.log_error(f"Batch {batch_id+1} exception: {error_msg}", skus_in_batch)
            return batch_id, 0, len(skus_in_batch)

    async def import_products_async(self, products, concurrent_batches=5):
        """Import products using async batch processing for maximum speed"""
        self.log_message(f"🚀 Starting ASYNC import of {len(products)} products")
        self.log_message(f"   Batch size: {self.batch_size}, Concurrent batches: {concurrent_batches}")
        
        # Split into batches
        batches = []
        for i in range(0, len(products), self.batch_size):
            batch = products[i:i + self.batch_size]
            batches.append(batch)
        
        self.log_message(f"   Created {len(batches)} batches")
        
        # Configure session with connection pooling
        connector = aiohttp.TCPConnector(
            limit=concurrent_batches * 2,
            limit_per_host=concurrent_batches,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=120, connect=30)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        ) as session:
            
            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(concurrent_batches)
            
            async def process_batch_with_semaphore(batch, batch_id):
                async with semaphore:
                    return await self.async_batch_create_products(session, batch, batch_id)
            
            # Create tasks for all batches
            tasks = []
            for i, batch in enumerate(batches):
                task = asyncio.create_task(
                    process_batch_with_semaphore(batch, i)
                )
                tasks.append(task)
            
            # Process with progress bar
            total_failed = 0
            with tqdm(total=len(batches), desc="Processing async batches") as pbar:
                for coro in asyncio.as_completed(tasks):
                    batch_id, created_count, failed_count = await coro
                    
                    if failed_count > 0:
                        total_failed += failed_count
                    
                    pbar.set_postfix({
                        'batch': f"{batch_id+1}/{len(batches)}", 
                        'created': created_count,
                        'failed': failed_count,
                        'total_failed': total_failed
                    })
                    pbar.update(1)
        
        # Log final batch summary
        self.log_message(f"✅ Async import completed")
        self.log_message(f"   Products created: {self.stats['products_created']}")
        self.log_message(f"   Products failed: {total_failed}")
        self.log_message(f"   Total errors: {self.stats['errors']}")
        
        return total_failed
    
    def run_serial_by_serial_import(self, specific_serial=None, limit_per_serial=None):
        """Run import processing one serial at a time"""
        start_time = time.time()
        
        self.log_message("🎯 SERIAL-BY-SERIAL BULK IMPORT STARTED")
        self.log_message("=" * 60)
        
        # Get list of serials to process
        if specific_serial:
            # Process only specified serial
            serials_to_process = [{'serial': specific_serial, 'vehicle_brand': 'Unknown', 'unique_skus': 0, 'total_parts': 0}]
            self.log_message(f"📋 Processing single serial: {specific_serial}")
        else:
            # Get all serials
            serials_to_process = self.get_all_serials()
            self.log_message(f"📋 Found {len(serials_to_process)} serials to process")
            
            # Show serial overview
            for i, serial_info in enumerate(serials_to_process[:5]):
                self.log_message(f"   {i+1}. {serial_info['serial']} ({serial_info['vehicle_brand']}) - {serial_info['unique_skus']} SKUs")
            if len(serials_to_process) > 5:
                self.log_message(f"   ... and {len(serials_to_process)-5} more serials")
        
        # Preload categories once for all serials
        self.preload_categories()
        
        total_processed = 0
        total_created = 0
        
        # Process each serial
        for serial_idx, serial_info in enumerate(serials_to_process):
            serial_number = serial_info['serial']
            self.log_message(f"\n🚗 Processing Serial {serial_idx+1}/{len(serials_to_process)}: {serial_number}")
            self.log_message("-" * 50)
            
            # Extract products for this serial
            products = self.extract_unique_skus(serial_filter=serial_number, limit=limit_per_serial)
            if not products:
                self.log_message(f"   ⏭️ No products found for {serial_number}")
                continue
            
            # Filter out already processed SKUs
            new_products = [p for p in products if p['sku'] not in self.processed_skus]
            if len(new_products) < len(products):
                skipped = len(products) - len(new_products)
                self.log_message(f"   ⏭️ Skipping {skipped} already processed SKUs")
            
            if not new_products:
                self.log_message(f"   ✅ All products for {serial_number} already imported!")
                continue
            
            self.log_message(f"   📦 Importing {len(new_products)} products from {serial_number}")
            
            # Import products for this serial
            try:
                asyncio.run(self.import_products_async(new_products, concurrent_batches=3))
                serial_created = self.stats['products_created'] - total_created
                total_created = self.stats['products_created']
                total_processed += len(new_products)
                
                self.log_message(f"   ✅ Serial {serial_number} completed: {serial_created} products created")
                
            except Exception as e:
                self.log_message(f"   ❌ Serial {serial_number} failed: {e}", "ERROR")
                continue
        
        # Final summary
        elapsed = time.time() - start_time
        rate = total_processed / elapsed if elapsed > 0 else 0
        
        self.log_message("\n🎉 SERIAL-BY-SERIAL IMPORT COMPLETED", "SUCCESS")
        self.log_message(f"   Total time: {elapsed:.1f}s")
        self.log_message(f"   Serials processed: {len(serials_to_process)}")
        self.log_message(f"   Products created: {total_created}")
        self.log_message(f"   Average rate: {rate:.1f} products/second")
        
        # Save final checkpoint
        self.save_checkpoint()
        
        self.log_message(f"📄 Detailed logs saved:")
        self.log_message(f"   Import log: {self.import_log}")
        self.log_message(f"   Progress: {self.progress_log}")
        self.log_message(f"   Errors: {self.error_log}")
        
        return {
            'serials_processed': len(serials_to_process),
            'products_created': total_created,
            'total_processed': len(self.processed_skus),
            'rate': rate
        }

    def import_products_bulk(self, products, concurrent_batches=3):
        """Import products using optimized batch processing (legacy sync method)"""
        print(f"\n🚀 Starting bulk import of {len(products)} products")
        print(f"   Batch size: {self.batch_size}")
        print(f"   Concurrent batches: {concurrent_batches}")
        
        # Split into batches
        batches = []
        for i in range(0, len(products), self.batch_size):
            batch = products[i:i + self.batch_size]
            batches.append(batch)
        
        print(f"   Created {len(batches)} batches")
        
        # Process batches concurrently
        with ThreadPoolExecutor(max_workers=concurrent_batches) as executor:
            futures = []
            
            # Submit all batches
            for i, batch in enumerate(batches):
                future = executor.submit(self.sync_batch_create_products, batch)
                futures.append((i, future))
            
            # Process results with progress bar
            with tqdm(total=len(batches), desc="Processing batches") as pbar:
                for batch_idx, future in futures:
                    try:
                        created_count = future.result(timeout=180)
                        pbar.set_postfix({
                            'batch': f"{batch_idx+1}/{len(batches)}", 
                            'created': created_count
                        })
                    except Exception as e:
                        print(f"❌ Batch {batch_idx+1} failed: {e}")
                        self.stats['errors'] += 1
                    
                    pbar.update(1)
                    
                    # Brief pause between batches to avoid overwhelming server
                    time.sleep(0.1)

    def sync_batch_create_products(self, products_batch):
        """Sync version of batch create for fallback"""
        batch_data = {
            'create': products_batch
        }
        
        # Resolve category IDs
        for product in batch_data['create']:
            category_ids = []
            for cat in product.get('categories', []):
                cat_id = self.category_cache.get(cat['name'])
                if cat_id:
                    category_ids.append({'id': cat_id})
            product['categories'] = category_ids
        
        try:
            url = f"{WORDPRESS_URL}/wp-json/wc/v3/products/batch"
            
            response = requests.post(
                url,
                json=batch_data,
                auth=(self.consumer_key, self.consumer_secret),
                headers={'Content-Type': 'application/json'},
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                created = len(result.get('create', []))
                self.stats['products_created'] += created
                return created
            else:
                print(f"❌ Batch create failed: {response.status_code}")
                return 0
                
        except Exception as e:
            print(f"❌ Batch create error: {e}")
            return 0


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Serial-by-Serial Bulk Import for Oscar to WooCommerce')
    parser.add_argument('--serial', help='Process specific vehicle serial only')
    parser.add_argument('--limit-per-serial', type=int, help='Limit SKUs per serial (for testing)')
    parser.add_argument('--batch-size', type=int, default=20, help='Batch size (default: 20)')
    parser.add_argument('--list-serials', action='store_true', help='List all available serials')
    
    args = parser.parse_args()
    
    optimizer = BulkImportOptimizer(batch_size=args.batch_size)
    
    if args.list_serials:
        print("📋 Available vehicle serials:")
        serials = optimizer.get_all_serials()
        for i, serial_info in enumerate(serials):
            print(f"   {i+1:2d}. {serial_info['serial']} ({serial_info['vehicle_brand']}) - {serial_info['unique_skus']} SKUs")
        print(f"\nTotal: {len(serials)} vehicle serials")
        return
    
    # Run serial-by-serial import
    result = optimizer.run_serial_by_serial_import(
        specific_serial=args.serial,
        limit_per_serial=args.limit_per_serial
    )
    
    if result:
        print(f"\n🎯 Import completed successfully!")
        print(f"   Serials processed: {result['serials_processed']}")
        print(f"   Products created: {result['products_created']}")
        print(f"   Processing rate: {result['rate']:.1f} products/second")

if __name__ == "__main__":
    main()