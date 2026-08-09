"""
Create new parts for replacements
"""
import json
import secrets
import string
import sys
from pathlib import Path
from woocommerce import API

# Load site URL and credentials from config.py / keys.txt
_base_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_base_dir))
from config import WORDPRESS_URL

_keys_file = _base_dir / 'keys.txt'
CONSUMER_KEY = CONSUMER_SECRET = None
with open(_keys_file, 'r', encoding='utf-8') as _f:
    _lines = [l.strip() for l in _f if l.strip()]
for _i, _line in enumerate(_lines):
    if 'Consumer key' in _line and _i + 1 < len(_lines):
        CONSUMER_KEY = _lines[_i + 1]
    if 'Consumer secret' in _line and _i + 1 < len(_lines):
        CONSUMER_SECRET = _lines[_i + 1]
if not CONSUMER_KEY or not CONSUMER_SECRET:
    raise RuntimeError("Could not load WooCommerce credentials from keys.txt")

WP_URL = WORDPRESS_URL

# Initialize WooCommerce API
wcapi = API(
    url=WP_URL,
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    version="wc/v3",
    timeout=30
)


# meta_data key that must always be reset to a fixed value on a duplicate,
# regardless of what the original product had.
FORCED_META_VALUES = {
    "replacement_avail": "no",
}


def _random_suffix(length: int = 5) -> str:
    """Random alphanumeric string used to guarantee SKU uniqueness."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def duplicate_product(product_id: int) -> dict | None:
    """Fetch an existing product and create a draft duplicate.

    The new product's SKU (and its `original_sku` meta) are derived from
    the source product's `replacement_sku` meta value, with a random
    5-character alphanumeric suffix appended to guarantee uniqueness
    (e.g. replacement_sku "C00089390" -> new SKU "C00089390-A1B2C").
    """
    resp = wcapi.get(f"products/{product_id}")
    if resp.status_code != 200:
        print(f"Error fetching product {product_id}: {resp.status_code} {resp.text}")
        return None

    original_product = resp.json()
    original_meta = original_product.get("meta_data", [])

    replacement_sku = next(
        (m["value"] for m in original_meta if m.get("key") == "replacement_sku"),
        "",
    )
    if not replacement_sku:
        print(
            f"Warning: product {product_id} has no replacement_sku meta value set; "
            "cannot derive a new SKU."
        )
        return None

    new_sku = f"{replacement_sku}-{_random_suffix()}"

    # The new product's original_sku meta reflects the source's
    # replacement_sku value, not the source product's own SKU.
    per_key_overrides = {**FORCED_META_VALUES, "original_sku": replacement_sku}

    # Carry over all meta_data as-is (dropping the original "id" on each
    # entry, since meta IDs are per-post — WooCommerce assigns new ones on
    # creation), overriding any keys in per_key_overrides.
    new_meta = [
        {
            "key": m["key"],
            "value": per_key_overrides.get(m["key"], m["value"]),
        }
        for m in original_meta
    ]
    # In case the original product didn't have one of these keys at all,
    # make sure it's still present on the duplicate.
    existing_keys = {m["key"] for m in new_meta}
    for key, value in per_key_overrides.items():
        if key not in existing_keys:
            new_meta.append({"key": key, "value": value})

    duplicated_data = {
        "name": original_product.get("name"),
        "type": original_product.get("type"),
        "status": "draft",
        "regular_price": original_product.get("regular_price"),
        "description": original_product.get("description"),
        "short_description": original_product.get("short_description"),
        "categories": original_product.get("categories"),
        "images": original_product.get("images"),
        "attributes": original_product.get("attributes"),
        "sku": new_sku,
        "meta_data": new_meta,
        # Shipping / dimensions are NOT copied by WooCommerce automatically —
        # they must be passed explicitly like everything else.
        "weight": original_product.get("weight"),
        "dimensions": original_product.get("dimensions"),
        "shipping_class": original_product.get("shipping_class"),
    }

    create_resp = wcapi.post("products", duplicated_data)
    if create_resp.status_code == 201:
        new_product = create_resp.json()
        print(
            f"Success! Duplicated Product ID: {new_product['id']} "
            f"(SKU: {new_sku}, from replacement_sku: {replacement_sku})"
        )
        return new_product
    else:
        print(f"Error creating duplicate: {create_resp.status_code} {create_resp.text}")
        return None


def main():
    duplicate_product(18709)


if __name__ == "__main__":
    main()