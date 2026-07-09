# Custom REST Endpoint: Query & Update by `original_sku`

## Background

**WordPress site**: `https://shane.maxusvanparts.co.uk`

**Problem**: WooCommerce products are stored with SKUs like `B00004124-A3F2` (base part number + 4-char md5 suffix).
The price loader has JSON files named `B00004124.json`. We need to find products by their `original_sku` meta value
(which equals the base part number exactly, e.g. `B00004124`). The standard WooCommerce REST API does not support
filtering by custom meta values.

**Solution**: A custom REST API endpoint added to the active theme's `functions.php` that:

| Route | Method | Purpose |
|---|---|---|
| `/wp-json/custom/v1/products-by-sku?original_sku=B00004124` | GET | Return all product/variation IDs with that `original_sku` meta |
| `/wp-json/custom/v1/products-by-sku` | POST | Update `_price` + `_regular_price` for all matching products |
| `/wp-json/custom/v1/products-by-sku/test` | GET | Health check — count of products with `original_sku` meta, sample values |

**Authentication**: Standard WooCommerce consumer key / secret (Basic Auth). The endpoint requires `edit_products` capability.

> **Important**: WooCommerce's built-in auth middleware only runs for `wc/v3` routes. For `custom/v1` routes, the `cvone_auth_check` permission callback must validate the API key directly against the `woocommerce_api_keys` table. The updated `cvone_auth_check` function below handles this — replace the original simple version if you see `rest_forbidden` 401 errors.

---

## How WC SKUs Work on This Site

| Field | Example value | Notes |
|---|---|---|
| WC `_sku` postmeta | `B00004124-A3F2` | Part number + 4-char md5 suffix — what WC REST API returns as `sku` |
| `original_sku` postmeta | `B00004124` | Raw part number — stored on every product/variation during import |
| Price JSON filename | `B00004124.json` | Named after the raw part number |
| Price field | `allInputs[24].value` | e.g. `"1.33"` |

---

## PHP Code to Insert into `functions.php`

Add the entire block below to the **bottom of** `wp-content/themes/<active-theme>/functions.php`.
If the file ends with `?>`, insert before it; otherwise just append.

```php
/**
 * Custom REST API: query and update products by original_sku meta
 * Namespace: custom/v1
 * Routes:
 *   GET  /wp-json/custom/v1/products-by-sku?original_sku=B00004124
 *   POST /wp-json/custom/v1/products-by-sku  body: { original_sku, price }
 *   GET  /wp-json/custom/v1/products-by-sku/test
 */
add_action( 'rest_api_init', function () {

    // --- GET: look up products by original_sku ---
    register_rest_route( 'custom/v1', '/products-by-sku', array(
        'methods'             => 'GET',
        'callback'            => 'cvone_get_products_by_original_sku',
        'permission_callback' => 'cvone_auth_check',
        'args'                => array(
            'original_sku' => array(
                'required'          => true,
                'sanitize_callback' => 'sanitize_text_field',
            ),
        ),
    ) );

    // --- POST: update price for products with original_sku ---
    register_rest_route( 'custom/v1', '/products-by-sku', array(
        'methods'             => 'POST',
        'callback'            => 'cvone_update_price_by_original_sku',
        'permission_callback' => 'cvone_auth_check',
    ) );

    // --- GET /test: verify endpoint and meta query work ---
    register_rest_route( 'custom/v1', '/products-by-sku/test', array(
        'methods'             => 'GET',
        'callback'            => 'cvone_test_endpoint',
        'permission_callback' => 'cvone_auth_check',
    ) );
} );

/**
 * Authenticate via WC consumer key/secret (Basic Auth or query-string).
 * WC's own auth sets the user for wc/v3 routes but NOT custom namespaces,
 * so we validate the key directly against the woocommerce_api_keys table.
 */
function cvone_auth_check( WP_REST_Request $request ) {
    // If WC auth has already set a user, check capability
    if ( is_user_logged_in() && current_user_can( 'edit_products' ) ) {
        return true;
    }
    // Validate WC consumer key directly from query params or Basic Auth header
    $ck = $request->get_param( 'consumer_key' );
    $cs = $request->get_param( 'consumer_secret' );
    if ( ! $ck ) {
        // Try Basic Auth header (consumer_key as username, consumer_secret as password)
        $ck = isset( $_SERVER['PHP_AUTH_USER'] ) ? $_SERVER['PHP_AUTH_USER'] : '';
        $cs = isset( $_SERVER['PHP_AUTH_PW'] )   ? $_SERVER['PHP_AUTH_PW']   : '';
    }
    if ( $ck && $cs ) {
        global $wpdb;
        $keys = $wpdb->get_row( $wpdb->prepare(
            "SELECT user_id, permissions, consumer_secret
               FROM {$wpdb->prefix}woocommerce_api_keys
              WHERE consumer_key = %s",
            wc_api_hash( $ck )
        ) );
        if ( $keys && hash_equals( $keys->consumer_secret, $cs ) ) {
            wp_set_current_user( $keys->user_id );
            return current_user_can( 'edit_products' );
        }
    }
    return false;
}

/**
 * Query the postmeta table directly for original_sku matches.
 * Returns all post IDs (products + variations) that have original_sku = $sku.
 */
function cvone_query_ids_by_original_sku( $sku ) {
    global $wpdb;
    $sku = sanitize_text_field( $sku );
    $ids = $wpdb->get_col( $wpdb->prepare(
        "SELECT post_id
           FROM {$wpdb->postmeta}
          WHERE meta_key   = 'original_sku'
            AND meta_value = %s",
        $sku
    ) );
    return array_map( 'intval', $ids );
}

/**
 * GET /wp-json/custom/v1/products-by-sku?original_sku=B00004124
 */
function cvone_get_products_by_original_sku( WP_REST_Request $request ) {
    $sku  = $request->get_param( 'original_sku' );
    $ids  = cvone_query_ids_by_original_sku( $sku );

    if ( empty( $ids ) ) {
        return new WP_REST_Response( array(
            'found'        => 0,
            'original_sku' => $sku,
            'products'     => array(),
        ), 200 );
    }

    $results = array();
    foreach ( $ids as $post_id ) {
        $post        = get_post( $post_id );
        $wc_sku      = get_post_meta( $post_id, '_sku', true );
        $parent_id   = $post ? (int) $post->post_parent : 0;
        $results[]   = array(
            'id'           => $post_id,
            'parent_id'    => $parent_id,
            'type'         => ( $parent_id > 0 ) ? 'variation' : 'product',
            'wc_sku'       => $wc_sku,
            'original_sku' => $sku,
            'status'       => $post ? $post->post_status : 'unknown',
        );
    }

    return new WP_REST_Response( array(
        'found'        => count( $results ),
        'original_sku' => $sku,
        'products'     => $results,
    ), 200 );
}

/**
 * POST /wp-json/custom/v1/products-by-sku
 * Body (JSON): { "original_sku": "B00004124", "price": "1.33" }
 */
function cvone_update_price_by_original_sku( WP_REST_Request $request ) {
    $sku   = sanitize_text_field( $request->get_param( 'original_sku' ) );
    $price = $request->get_param( 'price' );

    if ( ! $sku ) {
        return new WP_Error( 'missing_sku', 'original_sku is required', array( 'status' => 400 ) );
    }
    if ( ! is_numeric( $price ) || (float) $price <= 0 ) {
        return new WP_Error( 'invalid_price', 'price must be a positive number', array( 'status' => 400 ) );
    }

    $price_str = number_format( (float) $price, 2, '.', '' );
    $ids       = cvone_query_ids_by_original_sku( $sku );

    if ( empty( $ids ) ) {
        return new WP_REST_Response( array(
            'updated'      => 0,
            'original_sku' => $sku,
            'message'      => 'No products found with that original_sku',
        ), 200 );
    }

    $updated = array();
    $failed  = array();

    foreach ( $ids as $post_id ) {
        // Update WooCommerce price meta directly
        $ok1 = update_post_meta( $post_id, '_price',         $price_str );
        $ok2 = update_post_meta( $post_id, '_regular_price', $price_str );

        // Clear the transient/object cache for this product
        $parent_id = (int) get_post_field( 'post_parent', $post_id );
        wc_delete_product_transients( $parent_id > 0 ? $parent_id : $post_id );

        if ( $ok1 !== false || $ok2 !== false ) {
            $updated[] = array(
                'id'        => $post_id,
                'parent_id' => $parent_id,
                'price'     => $price_str,
            );
        } else {
            $failed[] = $post_id;
        }
    }

    return new WP_REST_Response( array(
        'original_sku' => $sku,
        'price'        => $price_str,
        'updated'      => count( $updated ),
        'failed'       => count( $failed ),
        'products'     => $updated,
        'failed_ids'   => $failed,
    ), 200 );
}

/**
 * GET /wp-json/custom/v1/products-by-sku/test
 * Runs a test query against postmeta to confirm original_sku meta exists on the site.
 */
function cvone_test_endpoint( WP_REST_Request $request ) {
    global $wpdb;

    // Count how many products have the original_sku meta key at all
    $total_with_meta = (int) $wpdb->get_var(
        "SELECT COUNT(*) FROM {$wpdb->postmeta} WHERE meta_key = 'original_sku'"
    );

    // Grab up to 5 example values
    $examples = $wpdb->get_results(
        "SELECT post_id, meta_value
           FROM {$wpdb->postmeta}
          WHERE meta_key = 'original_sku'
          LIMIT 5",
        ARRAY_A
    );

    // Try a specific lookup for B00004124 as a known test SKU
    $test_sku  = 'B00004124';
    $test_ids  = cvone_query_ids_by_original_sku( $test_sku );

    return new WP_REST_Response( array(
        'status'                        => 'ok',
        'total_with_original_sku_meta'  => $total_with_meta,
        'example_values'                => $examples,
        'test_sku'                      => $test_sku,
        'test_sku_post_ids'             => $test_ids,
    ), 200 );
}
```

---

## Troubleshooting: Route Not Found (404)

### Site & API credentials for testing

| | |
|---|---|
| **Site URL** | `https://shane.maxusvanparts.co.uk` |
| **Consumer Key** | `ck_f1afc5dfb58879e9f5cb2a00e2d0a80c3d72275c` |
| **Consumer Secret** | `cs_4d5dd541b8f50d4c562462bd4fc0c1c814c7c4b3` |
| **Auth method** | Query-string params `consumer_key` + `consumer_secret` (NOT Basic Auth — WP intercepts Basic Auth before custom routes can handle it) |

**Direct browser test** (GET, no tools needed — paste into browser address bar):
```
https://shane.maxusvanparts.co.uk/wp-json/custom/v1/products-by-sku/test?consumer_key=ck_f1afc5dfb58879e9f5cb2a00e2d0a80c3d72275c&consumer_secret=cs_4d5dd541b8f50d4c562462bd4fc0c1c814c7c4b3
```

**Check route is registered** (also paste into browser):
```
https://shane.maxusvanparts.co.uk/wp-json/custom/v1
```
Should show `products-by-sku` and `products-by-sku/test` in the routes. If only `products-not-in-category` appears, the PHP block was not saved.

---

If `/wp-json/custom/v1/products-by-sku` returns 404, check the registered routes:

```
GET /wp-json
```

Look for `/custom/v1/products-by-sku` in the `routes` list. If it's **missing** but `/custom/v1` namespace is present (showing only `/custom/v1/products-not-in-category`), it means the `products-by-sku` block was **not saved** into `functions.php`.

**Known issue (March 2026)**: When the theme was first edited, only the old `products-not-in-category` route was preserved. The new `products-by-sku` block was not included. Re-insert the full PHP block below into `functions.php` — leave the existing `products-not-in-category` route untouched, just append the new block alongside it.

To verify the route is live after inserting:
```powershell
.\env\Scripts\python.exe -c "
import requests, json
from config import WORDPRESS_URL
ck = 'ck_f1afc5dfb58879e9f5cb2a00e2d0a80c3d72275c'
cs = 'cs_4d5dd541b8f50d4c562462bd4fc0c1c814c7c4b3'
r = requests.get(WORDPRESS_URL.rstrip('/')+'/wp-json', params={'consumer_key':ck,'consumer_secret':cs}, timeout=15)
routes = [k for k in r.json().get('routes', {}).keys() if 'products-by-sku' in k]
print('products-by-sku routes:', routes)
"
```
Expected output: `products-by-sku routes: ['/custom/v1/products-by-sku', '/custom/v1/products-by-sku/test']`

---

## Testing After Insertion

Run from `c:\pythonstuff\wpimport` once the code is in place:

```powershell
.\env\Scripts\python.exe -c "
import requests, json
from config import WORDPRESS_URL
ck = 'ck_f1afc5dfb58879e9f5cb2a00e2d0a80c3d72275c'
cs = 'cs_4d5dd541b8f50d4c562462bd4fc0c1c814c7c4b3'

# Test 1: health check - counts products with original_sku meta, shows 5 examples
print('=== TEST endpoint ===')
r = requests.get(WORDPRESS_URL+'/wp-json/custom/v1/products-by-sku/test', auth=(ck,cs), timeout=15)
print('Status:', r.status_code)
print(json.dumps(r.json(), indent=2))

# Test 2: GET lookup by original_sku
print('\n=== GET by original_sku ===')
r2 = requests.get(WORDPRESS_URL+'/wp-json/custom/v1/products-by-sku',
                  params={'original_sku': 'B00004124'}, auth=(ck,cs), timeout=15)
print('Status:', r2.status_code)
print(json.dumps(r2.json(), indent=2))
"
```

### Expected successful output from `/test`

```json
{
  "status": "ok",
  "total_with_original_sku_meta": 3685,
  "example_values": [
    { "post_id": "1234", "meta_value": "B00004124" },
    ...
  ],
  "test_sku": "B00004124",
  "test_sku_post_ids": [1234]
}
```

- `total_with_original_sku_meta` should be > 0 (confirms the meta is being stored)
- `test_sku_post_ids` should be a non-empty array if `B00004124` was imported

### Expected successful output from GET lookup

```json
{
  "found": 1,
  "original_sku": "B00004124",
  "products": [
    {
      "id": 1234,
      "parent_id": 0,
      "type": "product",
      "wc_sku": "B00004124-A3F2",
      "original_sku": "B00004124",
      "status": "publish"
    }
  ]
}
```

---

## What Happens Next (in `wppriceloader.py`)

Once the endpoint is confirmed working, `find_all_products_by_sku()` in `wppriceloader.py` will be updated to:

1. `GET /wp-json/custom/v1/products-by-sku?original_sku={sku}` → get exact list of product/variation IDs
2. For each result, `POST /wp-json/custom/v1/products-by-sku` with `{ original_sku, price }` → update price directly

This replaces the current broken text-search strategy that returns false positives.

---

## Credentials Reference

| Key | Value |
|---|---|
| Site URL | `https://shane.maxusvanparts.co.uk` |
| Consumer Key | `ck_f1afc5dfb58879e9f5cb2a00e2d0a80c3d72275c` |
| Consumer Secret | `cs_4d5dd541b8f50d4c562462bd4fc0c1c814c7c4b3` |
| Auth method | HTTP Basic Auth (WC API key pair) |
