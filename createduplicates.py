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


def _to_str(value) -> str:
    """Coerce to string, treating None/empty as ''. Used for fields the Woo
    REST API stores as strings even when GET returns them as numbers
    (e.g. weight comes back as 0.6 but must be posted as "0.6")."""
    if value is None or value == "":
        return ""
    return str(value)


def _to_bool(value) -> bool:
    return bool(value)


def _to_int(value, default: int = 0) -> int:
    if value is None:
        return default
    return int(value)


def _id_list(items) -> list:
    """Categories/tags/brands only need their id on write — GET returns
    name/slug alongside it, but those are read-only and ignored on POST."""
    return [{"id": item["id"]} for item in (items or []) if "id" in item]


def duplicate_product(product_id: int) -> dict | None:
    """Fetch an existing product and create a live duplicate.

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

    # weight/dimensions are string-typed fields in the Woo REST API schema.
    # GET can return them as numbers (weight: 0.6) or null when unset, but
    # POST requires strings — coerce explicitly rather than relying on
    # truthiness.
    original_dimensions = original_product.get("dimensions") or {}
    dimensions = {
        "length": _to_str(original_dimensions.get("length")),
        "width": _to_str(original_dimensions.get("width")),
        "height": _to_str(original_dimensions.get("height")),
    }

    duplicated_data = {
        # --- core content ---
        "name": original_product.get("name"),
        "type": original_product.get("type"),
        "status": "publish",
        "featured": _to_bool(original_product.get("featured")),
        "catalog_visibility": original_product.get("catalog_visibility") or "visible",
        "description": original_product.get("description") or "",
        "short_description": original_product.get("short_description") or "",
        "sku": new_sku,

        # --- pricing (regular_price is already a string like "13.04";
        # sale_price/scheduling intentionally NOT carried over — a fresh
        # draft duplicate shouldn't inherit an active/scheduled sale) ---
        "regular_price": _to_str(original_product.get("regular_price")),

        # --- virtual/downloadable products ---
        "virtual": _to_bool(original_product.get("virtual")),
        "downloadable": _to_bool(original_product.get("downloadable")),
        "download_limit": _to_int(original_product.get("download_limit"), -1),
        "download_expiry": _to_int(original_product.get("download_expiry"), -1),

        # --- external/affiliate products (no-ops for type="simple") ---
        "external_url": original_product.get("external_url") or "",
        "button_text": original_product.get("button_text") or "",

        # --- tax ---
        "tax_status": original_product.get("tax_status") or "taxable",
        "tax_class": original_product.get("tax_class") or "",

        # --- stock ---
        "manage_stock": _to_bool(original_product.get("manage_stock")),
        "stock_quantity": original_product.get("stock_quantity"),
        "stock_status": original_product.get("stock_status") or "instock",
        "backorders": original_product.get("backorders") or "no",
        "sold_individually": _to_bool(original_product.get("sold_individually")),

        # --- shipping ---
        "weight": _to_str(original_product.get("weight")),
        "dimensions": dimensions,
        "shipping_class": original_product.get("shipping_class") or "",

        # --- reviews / ordering ---
        "reviews_allowed": _to_bool(original_product.get("reviews_allowed")),
        "purchase_note": original_product.get("purchase_note") or "",
        "menu_order": _to_int(original_product.get("menu_order"), 0),

        # --- relationships (only id needed on write) ---
        "upsell_ids": original_product.get("upsell_ids") or [],
        "cross_sell_ids": original_product.get("cross_sell_ids") or [],
        "categories": _id_list(original_product.get("categories")),
        "tags": _id_list(original_product.get("tags")),

        # --- media / variations ---
        "images": original_product.get("images") or [],
        "attributes": original_product.get("attributes") or [],
        "default_attributes": original_product.get("default_attributes") or [],

        "meta_data": new_meta,
    }

    # "brands" is a custom taxonomy some Woo sites have (not core on every
    # install) — only send it if the source product actually returned one,
    # to avoid rest_invalid_param on sites where it isn't registered.
    if original_product.get("brands"):
        duplicated_data["brands"] = _id_list(original_product.get("brands"))

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


def get_product_data(product_id: int) -> dict | None:
    """Fetch and pretty-print the raw product JSON for inspection."""
    resp = wcapi.get(f"products/{product_id}")
    if resp.status_code != 200:
        print(f"Error fetching product {product_id}: {resp.status_code} {resp.text}")
        return None
    data = resp.json()
    print(json.dumps(data, indent=4))
    return data


def main():
    duplicate_product(117846)


if __name__ == "__main__":
    main()