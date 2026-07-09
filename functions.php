<?php
// ============================================================// FIX: Vehicle & Department page titles (override AIOSEO)// ============================================================add_filter( 'pre_get_document_title', 'mvp_fix_page_titles', 999 );add_filter( 'aioseo_title', 'mvp_fix_page_titles_aioseo', 999 );function mvp_fix_page_titles( $title ) {    $vehicle_slug = get_query_var( 'mvp_vehicle' );    if ( $vehicle_slug ) {        $maxus_term_id = mvp_get_maxus_term_id();        $vin_terms = get_terms( array(            'taxonomy'   => 'product_cat',            'parent'     => $maxus_term_id,            'hide_empty' => false,            'meta_query' => array( array( 'key' => 'vehicle_slug', 'value' => sanitize_title( $vehicle_slug ) ) ),        ) );        if ( ! is_wp_error( $vin_terms ) && ! empty( $vin_terms ) ) {            $model = get_term_meta( $vin_terms[0]->term_id, 'vehicle_model', true );            return ( $model ? $model : 'Vehicle' ) . ' - Maxus Parts Direct';        }    }    $dept_slug = get_query_var( 'mvp_department' );    if ( $dept_slug ) {        $dept_name = ucwords( str_replace( '-', ' ', $dept_slug ) );        $vehicle_slug2 = get_query_var( 'mvp_dept_vehicle' );        if ( $vehicle_slug2 ) {            $maxus_term_id = mvp_get_maxus_term_id();            $vin_terms = get_terms( array(                'taxonomy'   => 'product_cat',                'parent'     => $maxus_term_id,                'hide_empty' => false,                'meta_query' => array( array( 'key' => 'vehicle_slug', 'value' => sanitize_title( $vehicle_slug2 ) ) ),            ) );            if ( ! is_wp_error( $vin_terms ) && ! empty( $vin_terms ) ) {                $model = get_term_meta( $vin_terms[0]->term_id, 'vehicle_model', true );                return $dept_name . ' - ' . ( $model ? $model : $vehicle_slug2 ) . ' - Maxus Parts Direct';            }        }        return $dept_name . ' - Maxus Parts Direct';    }    return $title;}function mvp_fix_page_titles_aioseo( $title ) {    $custom = mvp_fix_page_titles( '' );    return $custom ? $custom : $title;}
require_once get_stylesheet_directory() . "/trade-account-form.php";

function mobex_enovathemes_child_scripts() {
    wp_enqueue_style( 'mobex_enovathemes-parent-style', get_template_directory_uri(). '/style.css' );
}
add_action( 'wp_enqueue_scripts', 'mobex_enovathemes_child_scripts' );

// Replace product SKU with original_sku meta field ONLY for frontend display
// This does NOT affect order processing, inventory, or any backend operations
add_filter( 'woocommerce_product_get_sku', 'mvp_use_original_sku_on_frontend', 10, 2 );
add_filter( 'woocommerce_product_variation_get_sku', 'mvp_use_original_sku_on_frontend', 10, 2 );
function mvp_use_original_sku_on_frontend( $sku, $product ) {
    // Skip if in admin area
    if ( is_admin() ) {
        return $sku;
    }
    
    // Skip during AJAX requests (checkout, cart updates, etc.)
    if ( wp_doing_ajax() ) {
        return $sku;
    }
    
    // Skip during REST API requests (order processing, inventory sync, etc.)
    if ( defined( 'REST_REQUEST' ) && REST_REQUEST ) {
        return $sku;
    }
    
    // Skip during cron jobs
    if ( wp_doing_cron() ) {
        return $sku;
    }
    
    // Skip during any order/cart processing to ensure backend operations use real SKU
    $wc_actions = array(
        'woocommerce_checkout_process',
        'woocommerce_checkout_order_processed',
        'woocommerce_new_order',
        'woocommerce_order_status_changed',
        'woocommerce_add_to_cart',
        'woocommerce_cart_item_removed',
        'woocommerce_update_cart_action_cart_updated',
    );
    foreach ( $wc_actions as $action ) {
        if ( did_action( $action ) || doing_action( $action ) ) {
            return $sku;
        }
    }
    
    // Only replace for display purposes on frontend
    $original_sku = get_post_meta( $product->get_id(), 'original_sku', true );
    if ( $original_sku ) {
        return $original_sku;
    }
    
    return $sku;
}

add_action('after_switch_theme', 'mobex_child_repair_theme_mods_and_kirki_css');
add_action('admin_init', 'mobex_child_repair_theme_mods_and_kirki_css_once');

function mobex_child_repair_theme_mods_and_kirki_css_once() {
    // If we already repaired, skip.
    if (get_option('mobex_child_theme_mods_repaired')) {
        return;
    }
    $did = mobex_child_repair_theme_mods_and_kirki_css();
    if ($did) {
        update_option('mobex_child_theme_mods_repaired', 1);
    }
}

/**
 * Returns true if it actually migrated/changed anything.
 */
function mobex_child_repair_theme_mods_and_kirki_css() {
    $parent = get_template();
    $child  = get_stylesheet();
    if ($parent === $child) {
        // Not a child setup.
        return false;
    }
}

/**
 * Custom REST API endpoint to find products NOT in a specific category
 */
add_action('rest_api_init', function () {
    register_rest_route('custom/v1', '/products-not-in-category', array(
        'methods' => 'GET',
        'callback' => 'get_products_not_in_category',
        'permission_callback' => function() {
            return current_user_can('edit_products');
        }
    ));
});

function get_products_not_in_category($request) {
    $exclude_category = $request->get_param('exclude_category');
    $page = $request->get_param('page') ?: 1;
    $per_page = 100;
    
    if (!$exclude_category) {
        return new WP_Error('missing_param', 'exclude_category parameter required', array('status' => 400));
    }
    
    global $wpdb;
    
    // Find all product IDs that DO NOT have the specified category
    // This excludes products that have this category in their term relationships
    $offset = ($page - 1) * $per_page;
    
    $query = "
        SELECT DISTINCT p.ID 
        FROM {$wpdb->posts} p
        WHERE p.post_type = 'product'
        AND p.post_status = 'publish'
        AND p.ID NOT IN (
            SELECT object_id 
            FROM {$wpdb->term_relationships} tr
            INNER JOIN {$wpdb->term_taxonomy} tt ON tr.term_taxonomy_id = tt.term_taxonomy_id
            WHERE tt.term_id = %d
            AND tt.taxonomy = 'product_cat'
        )
        ORDER BY p.ID
        LIMIT %d OFFSET %d
    ";
    
    $product_ids = $wpdb->get_col($wpdb->prepare($query, $exclude_category, $per_page, $offset));
    
    // Get total count
    $count_query = "
        SELECT COUNT(DISTINCT p.ID) 
        FROM {$wpdb->posts} p
        WHERE p.post_type = 'product'
        AND p.post_status = 'publish'
        AND p.ID NOT IN (
            SELECT object_id 
            FROM {$wpdb->term_relationships} tr
            INNER JOIN {$wpdb->term_taxonomy} tt ON tr.term_taxonomy_id = tt.term_taxonomy_id
            WHERE tt.term_id = %d
            AND tt.taxonomy = 'product_cat'
        )
    ";
    
    $total = $wpdb->get_var($wpdb->prepare($count_query, $exclude_category));
    $total_pages = ceil($total / $per_page);
    
    return array(
        'ids' => array_map('intval', $product_ids),
        'total' => (int)$total,
        'page' => (int)$page,
        'per_page' => $per_page,
        'total_pages' => (int)$total_pages
    );
}


/**


/**
 * Maxus Van Parts — Homepage Facelift
 *
 * Transforms shane.maxusvanparts.co.uk homepage to match
 * the maxusvanparts.acstestweb.co.uk design.
 *
 * Approach: CSS hides unwanted Elementor sections, JS injects
 * hero banner + vehicle carousel into correct DOM position.
 */


// ============================================================
// 0. SITE-WIDE HEADER — 3-row header matching target site
// ============================================================
add_action( 'wp_head', 'mvp_sitewide_header_css', 998 );
function mvp_sitewide_header_css() {
    $logo_url = content_url( '/uploads/mpd-logo-original.webp' );
    ?>
    <style id="mvp-sitewide-header">
    /* ── Hide default Mobex desktop header + Elementor header — we replace it entirely ── */
    #et-desktop-8543,
    .et-desktop.header {
        display: none !important;
    }

    /* ── Mobile header: orange background + logo swap ── */
    #et-mobile-435 {
        background: #F29F05 !important;
    }
    #et-mobile-435 .header-logo .logo {
        visibility: hidden;
        width: 0; height: 0; position: absolute;
    }
    #et-mobile-435 .header-logo {
        display: block;
        background-image: url('<?php echo esc_url( $logo_url ); ?>');
        background-repeat: no-repeat;
        background-size: contain;
        background-position: center left;
        width: 180px; height: 40px; min-width: 180px;
    }
    #et-mobile-435 .mobile-toggle,
    #et-mobile-435 .mobile-toggle:before,
    #et-mobile-435 .mobile-toggle:after {
        color: #fff !important;
        background-color: #fff !important;
    }
    #et-mobile-435 .mobile-menu li a { color: #333 !important; }
    #et-mobile-435 [data-id="60c0b2d"],
    #et-mobile-435 .e-con {
        background: #D18A0C !important;
    }
    #et-mobile-435 .e-con * {
        color: #fff !important;
    }
    /* Hamburger toggle — SVG 3-line icon */
    #et-mobile-435 .mobile-toggle {
        width: 30px !important;
        height: 30px !important;
        position: relative !important;
        z-index: 100;
        background: transparent !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='20' viewBox='0 0 24 20'%3E%3Crect y='0' width='24' height='3' rx='1.5' fill='white'/%3E%3Crect y='8.5' width='24' height='3' rx='1.5' fill='white'/%3E%3Crect y='17' width='24' height='3' rx='1.5' fill='white'/%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: 24px 20px !important;
        border: none !important;
        box-shadow: none !important;
        cursor: pointer !important;
        font-size: 0 !important;
        color: transparent !important;
    }
    #et-mobile-435 .mobile-toggle:before,
    #et-mobile-435 .mobile-toggle:after {
        display: none !important;
    }
    }

    /* ═══════════════════════════════════════
       CUSTOM 3-ROW DESKTOP HEADER
       ═══════════════════════════════════════ */
    .mvp-hdr { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    .mvp-hdr *, .mvp-hdr *::before, .mvp-hdr *::after { box-sizing: border-box; }
    .mvp-hdr a { text-decoration: none; transition: color 0.2s, background 0.2s; }
    .mvp-hdr-wrap { max-width: 1320px; margin: 0 auto; padding: 0 10px; }

    /* ── ROW 1: Top utility bar — white bg, 48px min-height ── */
    .mvp-hdr-r1 {
        background: #fff;
        border-bottom: 1px solid #f0f0f0;
    }
    .mvp-hdr-r1 .mvp-hdr-wrap {
        display: flex;
        align-items: center;
        min-height: 48px;
        gap: 0;
    }
    .mvp-hdr-r1-ask {
        display: flex; align-items: center; gap: 8px;
        color: #111; font-size: 13px; font-weight: 400;
    }
    .mvp-hdr-r1-ask svg { width: 18px; height: 18px; fill: #F29F05; flex-shrink: 0; display: none; }
    .mvp-hdr-r1-ask:hover { color: #F29F05; }

    .mvp-hdr-r1-social {
        display: flex; align-items: center; gap: 8px;
        margin-left: auto;
    }
    .mvp-hdr-r1-social span {
        font-size: 13px; font-weight: 600; color: #111;
        margin-right: 8px;
    }
    .mvp-hdr-r1-social a {
        display: flex; align-items: center; justify-content: center;
        width: 24px; height: 24px;
    }
    .mvp-hdr-r1-social a svg { width: 12px; height: 12px; fill: #fff; }
    .mvp-hdr-r1-social a:hover svg { fill: #fff; }
    .mvp-hdr-r1-social a { border-radius: 6px; }
    .mvp-hdr-r1-social a[title="Facebook"] { background: #3B5998; }
    .mvp-hdr-r1-social a[title="Instagram"] { background: #BC2A8D; }
    .mvp-hdr-r1-social a[title="LinkedIn"] { background: #007BB6; }
    .mvp-hdr-r1-social a[title="Twitter"] { background: #00ACED; }
    .mvp-hdr-r1-social a[title="YouTube"] { background: #BB0000; }

    .mvp-hdr-r1-login {
        margin-left: 18px; position: relative; margin-right: -20px;
    }
    .mvp-hdr-r1-login > a {
        display: flex; align-items: center; gap: 6px;
        background: none; color: #111; font-size: 13px; font-weight: 700;
        padding: 0; height: auto; cursor: pointer; border-radius: 0;
    }
    .mvp-hdr-r1-login > a svg { width: 14px; height: 14px; fill: #111; }
    .mvp-hdr-r1-login > a:hover { color: #F29F05; } .mvp-hdr-r1-login > a:hover svg { fill: #F29F05; }
    .mvp-hdr-r1-login .mvp-login-dd {
        display: none; position: absolute; right: 0; top: 40px;
        background: #111; padding: 16px; min-width: 220px; z-index: 9999;
        border-radius: 0 0 4px 4px;
    }
    .mvp-hdr-r1-login:hover .mvp-login-dd { display: block; }
    .mvp-login-dd input[type="text"],
    .mvp-login-dd input[type="password"] {
        width: 100%; padding: 8px 10px; margin-bottom: 8px;
        border: 1px solid #333; border-radius: 3px;
        background: #222; color: #fff; font-size: 13px;
    }
    .mvp-login-dd input::placeholder { color: #999; }
    .mvp-login-dd .mvp-login-btn {
        width: 100%; padding: 8px; border: none; border-radius: 3px;
        background: #F29F05; color: #000; font-weight: 700; font-size: 13px;
        cursor: pointer; margin-bottom: 8px;
    }
    .mvp-login-dd .mvp-login-btn:hover { background: #F29F05; }
    .mvp-login-dd .mvp-login-links { display: flex; justify-content: space-between; }
    .mvp-login-dd .mvp-login-links a { color: #9a9a9a; font-size: 12px; }
    .mvp-login-dd .mvp-login-links a:hover { color: #fff; }

    /* ── ROW 2: Logo + search + phone — white bg, padding 4px 0 16px ── */
    .mvp-hdr-r2 {
        background: #fff;
    }
    .mvp-hdr-r2 .mvp-hdr-wrap {
        display: flex;
        align-items: center;
        padding-top: 8px;
        padding-bottom: 16px;
        gap: 0;
    }
    .mvp-hdr-r2-logo {
        flex-shrink: 0;
        margin-right: 32px;
    }
    .mvp-hdr-r2-logo img {
        width: 164px; height: auto; display: block;
    }
    .mvp-hdr-r2-home {
        flex-shrink: 0;
        display: flex; align-items: center; gap: 8px;
        background: #BF3617; color: #fff; font-weight: 700; font-size: 16px;
        padding: 0 24px; height: 48px; border-radius: 6px;
        margin-right: 8px;
    }
    .mvp-hdr-r2-home svg { width: 18px; height: 18px; flex-shrink: 0; }
    .mvp-hdr-r2-home:hover { background: #a82e13; color: #fff; }

    .mvp-hdr-r2-search {
        flex: 1; display: flex; align-items: center; max-width: 520px;
        background: #f0f0f0; border: 1px solid #e0e0e0; border-radius: 6px;
        overflow: hidden; height: 48px;
    }
    .mvp-hdr-r2-search input[type="text"] {
        text-align: center; line-height: 48px;
        flex: 1; border: none; background: transparent;
        padding: 0 14px; font-size: 14px; color: #333; height: 100%;
        outline: none;
    }
    .mvp-hdr-r2-search input::placeholder { color: #999; }
    .mvp-hdr-r2-search button {
        background: #BF3617; border: none; color: #fff;
        width: 52px; height: 100%; font-size: 0;
        cursor: pointer; flex-shrink: 0;
        display: flex; align-items: center; justify-content: center;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2.5' stroke-linecap='round'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cpath d='M21 21l-4.35-4.35'/%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: center;
    }
    .mvp-hdr-r2-search button:hover { background: #a82e13; }

    .mvp-hdr-r2-phone {
        flex-shrink: 0; display: flex; align-items: center; gap: 10px;
        margin-left: auto; text-decoration: none; color: #333;
    }
    .mvp-hdr-r2-phone svg { display: none !important; }
    .mvp-hdr-r2-phone-text { line-height: 1.3; }
    .mvp-hdr-r2-phone-num { font-size: 14px; font-weight: 700; color: #111; display: block; }
    .mvp-hdr-r2-phone-sub { font-size: 13px; color: #777; display: block; }

    /* ── ROW 3: Nav bar — dark gold, 64px min-height ── */
    .mvp-hdr-r3 {
        background: #D18A0C;
    }
    .mvp-hdr-r3 .mvp-hdr-wrap {
        display: flex;
        align-items: center;
        min-height: 64px;
    }
    .mvp-hdr-r3-nav {
        display: flex; align-items: center; gap: 0;
        list-style: none; margin: 0; padding: 0;
        margin-left: -16px;
        margin-right: auto;
    }
    .mvp-hdr-r3-nav li a {
        display: block; padding: 22px 16px;
        color: #fff; font-size: 16px; font-weight: 700;
        white-space: nowrap; line-height: 1;
    }
    .mvp-hdr-r3-nav li a:hover {
    }
    .mvp-hdr-r3-nav li.current-menu-item a, .mvp-hdr-r3-nav li:first-child a {
        text-decoration: underline; text-underline-offset: 4px;
    /* ── Nav dropdown menu ── */
    .mvp-hdr-r3-nav .mvp-has-dropdown { position: relative; }
    .mvp-hdr-r3-nav .mvp-dropdown {
        display: none !important; position: absolute; top: 100%; left: 0; z-index: 9999;
        background: #fff; min-width: 260px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        border-radius: 0 0 6px 6px; padding: 8px 0; list-style: none; margin: 0;
    }
    .mvp-hdr-r3-nav .mvp-has-dropdown:hover .mvp-dropdown { display: block !important; }
    .mvp-hdr-r3-nav .mvp-dropdown li a {
        display: block; padding: 8px 20px; color: #333 !important; font-size: 14px !important;
        font-weight: 500 !important; white-space: nowrap;
    }
    .mvp-hdr-r3-nav .mvp-dropdown li a:hover {
        background: #f5f5f5; color: #BF3617 !important; text-decoration: none !important;
    }
    /* ── Custom scrollbar for vehicle dropdown ── */
    .mvp-mega::-webkit-scrollbar { display: none; }
    .mvp-mega { -ms-overflow-style: none; scrollbar-width: none; }
        text-decoration: underline; text-underline-offset: 4px;
    }
    .mvp-hdr-r3-actions {
        display: flex; align-items: center; gap: 0;
        margin-left: auto;
    }
    .mvp-hdr-r3-actions a {
        display: flex; align-items: center; gap: 6px;
        padding: 22px 14px; color: #fff; font-size: 13px; font-weight: 600;
        white-space: nowrap; line-height: 1;
    }
    .mvp-hdr-r3-actions a svg { width: 20px; height: 20px; fill: #fff; }
    .mvp-hdr-r3-actions a:hover { text-decoration: underline; text-underline-offset: 4px; }
    .mvp-hdr-r3-actions a.mvp-r3-cart { flex-direction: row; align-items: center; gap: 6px; }
    .mvp-hdr-r3-actions a.mvp-r3-icon { padding: 22px 12px; gap: 0; } .mvp-hdr-r3-actions a.mvp-r3-icon svg { border-radius: 32px; }
    .mvp-hdr-r3-actions a.mvp-r3-icon svg { width: 22px; height: 22px; }
    .mvp-hdr-r3-actions .mvp-r3-myvehicle {
        background: #BF3617; padding: 0 24px; height: 48px; border-radius: 6px; font-size: 16px;
        margin-left: 8px; font-weight: 700;
    }
    .mvp-hdr-r3-actions .mvp-r3-myvehicle:hover { background: #040404; text-decoration: none; }
    .mvp-hdr-r3-actions .mvp-cart-badge {
    .mvp-cart-text { font-size: 16px; font-weight: 700; line-height: 1; width: 100%; }
    .mvp-cart-stacked { display: flex; flex-direction: column; gap: 1px; }
    .mvp-cart-sub { font-size: 11px; font-weight: 700; display: block; line-height: 1; margin-top: 2px; }
    .mvp-cart-sub .mvp-cart-badge { margin-left: 0; margin-right: 2px; }
        background: #F29F05; color: #000; font-size: 10px; font-weight: 700;
    .mvp-cart-text { font-size: 16px; font-weight: 700; line-height: 1; width: 100%; }
    .mvp-cart-stacked { display: flex; flex-direction: column; gap: 1px; }
    .mvp-cart-sub { font-size: 11px; font-weight: 700; display: block; line-height: 1; margin-top: 2px; }
    .mvp-cart-sub .mvp-cart-badge { margin-left: 0; margin-right: 2px; }
        border-radius: 50%; min-width: 18px; height: 18px;
    .mvp-cart-text { font-size: 16px; font-weight: 700; line-height: 1; width: 100%; }
    .mvp-cart-stacked { display: flex; flex-direction: column; gap: 1px; }
    .mvp-cart-sub { font-size: 11px; font-weight: 700; display: block; line-height: 1; margin-top: 2px; }
    .mvp-cart-sub .mvp-cart-badge { margin-left: 0; margin-right: 2px; }
        display: inline-flex; align-items: center; justify-content: center;
    .mvp-cart-text { font-size: 16px; font-weight: 700; line-height: 1; width: 100%; }
    .mvp-cart-stacked { display: flex; flex-direction: column; gap: 1px; }
    .mvp-cart-sub { font-size: 11px; font-weight: 700; display: block; line-height: 1; margin-top: 2px; }
    .mvp-cart-sub .mvp-cart-badge { margin-left: 0; margin-right: 2px; }
        margin-left: 4px; padding: 0 4px;
    .mvp-cart-text { font-size: 16px; font-weight: 700; line-height: 1; width: 100%; }
    .mvp-cart-stacked { display: flex; flex-direction: column; gap: 1px; }
    .mvp-cart-sub { font-size: 11px; font-weight: 700; display: block; line-height: 1; margin-top: 2px; }
    .mvp-cart-sub .mvp-cart-badge { margin-left: 0; margin-right: 2px; }
    }
    .mvp-cart-text { font-size: 16px; font-weight: 700; line-height: 1; width: 100%; }
    .mvp-cart-stacked { display: flex; flex-direction: column; gap: 1px; }
    .mvp-cart-sub { font-size: 11px; font-weight: 700; display: block; line-height: 1; margin-top: 2px; }
    .mvp-cart-sub .mvp-cart-badge { margin-left: 0; margin-right: 2px; }

    /* ── WooCommerce Add to Cart + View Cart buttons — site red ── */
    .woocommerce a.added_to_cart,
    .woocommerce a.button.wc-forward {
        background-color: #BF3617 !important;
        color: #fff !important;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: 600;
        text-decoration: none;
    }
    .woocommerce a.added_to_cart:hover,
    .woocommerce a.button.wc-forward:hover {
        background-color: #a02e13 !important;
    }
    .woocommerce-message.mvp-cart-notice {
        background: #f7f6f7;
        border-top: 3px solid #BF3617; border-bottom: 1px solid #e0e0e0;
        padding: 14px 20px;
        margin: 0 0 20px;
        font-size: 14px;
        color: #333;
        line-height: 1.6;
        overflow: hidden;
    }
    .woocommerce ul.products li.product .button.add_to_cart_button {
        color: #BF3617 !important;
    }
    .woocommerce ul.products li.product .button.add_to_cart_button:hover {
        color: #a02e13 !important;
    }
    /* ── WooCommerce Blocks buttons (Cart, Checkout, Place Order) — site red ── */
    .wc-block-cart__submit-button,
    .wc-block-components-button.contained,
    .wp-element-button.wc-block-components-button,
    .wc-block-components-checkout-place-order-button,
    .wc-block-checkout__actions_row .wc-block-components-button,
    .wc-block-components-totals-coupon__button {
        background-color: #BF3617 !important;
        color: #fff !important;
        border: none !important;
    }
    .wc-block-cart__submit-button:hover,
    .wc-block-components-button.contained:hover,
    .wp-element-button.wc-block-components-button:hover,
    .wc-block-components-checkout-place-order-button:hover {
        background-color: #a02e13 !important;
    }
    /* Return to cart link */
    .wc-block-components-checkout-return-to-cart-button {
        color: #BF3617 !important;
    }
    .wc-block-components-checkout-return-to-cart-button:hover {
    /* ── Worldpay payment form fix for WooCommerce Blocks ── */
    .wc-block-components-radio-control-accordion-content iframe {
        height: 44px !important;
        max-height: 44px !important;
    }
    .wc-block-components-radio-control-accordion-content .wc-block-gateway-input.field {
        height: auto !important;
        margin-bottom: 12px;
    }
    .wc-block-components-radio-control-accordion-content {
        padding: 16px !important;
    }
    #access_worldpay_checkout-card-number,
    #access_worldpay_checkout-card-expiry,
    #access_worldpay_checkout-card-cvc {
        border: 1px solid #ddd;
        border-radius: 4px;
        overflow: hidden;
        height: 44px !important;
    }
    #access_worldpay_checkout-card-expiry,
    #access_worldpay_checkout-card-cvc {
        display: inline-block;
        width: calc(50% - 8px) !important;
    }
    #access_worldpay_checkout-card-cvc { margin-left: 12px; }
    #access_worldpay_checkout-card-holder-name {
        width: 100% !important;
        height: 44px;
        padding: 0 12px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 14px;
        margin-top: 12px;
    }
        color: #a02e13 !important;
    /* ── Worldpay payment form fix for WooCommerce Blocks ── */
    .wc-block-components-radio-control-accordion-content iframe {
        height: 44px !important;
        max-height: 44px !important;
    }
    .wc-block-components-radio-control-accordion-content .wc-block-gateway-input.field {
        height: auto !important;
        margin-bottom: 12px;
    }
    .wc-block-components-radio-control-accordion-content {
        padding: 16px !important;
    }
    #access_worldpay_checkout-card-number,
    #access_worldpay_checkout-card-expiry,
    #access_worldpay_checkout-card-cvc {
        border: 1px solid #ddd;
        border-radius: 4px;
        overflow: hidden;
        height: 44px !important;
    }
    #access_worldpay_checkout-card-expiry,
    #access_worldpay_checkout-card-cvc {
        display: inline-block;
        width: calc(50% - 8px) !important;
    }
    #access_worldpay_checkout-card-cvc { margin-left: 12px; }
    #access_worldpay_checkout-card-holder-name {
        width: 100% !important;
        height: 44px;
        padding: 0 12px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 14px;
        margin-top: 12px;
    }
    }
    /* ── Worldpay payment form fix for WooCommerce Blocks ── */
    .wc-block-components-radio-control-accordion-content iframe {
        height: 44px !important;
        max-height: 44px !important;
    }
    .wc-block-components-radio-control-accordion-content .wc-block-gateway-input.field {
        height: auto !important;
        margin-bottom: 12px;
    }
    .wc-block-components-radio-control-accordion-content {
        padding: 16px !important;
    }
    #access_worldpay_checkout-card-number,
    #access_worldpay_checkout-card-expiry,
    #access_worldpay_checkout-card-cvc {
        border: 1px solid #ddd;
        border-radius: 4px;
        overflow: hidden;
        height: 44px !important;
    }
    #access_worldpay_checkout-card-expiry,
    #access_worldpay_checkout-card-cvc {
        display: inline-block;
        width: calc(50% - 8px) !important;
    }
    #access_worldpay_checkout-card-cvc { margin-left: 12px; }
    #access_worldpay_checkout-card-holder-name {
        width: 100% !important;
        height: 44px;
        padding: 0 12px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 14px;
        margin-top: 12px;
    }
    /* ── Pagination — site red for active/hover ── */
    .woocommerce nav.woocommerce-pagination ul li a:hover,
    .woocommerce nav.woocommerce-pagination ul li span.current,
    nav.woocommerce-pagination ul li a:hover,
    nav.woocommerce-pagination ul li span.current {
        background: #BF3617 !important;
        color: #fff !important;
        border-color: #BF3617 !important;
    }
    .woocommerce nav.woocommerce-pagination ul li a,
    nav.woocommerce-pagination ul li a {
        border-color: #BF3617 !important;
        color: #BF3617 !important;
    }
    /* ── Hide Archives, Categories sidebar widgets + default Mobex footer ── */
    .shop-bottom-widgets,
    #et-footer-default {
        display: none !important;
    }

    /* ── Single product page layout ── */
    body.single-product .summary.entry-summary {
        display: flex; flex-direction: column; min-height: 450px;
    }
    body.single-product .summary .product_title {
        margin-bottom: 10px; font-size: 24px; font-weight: 700;
    }
    body.single-product .summary .price {
        margin-top: 10px; margin-bottom: 20px; font-size: 1.8em;
    }
    body.single-product .summary form.cart {
        margin-top: 15px; margin-bottom: 20px;
    }
    /* Hide default WooCommerce meta (categories/tags) on product pages */
    body.single-product .product_meta {
        display: none !important;
    }
    /* Hide Callout/Qty text that appears after add to cart */
    body.single-product .summary .callout-field,
    body.single-product .summary p:has(> .callout),
    body.single-product .summary > p[style] {
        display: none !important;
    }
    /* Hide reviews tab */
    body.single-product .woocommerce-Reviews,
    body.single-product #tab-reviews,
    body.single-product li.reviews_tab {
        display: none !important;
    }
    /* Hide WooCommerce tabs - show description inline */
    body.single-product .woocommerce-tabs {
        display: none !important;
    }

    /* SKU / Part No / Weight meta row */
    .mvp-product-meta-info {
        margin-bottom: 15px; font-size: 14px; color: #666;
    }
    .mvp-product-meta-info .meta-label { color: #888; }
    .mvp-product-meta-info .meta-value { font-family: monospace; color: #333; font-weight: 600; }
    .mvp-product-meta-info .meta-sep { margin: 0 12px; color: #ccc; }

    /* Request a Price button */
    .mvp-price-request-text {
        font-size: 1.4em; font-weight: 600; color: #888; margin: 10px 0 5px;
    }
    .mvp-request-price-btn {
        display: inline-block; background: #F29F05; color: #fff; border: none;
        padding: 12px 28px; font-size: 15px; font-weight: 700; border-radius: 4px;
        cursor: pointer; text-transform: uppercase; letter-spacing: 0.5px;
        text-decoration: none; margin: 10px 0 15px;
    }
    .mvp-request-price-btn:hover { background: #F29F05; color: #fff; }

    /* Estimated Delivery */
    .mvp-delivery-time {
        margin: 15px 0; padding: 12px 15px;
        background: #fff8e6; border-radius: 6px; border-left: 4px solid #F29F05;
    }
    .mvp-delivery-time .delivery-label { font-weight: 600; color: #333; margin-right: 8px; }
    .mvp-delivery-time .delivery-value { color: #F29F05; font-weight: 600; }

    /* Compatible Vehicles */
    .mvp-vehicle-compat {
        margin-top: auto !important; padding: 15px;
        background: #f5f5f5; border-radius: 6px; border-left: 4px solid #F29F05;
    }
    .mvp-vehicle-compat h4 { margin: 0 0 10px; font-size: 0.95em; color: #333; font-weight: 600; }
    .mvp-vehicle-compat ul { margin: 0; padding: 0; list-style: none; }
    .mvp-vehicle-compat li {
        padding: 5px 0; border-bottom: 1px solid #e0e0e0; font-size: 0.9em;
    }
    .mvp-vehicle-compat li:last-child { border-bottom: none; }
    .mvp-vehicle-compat .v-name { font-weight: 600; color: #333; }
    .mvp-vehicle-compat .v-year { color: #666; margin-left: 5px; }
    .mvp-vehicle-compat .v-empty { color: #999; font-style: italic; font-size: 0.9em; }

    /* Hide related products */
    body.single-product .related.products {
        display: none !important;
    }

    /* Hide review form, post navigation (Previous/Next), and any stray borders between description and recently viewed */
    body.single-product #reviews,
    body.single-product #review_form_wrapper,
    body.single-product .woocommerce-Reviews,
    body.single-product #respond,
    body.single-product .comment-respond,
    body.single-product .storefront-product-pagination,
    body.single-product nav.post-navigation,
    body.single-product .product-navigation,
    body.single-product .mobex-product-navigation,
    body.single-product .product > .summary ~ hr,
    body.single-product .product > .summary ~ .clear {
        display: none !important;
    }
    /* Remove stray borders/margins/lines from hidden woo sections */
    body.single-product .woocommerce-tabs,
    body.single-product .related.products,
    body.single-product .up-sells,
    body.single-product .cross-sells {
        margin: 0 !important; padding: 0 !important; border: none !important;
        height: 0 !important; overflow: hidden !important;
    }
    /* Kill all hr and border lines between description and recently viewed */
    body.single-product div.product hr,
    body.single-product div.product > .clear,
    body.single-product .products-separator,
    body.single-product .product-separator {
        display: none !important;
    }
    body.single-product div.product > div:not(.mvp-product-description):not(.images):not(.summary):not(.mvp-vehicle-notice):not([class*="recently"]):not([class*="widget"]):not(.mvp-vehicle-compat) {
        border: none !important;
    }

    /* Product description section (below image/summary) */
    .mvp-product-description {
        padding: 25px 0; border-top: 1px solid #eee; margin-top: 20px;
        padding-bottom: 0; margin-bottom: 0;
        clear: both;
    }
    .mvp-product-description h3 {
        font-size: 18px; font-weight: 700; color: #333; margin: 0 0 12px;
    }
    .mvp-product-description p, .mvp-product-description div {
        font-size: 14px; color: #555; line-height: 1.7;
    }

    /* ── Hide orange vehicle filter bar (Model/Year/Engine/Transmission/Trim) ── */
    body:not(.home) .widget_product_vehicle_filter_widget,
    body:not(.home) .product-vehicle-filter,
    body:not(.home) .vehicle-filter-mobile-toggle {
        display: none !important;
    }

    /* ── "Viewing parts for" bar — red background ── */
    .mvp-vehicle-notice {
        background: #BF3617 !important;
    }
    .mvp-vehicle-notice a {
        color: #fff !important;
    }
    /* Hide "Viewing parts for" bar on cart, checkout, and account pages */
    body.woocommerce-cart .mvp-vehicle-notice,
    body.woocommerce-checkout .mvp-vehicle-notice,
    body.woocommerce-account .mvp-vehicle-notice {
        display: none !important;
    }

    /* ── Why Use Us ── */
    .mvp-why-us {
        background: #fff;
        padding: 20px 20px 25px;
        text-align: center; line-height: 48px;
    }
    .mvp-why-us h2 { font-size: 22px; font-weight: 700; color: #333; margin: 0 0 16px; }
    .mvp-why-grid {
        display: flex; flex-wrap: nowrap; justify-content: center;
        gap: 20px; max-width: 1100px; margin: 0 auto;
    }
    .mvp-why-card {
        background: #fff; border-radius: 8px; padding: 18px 14px 16px;
        flex: 1 1 0; max-width: 170px; text-align: center; line-height: 48px;
        transition: transform 0.3s, box-shadow 0.3s;
    }
    .mvp-why-card:hover { transform: translateY(-4px); box-shadow: 0 6px 20px rgba(0,0,0,0.08); }
    .mvp-why-icon { width: 48px; height: 48px; margin: 0 auto 10px; display: flex; align-items: center; justify-content: center; }
    .mvp-why-icon svg { width: 40px; height: 40px; fill: none; stroke: #034C8C; stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round; }
    .mvp-why-card h3 { font-size: 13px; font-weight: 700; color: #333; margin: 0 0 6px; }
    .mvp-why-card p { font-size: 11px; color: #888; line-height: 1.4; margin: 0; }
    @media (max-width: 1024px) {
        .mvp-why-grid { flex-wrap: wrap; gap: 16px; }
        .mvp-why-card { flex: 1 1 200px; max-width: 30%; padding: 20px 16px 18px; }
    }
    @media (max-width: 768px) {
        .mvp-why-us { padding: 25px 20px 30px; }
        .mvp-why-grid { flex-wrap: wrap; gap: 16px; }
        .mvp-why-card { flex: 1 1 200px; max-width: 45%; padding: 20px 16px 18px; }
        .mvp-why-card h3 { font-size: 14px; }
        .mvp-why-card p { font-size: 12px; line-height: 1.5; }
    }
    @media (max-width: 480px) {
        .mvp-why-card { flex: 1 1 130px; max-width: 45%; padding: 14px 10px 12px; }
    }

    /* ── Custom Footer ── */
    .mvp-footer * { box-sizing: border-box; }
    .mvp-footer {
        background: #1a1a2e; color: #ccc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 14px; line-height: 1.7; padding: 0; margin: 0; width: 100%;
    }
    .mvp-footer-main {
        max-width: 1300px; margin: 0 auto; padding: 50px 30px 40px;
        display: grid; grid-template-columns: 1.4fr 1fr 1fr 1fr 1fr 1fr; gap: 30px;
    }
    .mvp-footer-col h4 {
        color: #fff; font-size: 16px; font-weight: 600; margin: 0 0 18px 0;
        padding-bottom: 12px; border-bottom: 2px solid #F29F05;
        text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap;
    }
    .mvp-footer-col ul { list-style: none; margin: 0; padding: 0; }
    .mvp-footer-col ul li { margin-bottom: 8px; }
    .mvp-footer-col ul li a { color: #ccc; text-decoration: none; transition: color 0.2s ease; }
    .mvp-footer-col ul li a:hover { color: #F29F05; }
    .mvp-footer-company-name { color: #fff; font-size: 20px; font-weight: 700; margin: 0 0 4px 0; }
    .mvp-footer-trading { font-size: 12px; color: #999; margin-bottom: 16px; }
    .mvp-footer-contact { margin-bottom: 16px; }
    .mvp-footer-contact p { margin: 0 0 6px 0; color: #ccc; font-size: 13px; line-height: 1.6; }
    .mvp-footer-contact a { color: #F29F05; text-decoration: none; }
    .mvp-footer-contact a:hover { color: #fff; }
    .mvp-footer-phone { font-size: 16px !important; font-weight: 600; color: #fff !important; }
    .mvp-footer-reg { font-size: 12px; color: #888; margin-bottom: 16px; }
    .mvp-footer-reg p { margin: 0 0 2px 0; }
    .mvp-footer-payments { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
    .mvp-footer-payments .pay-icon {
        background: #fff; color: #333; border-radius: 4px; padding: 4px 10px;
        font-size: 11px; font-weight: 700; letter-spacing: 0.3px;
        display: inline-flex; align-items: center; height: 28px;
    }
    .mvp-footer-bottom { border-top: 1px solid #2a2a3e; background: #151525; }
    .mvp-footer-bottom-inner {
        max-width: 1300px; margin: 0 auto; padding: 18px 30px;
        display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;
    }
    .mvp-footer-copyright { color: #888; font-size: 13px; margin: 0; }
    .mvp-footer-bottom-links { display: flex; gap: 8px; align-items: center; font-size: 13px; }
    .mvp-footer-bottom-links a { color: #888; text-decoration: none; transition: color 0.2s ease; }
    .mvp-footer-bottom-links a:hover { color: #F29F05; }
    .mvp-footer-bottom-links .sep { color: #555; }
    @media (max-width: 1024px) {
        .mvp-footer-main { grid-template-columns: 1fr 1fr; gap: 24px 30px; padding: 40px 24px 30px; }
        .mvp-footer-col:first-child { grid-column: 1 / -1; }
    }
    @media (max-width: 768px) {
        .mvp-footer-main { grid-template-columns: 1fr; gap: 20px; padding: 30px 20px 24px; }
        .mvp-footer-bottom-inner { flex-direction: column; text-align: center; line-height: 48px; padding: 14px 20px; }
    }

    /* ── Responsive: hide custom header on mobile, show default ── */
    @media (max-width: 1024px) {
        .mvp-hdr { display: none !important; }
        #et-desktop-8543 { display: none !important; background: #F29F05 !important; }
        #et-desktop-8543 .header-logo .logo { visibility: hidden; width: 0; height: 0; position: absolute; }
        #et-desktop-8543 .header-logo {
            display: block;
            background-image: url('<?php echo esc_url( $logo_url ); ?>');
            background-repeat: no-repeat; background-size: contain;
            background-position: center left;
            width: 180px; height: 40px; min-width: 180px;
        }
        #et-desktop-8543 .header-menu > li > a,
        #et-desktop-8543 .header-menu > li > a .txt { color: #fff !important; }
    }
    </style>
    <?php
}

// ============================================================
// 0b. INJECT 3-ROW HEADER via wp_footer JS
// ============================================================
add_action( 'wp_footer', 'mvp_sitewide_header_inject', 1 );
function mvp_sitewide_header_inject() {
    $home       = esc_url( home_url( '/' ) );
    $shop       = esc_url( home_url( '/shop/' ) );
    $my_account = esc_url( home_url( '/my-account/' ) );
    $contact    = esc_url( home_url( '/contact-us/' ) );
    $compare    = esc_url( home_url( '/compare' ) );
    $cart       = esc_url( home_url( '/cart/' ) );
    $cart_count = function_exists("WC") && WC()->cart ? WC()->cart->get_cart_contents_count() : 0;
    $logo_url   = esc_url( content_url( '/uploads/mpd-logo-original.webp' ) );
    $ajax_url   = esc_url( admin_url( 'admin-ajax.php' ) );

    // Read nav menu items from the existing Mobex header menu (slug: header-menu-1, term_id: 505)
    $menu_items = wp_get_nav_menu_items( 'header-menu-1' );
    $nav_html = '';
    $vehicle_cats = get_terms( array( 'taxonomy' => 'product_cat', 'parent' => 3590, 'hide_empty' => false ) );
    if ( $menu_items ) {
        foreach ( $menu_items as $item ) {
            if ( $item->menu_item_parent != 0 ) continue;
            $is_vehicles = ( strpos( strtolower( $item->title ), 'vehicle' ) !== false );
            if ( $is_vehicles && ! is_wp_error( $vehicle_cats ) && count( $vehicle_cats ) > 0 ) {
                $nav_html .= '<li class="mvp-has-dropdown"><a href="' . esc_url( $item->url ) . '">' . esc_html( $item->title ) . ' <svg width="10" height="6" viewBox="0 0 10 6" style="margin-left:4px;vertical-align:middle;"><path d="M1 1l4 4 4-4" stroke="#fff" stroke-width="1.5" fill="none"/></svg></a>';
                $nav_html .= '<div class="mvp-dropdown mvp-mega" style="display:none;position:absolute;top:100%;left:-50px;z-index:9999;background:#D18A0C;width:340px;box-shadow:0 4px 20px rgba(0,0,0,0.15);border-radius:0 0 6px 6px;padding:12px 0;max-height:500px;overflow-y:auto;">';
                // Group vehicles by model family
                $groups = array();
                foreach ( $vehicle_cats as $vc ) {
                    $model = get_term_meta( $vc->term_id, 'vehicle_model', true );
                    $display = $model ? $model : $vc->name;
                    if ( preg_match( '/^((?:E |New )?(?:Deliver \d+|T\d+|A\d+|V\d+))/i', $display, $m ) ) {
                        $family = $m[1];
                    } else {
                        $family = 'Other';
                    }
                    if ( ! isset( $groups[$family] ) ) $groups[$family] = array();
                    $groups[$family][] = array( 'slug' => (get_term_meta( $vc->term_id, 'vehicle_slug', true ) ?: $vc->slug), 'name' => $display, 'img' => get_term_meta( $vc->term_id, 'vehicle_image', true ) );
                }
                ksort( $groups );
                foreach ( $groups as $family => $vehicles ) {
                    $nav_html .= '<div style="padding:6px 16px 2px;font-size:11px;font-weight:700;color:rgba(255,255,255,0.6);text-transform:uppercase;letter-spacing:0.5px;">' . esc_html( $family ) . '</div>';
                    foreach ( $vehicles as $v ) {
                        $link = home_url( '/vehicle/' . $v['slug'] . '/' );
                        $nav_html .= '<a href="' . esc_url( $link ) . '" style="display:flex;align-items:center;gap:10px;padding:5px 16px;color:#fff;font-size:13px;font-weight:500;text-decoration:none;white-space:nowrap;">';
                        if ( $v['img'] ) {
                            $nav_html .= '<img src="' . esc_url( $v['img'] ) . '" style="width:40px;height:26px;object-fit:contain;border-radius:2px;background:rgba(255,255,255,0.9);" alt="">';
                        }
                        $nav_html .= esc_html( $v['name'] ) . '</a>';
                    }
                }
                $nav_html .= '</div></li>';
            } elseif ( strpos( strtolower( $item->title ), 'vin' ) !== false ) {
                $nav_html .= '<li class="mvp-has-dropdown mvp-dd-vin"><a href="' . esc_url( $item->url ) . '">' . esc_html( $item->title ) . ' <svg width="10" height="6" viewBox="0 0 10 6" style="margin-left:4px;vertical-align:middle;"><path d="M1 1l4 4 4-4" stroke="#fff" stroke-width="1.5" fill="none"/></svg></a>';
                $nav_html .= '<div class="mvp-dropdown mvp-dd-search" style="display:none;position:absolute;top:100%;left:0;z-index:9999;background:#D18A0C;min-width:400px;box-shadow:0 4px 20px rgba(0,0,0,0.15);border-radius:0 0 6px 6px;padding:16px 20px;">';
                $nav_html .= '<p style="color:#fff;font-size:14px;font-weight:600;margin:0 0 8px;">Search by VIN Number</p>';
                $nav_html .= '<form class="mvp-dd-vin-form" style="display:flex;gap:8px;" action="' . home_url( '/vin-search-test/' ) . '">';
                $nav_html .= '<input type="text" name="vin" placeholder="Enter VIN number" style="flex:1;height:40px;padding:0 12px;border:none;border-radius:4px;font-size:14px;">';
                $nav_html .= '<button type="submit" style="height:40px;padding:0 20px;background:#BF3617;color:#fff;border:none;border-radius:4px;font-weight:600;cursor:pointer;">Search</button>';
                $nav_html .= '</form></div></li>';
            } elseif ( strpos( strtolower( $item->title ), 'registration' ) !== false ) {
                $nav_html .= '<li class="mvp-has-dropdown mvp-dd-reg"><a href="' . esc_url( $item->url ) . '">' . esc_html( $item->title ) . ' <svg width="10" height="6" viewBox="0 0 10 6" style="margin-left:4px;vertical-align:middle;"><path d="M1 1l4 4 4-4" stroke="#fff" stroke-width="1.5" fill="none"/></svg></a>';
                $nav_html .= '<div class="mvp-dropdown mvp-dd-search" style="display:none;position:absolute;top:100%;left:0;z-index:9999;background:#D18A0C;min-width:400px;box-shadow:0 4px 20px rgba(0,0,0,0.15);border-radius:0 0 6px 6px;padding:16px 20px;">';
                $nav_html .= '<p style="color:#fff;font-size:14px;font-weight:600;margin:0 0 8px;">Search by Registration</p>';
                $nav_html .= '<form class="mvp-dd-reg-form" style="display:flex;gap:8px;" action="' . home_url( '/registration-lookup/' ) . '">';
                $nav_html .= '<input type="text" name="reg" placeholder="e.g. AB12 CDE" maxlength="10" style="flex:1;height:40px;padding:0 12px;border:none;border-radius:4px;font-size:14px;text-transform:uppercase;">';
                $nav_html .= '<button type="submit" style="height:40px;padding:0 20px;background:#BF3617;color:#fff;border:none;border-radius:4px;font-weight:600;cursor:pointer;">Search</button>';
                $nav_html .= '</form></div></li>';
            } else {
                $nav_html .= '<li><a href="' . esc_url( $item->url ) . '">' . esc_html( $item->title ) . '</a></li>';
            }
        }
    }
    ?>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        var wrap = document.getElementById('wrap');
        if (!wrap) return;
        // Don't inject on small screens (mobile uses default header)

        var hdr = document.createElement('div');
        hdr.className = 'mvp-hdr';
        hdr.innerHTML = ''
        /* ── ROW 1: Utility ── */
        + '<div class="mvp-hdr-r1"><div class="mvp-hdr-wrap">'
        +   '<a href="<?php echo $contact; ?>" class="mvp-hdr-r1-ask">'
        +     '<svg viewBox="0 0 24 24"><path d="M12 1c-6.627 0-12 4.208-12 9.399 0 3.356 2.246 6.301 5.625 7.963-.225 2.254-1.365 3.576-1.389 3.601-.078.091-.101.218-.054.329.046.111.152.185.273.185 2.891 0 5.281-1.749 6.543-2.901.324.033.656.05.993.05 6.627 0 12-4.208 12-9.399-.009-5.218-5.382-9.227-11.991-9.227z"/></svg>'
        +     'Ask us a question?'
        +   '</a>'
        +   '<div class="mvp-hdr-r1-social">'
        +     '<span>Stay connected:</span>'
        +     '<a href="https://www.facebook.com/maxusvanpartsdirect" target="_blank" rel="noopener" title="Facebook"><svg viewBox="0 0 24 24"><path d="M18 2h-3a5 5 0 00-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 011-1h3z"/></svg></a>'
        +     '<a href="#" title="Instagram"><svg viewBox="0 0 24 24"><rect x="2" y="2" width="20" height="20" rx="5" ry="5" fill="none" stroke="#bbb" stroke-width="2"/><circle cx="12" cy="12" r="5" fill="none" stroke="#bbb" stroke-width="2"/><circle cx="17.5" cy="6.5" r="1.5" fill="#bbb"/></svg></a>'
        +     '<a href="#" title="LinkedIn"><svg viewBox="0 0 24 24"><path d="M16 8a6 6 0 016 6v7h-4v-7a2 2 0 00-4 0v7h-4v-7a6 6 0 016-6zM2 9h4v12H2zM4 6a2 2 0 100-4 2 2 0 000 4z"/></svg></a>'
        +     '<a href="#" title="Twitter"><svg viewBox="0 0 24 24"><path d="M23 3a10.9 10.9 0 01-3.14 1.53A4.48 4.48 0 0012 7.5v1A10.66 10.66 0 013 4s-4 9 5 13a11.64 11.64 0 01-7 2c9 5 20 0 20-11.5 0-.28-.03-.56-.08-.83A7.72 7.72 0 0023 3z"/></svg></a>'
        +     '<a href="#" title="YouTube"><svg viewBox="0 0 24 24"><path d="M22.54 6.42a2.78 2.78 0 00-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 00-1.94 2A29 29 0 001 11.75a29 29 0 00.46 5.33 2.78 2.78 0 001.94 2c1.72.46 8.6.46 8.6.46s6.88 0 8.6-.46a2.78 2.78 0 001.94-2 29 29 0 00.46-5.25 29 29 0 00-.46-5.33z"/><polygon points="9.75 15.02 15.5 11.75 9.75 8.48 9.75 15.02" fill="#fff"/></svg></a>'
        +   '</div>'
        +   '<div class="mvp-hdr-r1-login">'
        +     '<a href="<?php echo $my_account; ?>"><svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>Login</a>'
        +     '<div class="mvp-login-dd">'
        +       '<form action="<?php echo esc_url( wp_login_url( $my_account ) ); ?>" method="post">'
        +         '<input type="text" name="log" placeholder="Username" autocomplete="username">'
        +         '<input type="password" name="pwd" placeholder="Password" autocomplete="current-password">'
        +         '<button type="submit" class="mvp-login-btn">Log In</button>'
        +       '</form>'
        +       '<div class="mvp-login-links">'
        +         '<a href="<?php echo esc_url( wp_lostpassword_url() ); ?>">Forgot password?</a>'
        +         '<a href="<?php echo $my_account; ?>">Sign up</a>'
        +       '</div>'
        +     '</div>'
        +   '</div>'
        + '</div></div>'

        /* ── ROW 2: Logo + search + phone ── */
        + '<div class="mvp-hdr-r2"><div class="mvp-hdr-wrap">'
        +   '<a href="<?php echo $home; ?>" class="mvp-hdr-r2-logo"><img src="<?php echo $logo_url; ?>" alt="Maxus Parts Direct"></a>'
        +   '<a href="<?php echo $home; ?>" class="mvp-hdr-r2-home">Home</a>'
        +   '<div class="mvp-hdr-r2-search">'
        +     '<input type="text" placeholder="Enter a keyword or product SKU" id="mvp-hdr-search-input">'
        +     '<button type="button" onclick="var v=document.getElementById(\'mvp-hdr-search-input\').value;if(v)window.location.href=\'<?php echo $shop; ?>?s=\'+encodeURIComponent(v)+\'&amp;post_type=product\';"></button>'
        +   '</div>'
        +   '<a href="tel:01953528800" class="mvp-hdr-r2-phone">'
        +     '<svg viewBox="0 0 24 24"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6A19.79 19.79 0 012.12 4.18 2 2 0 014.11 2h3a2 2 0 012 1.72c.13.81.37 1.6.65 2.37a2 2 0 01-.45 2.11L8.09 9.42a16 16 0 006 6l1.22-1.22a2 2 0 012.11-.45c.77.28 1.56.52 2.37.65a2 2 0 011.72 2.03z"/></svg>'
        +     '<span class="mvp-hdr-r2-phone-text"><span class="mvp-hdr-r2-phone-num">01953 528300</span><span class="mvp-hdr-r2-phone-sub">Call us between 9 AM - 5 PM</span></span>'
        +   '</a>'
        + '</div></div>'

        /* ── ROW 3: Nav + actions ── */
        + '<div class="mvp-hdr-r3"><div class="mvp-hdr-wrap">'
        +   '<ul class="mvp-hdr-r3-nav"><?php echo $nav_html; ?></ul>'
        +   '<div class="mvp-hdr-r3-actions">'
        +     '<a href="<?php echo $compare; ?>" class="mvp-r3-icon"><svg viewBox="0 0 24 24"><path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2v-4M9 21H5a2 2 0 01-2-2v-4" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg></a>'
        +     '<a href="<?php echo $cart; ?>" class="mvp-r3-cart"><svg viewBox="0 0 24 24"><circle cx="9" cy="21" r="1" fill="#fff"/><circle cx="20" cy="21" r="1" fill="#fff"/><path d="M1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 002-1.61L23 6H6" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg><span class="mvp-cart-stacked"><span class="mvp-cart-text">Cart</span><span class="mvp-cart-sub"><span class="mvp-cart-badge"><?php echo $cart_count; ?></span>items</span></span></a>'
        +     '<a href="#" class="mvp-r3-myvehicle">My Vehicle</a>'
        +   '</div>'
        + '</div></div>';

        wrap.insertBefore(hdr, wrap.firstChild);

        // Logo hiding removed - using original logo

        // Enter key on search
        document.getElementById('mvp-hdr-search-input').addEventListener('keydown', function(e) {
            if (e.key === 'Enter') { e.preventDefault(); this.nextElementSibling.click(); }
        });
        // Dropdown hover show/hide
        // Dropdown hover show/hide for ALL dropdown menu items
        document.querySelectorAll(".mvp-has-dropdown").forEach(function(ddParent) {
            var ddMenu = ddParent.querySelector(".mvp-dropdown");
            if (!ddMenu) return;
            ddParent.style.position = "relative";
            ddParent.addEventListener("mouseenter", function() { ddMenu.style.display = "block"; });
            ddParent.addEventListener("mouseleave", function() { ddMenu.style.display = "none"; });
            ddMenu.querySelectorAll("a:not([type=submit])").forEach(function(a) {
                a.addEventListener("mouseenter", function() { a.style.background = "rgba(255,255,255,0.15)"; });
                a.addEventListener("mouseleave", function() { a.style.background = ""; });
            });
        });
        var cartObserver = new MutationObserver(function(mutations) {
            mutations.forEach(function(m) {
                m.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1 && node.classList && node.classList.contains("added_to_cart")) {
                        // Badge update
                        var badge = document.querySelector(".mvp-cart-badge");
                        if (badge) badge.textContent = parseInt(badge.textContent || "0") + 1;
                        // Show notification bar
                        var existing = document.querySelector(".mvp-cart-notice");
                        if (existing) existing.remove();
                        var wrapper = document.querySelector(".mvp-cart-notice-area"); if (!wrapper) { var contentArea = document.querySelector(".entry-content, .site-content, .woocommerce, #content, main, #wrap"); if (contentArea) { wrapper = document.createElement("div"); wrapper.className = "mvp-cart-notice-area"; wrapper.style.cssText = "max-width:1320px;margin:0 auto;padding:0 10px;"; var header = document.querySelector(".mvp-hdr-r3, .et-desktop"); if (header) { header.parentNode.insertBefore(wrapper, header.nextSibling); } else { contentArea.insertBefore(wrapper, contentArea.firstChild); } } }
                        if (wrapper) {
                            var productName = "";
                            var card = node.closest("li.product");
                            if (card) {
                                var title = card.querySelector(".woocommerce-loop-product__title, h2, h3");
                                if (title) productName = title.textContent.trim();
                            }
                            var msg = document.createElement("div");
                            msg.className = "woocommerce-message mvp-cart-notice";
                            msg.setAttribute("role", "alert");
                            var linkHtml = '<a href="/cart/" class="button wc-forward" style="background:#BF3617;color:#fff;padding:8px 18px;border-radius:4px;text-decoration:none;font-weight:600;float:right;">View cart</a>';
                            msg.innerHTML = linkHtml + (productName ? "u201c" + productName + "u201d has been added to your cart." : "Product added to your cart.");
                            wrapper.innerHTML = "";
                            wrapper.appendChild(msg);
                            window.scrollTo({top: 0, behavior: "smooth"});
                        }
                    }
                });
            });
        });
        cartObserver.observe(document.body, {childList: true, subtree: true});
    });
    </script>
    <script>
    /* Move WooCommerce "added to cart" notice to top of page */
    (function() {
        function moveNotice() {
            var wcNotice = document.querySelector(".woocommerce-notices-wrapper .woocommerce-message");
            if (!wcNotice) return;
            if (document.querySelector(".mvp-cart-notice-area")) return;
            var noticeArea = document.createElement("div");
            noticeArea.className = "mvp-cart-notice-area";
            noticeArea.style.cssText = "max-width:1320px;margin:0 auto;padding:10px 10px 0;";
            wcNotice.classList.add("mvp-cart-notice");
            noticeArea.appendChild(wcNotice);
            var wrapEl = document.getElementById("wrap");
            if (wrapEl && wrapEl.children.length > 1) {
                wrapEl.insertBefore(noticeArea, wrapEl.children[1]);
            }
        }
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", moveNotice);
        } else {
            setTimeout(moveNotice, 0);
        }
    })();
    </script>
    <script>
    /* Fix Why Use Us height on mobile */
    (function() {
        if (window.innerWidth > 1024) return;
        function fixWhyUs() {
            var section = document.querySelector("[data-id=\"8b07793\"]");
            if (!section) return;
            section.style.height = "auto";
            section.style.maxHeight = "none";
            section.style.overflow = "visible";
            var inner = section.querySelector(".e-con-inner");
            if (inner) {
                inner.style.height = "auto";
                inner.style.display = "block";
            }
            section.querySelectorAll(".e-child, .e-con").forEach(function(el) {
                el.style.width = "100%";
                el.style.maxWidth = "100%";
                el.style.flexBasis = "100%";
                el.style.height = "auto";
            });
        }
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", fixWhyUs);
        } else {
            setTimeout(fixWhyUs, 100);
        }
    })();
    </script>
    <?php
}


// ============================================================
// 1. HOMEPAGE CSS — Hide unwanted sections & inject styles
// ============================================================
add_action( 'wp_head', 'mvp_facelift_css', 999 );
function mvp_facelift_css() {
    if ( ! is_front_page() && ! is_home() ) return;
    ?>
    <style id="mvp-facelift-css">
    /* === HIDE: RevSlider widget (inside elementor section a40da3e) === */
    body.home .elementor-element-a40da3e,
    body.home sr7-module,
    body.home .wp-block-themepunch-revslider,
    body.home .elementor-widget-slider_revolution {
        display: none !important;
    }

    /* === HIDE: Department category icons row === */
    body.home .elementor-element-099500a {
        display: none !important;
    }

    /* === HIDE: Featured manufacturers heading + logos === */
    body.home .elementor-element-9f85e6f,
    body.home .elementor-element-e540d81 {
        display: none !important;
    }

    /* === HIDE: Promo banners (Engine Oil, Tools, Batteries) === */
    body.home .elementor-element-23763df {
        display: none !important;
    }

    /* === HIDE: "Know what you pay for" section === */
    body.home .elementor-element-20e40c9 {
        display: none !important;
    }

    /* === HIDE: "Car repairs have never been so easy" section === */
    body.home .elementor-element-7033a3b {
        display: none !important;
    }

    /* === HIDE: Empty spacer section === */
    body.home .elementor-element-9e19027 {
        display: none !important;
    }

    /* === HIDE: Original 6-dropdown vehicle filter bar === */
    body.home .elementor-element-3e78bee {
        display: block !important;
    }

    /* ── Hero Banner ── */
    #mvp-facelift-hero-area { padding: 24px 0; }
    .mvp-hero {
        position: relative;
        max-width: 1320px;
        margin: 0 auto;
        height: 348px;
        border-radius: 6px;
        background-image: url('https://shane.maxusvanparts.co.uk/wp-content/uploads/resized.jpg');
        background-size: cover;
        background-position: center;
        display: flex;
        align-items: center;
        overflow: hidden;
        margin-bottom: 0;
    }
    .mvp-hero-content {
        position: relative;
        z-index: 2;
        max-width: none;
        padding: 60px 120px;
        text-align: left;
    }
    .mvp-hero-content h1 { white-space: nowrap;
        font-family: 'Oswald', sans-serif;
        font-size: 56px;
        font-weight: 700;
        color: #fff;
        line-height: 1;
        margin: 0 0 8px;
        text-transform: uppercase;
        letter-spacing: 0px;
        text-shadow: 1px 1px 1px rgba(0,0,0,0.25);
    }
    .mvp-hero-content h1 .hero-sub {
        display: block;
        font-size: 32px;
        line-height: 1;
        margin-top: 4px;
    }
    .mvp-hero-content p {
        font-family: 'Inter', sans-serif;
        font-size: 18px;
        font-weight: 500;
        color: #fff;
        line-height: 1.35;
        margin: 16px 0 24px;
        max-width: 520px;
    }
    .mvp-hero-btn {
        display: inline-block;
        padding: 12px 32px;
        background: #F29F05;
        color: #fff;
        font-size: 15px;
        font-weight: 600;
        text-decoration: none;
        border-radius: 4px;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .mvp-hero-btn:hover {
        background: #e08e00;
        color: #fff;
    }
    @media (max-width: 768px) {
        .mvp-hero { height: 300px; }
        .mvp-hero-content { padding: 30px 30px; }
        .mvp-hero-content h1 { white-space: nowrap; font-size: 42px; }
        .mvp-hero-content h1 .hero-sub { font-size: 26px; }
        .mvp-hero-content p { font-size: 15px; margin: 12px 0 18px; }
        .mvp-hero-btn { padding: 10px 24px; font-size: 13px; }
    }
    @media (max-width: 480px) {
        .mvp-hero { height: 220px; }
        .mvp-hero-content { padding: 20px 20px; }
        .mvp-hero-content h1 { white-space: nowrap; font-size: 28px; }
        .mvp-hero-content h1 .hero-sub { font-size: 18px; }
        .mvp-hero-content p { font-size: 13px; margin: 8px 0 12px; }
    }

    /* ── Vehicle Carousel ── */
    .mvp-vehicles {
        background: #fff;
        padding: 25px 0 20px;
        text-align: center; line-height: 48px;
    }
    .mvp-carousel-wrapper {
        position: relative;
        max-width: 1400px;
        margin: 0 auto;
        padding: 0 60px;
    }
    .mvp-carousel-track {
        display: flex;
        gap: 8px;
        overflow-x: auto;
        scroll-behavior: smooth;
        scrollbar-width: none;
        -ms-overflow-style: none;
        padding: 10px 5px;
    }
    .mvp-carousel-track::-webkit-scrollbar { display: none; }
    .mvp-vehicle-card {
        flex: 0 0 140px;
        text-align: center; line-height: 48px;
        text-decoration: none;
        color: #333;
        padding: 5px;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .mvp-vehicle-card:hover { transform: translateY(-3px); }
    .mvp-vehicle-circle {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        border: 3px solid #ccc;
        background: #f8f8f8;
        margin: 0 auto 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    .mvp-vehicle-circle img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: 50%;
    }
    .mvp-vehicle-card:hover .mvp-vehicle-circle {
        border-color: #999;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
    }
    .mvp-vehicle-card:hover .mvp-vehicle-name { color: #F29F05; }
    .mvp-vehicle-name {
        font-weight: 600;
        font-size: 12px;
        margin-bottom: 2px;
        color: #333;
        transition: color 0.3s ease;
        line-height: 1.2;
    }
    .mvp-vehicle-years {
        font-size: 11px;
        color: #999;
    }
    .mvp-carousel-nav {
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        width: 30px;
        height: 40px;
        background: transparent;
        color: #333;
        border: none;
        cursor: pointer;
        font-size: 24px;
        z-index: 10;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: color 0.3s;
    }
    .mvp-carousel-nav:hover { color: #F29F05; }
    .mvp-carousel-nav.prev { left: 15px; }
    .mvp-carousel-nav.next { right: 15px; }
    @media (max-width: 767px) {
        .mvp-carousel-wrapper { padding: 0 40px; }
        .mvp-carousel-track { gap: 6px; }
        .mvp-vehicle-card { flex: 0 0 100px; }
        .mvp-vehicle-circle { width: 90px; height: 90px; }
        .mvp-vehicle-name { font-size: 10px; }
        .mvp-carousel-nav { width: 24px; height: 30px; font-size: 20px; }
        .mvp-carousel-nav.prev { left: 10px; }
        .mvp-carousel-nav.next { right: 10px; }
    }

    /* ── Why Use Us ── */
    .mvp-why-us {
        background: #fff;
        padding: 20px 20px 25px;
        text-align: center; line-height: 48px;
    }
    .mvp-why-us h2 {
        font-size: 22px;
        font-weight: 700;
        color: #333;
        margin: 0 0 16px;
    }
    .mvp-why-grid {
        display: flex;
        flex-wrap: nowrap;
        justify-content: center;
        gap: 20px;
        max-width: 1100px;
        margin: 0 auto;
    }
    .mvp-why-card {
        background: #fff;
        border-radius: 8px;
        padding: 18px 14px 16px;
        flex: 1 1 0;
        max-width: 170px;
        text-align: center; line-height: 48px;
        transition: transform 0.3s, box-shadow 0.3s;
    }
    .mvp-why-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
    }
    .mvp-why-icon {
        width: 48px;
        height: 48px;
        margin: 0 auto 10px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .mvp-why-icon svg {
        width: 40px;
        height: 40px;
        fill: none;
        stroke: #034C8C;
        stroke-width: 1.5;
        stroke-linecap: round;
        stroke-linejoin: round;
    }
    .mvp-why-card h3 {
        font-size: 13px;
        font-weight: 700;
        color: #333;
        margin: 0 0 6px;
    }
    .mvp-why-card p {
        font-size: 11px;
        color: #888;
        line-height: 1.4;
        margin: 0;
    }
    @media (max-width: 1024px) {
        .mvp-why-grid { flex-wrap: wrap; gap: 16px; }
        .mvp-why-card { flex: 1 1 200px; max-width: 30%; padding: 20px 16px 18px; }
    }
    @media (max-width: 768px) {
        .mvp-why-us { padding: 25px 20px 30px; }
        .mvp-why-grid { flex-wrap: wrap; gap: 16px; }
        .mvp-why-card { flex: 1 1 200px; max-width: 45%; padding: 20px 16px 18px; }
        .mvp-why-card h3 { font-size: 14px; }
        .mvp-why-card p { font-size: 12px; line-height: 1.5; }
    }
    @media (max-width: 480px) {
        .mvp-why-card { flex: 1 1 130px; max-width: 45%; padding: 14px 10px 12px; }
    }

    /* ── Custom Footer ── */
    .mvp-footer * { box-sizing: border-box; }
    .mvp-footer {
        background: #1a1a2e;
        color: #ccc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 14px;
        line-height: 1.7;
        padding: 0;
        margin: 0;
        width: 100%;
    }
    .mvp-footer-main {
        max-width: 1300px;
        margin: 0 auto;
        padding: 50px 30px 40px;
        display: grid;
        grid-template-columns: 1.4fr 1fr 1fr 1fr 1fr 1fr;
        gap: 30px;
    }
    .mvp-footer-col h4 {
        color: #fff;
        font-size: 16px;
        font-weight: 600;
        margin: 0 0 18px 0;
        padding-bottom: 12px;
        border-bottom: 2px solid #F29F05;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        white-space: nowrap;
    }
    .mvp-footer-col ul { list-style: none; margin: 0; padding: 0; }
    .mvp-footer-col ul li { margin-bottom: 8px; }
    .mvp-footer-col ul li a {
        color: #ccc;
        text-decoration: none;
        transition: color 0.2s ease;
    }
    .mvp-footer-col ul li a:hover { color: #F29F05; }
    .mvp-footer-company-name {
        color: #fff;
        font-size: 20px;
        font-weight: 700;
        margin: 0 0 4px 0;
    }
    .mvp-footer-trading {
        font-size: 12px;
        color: #999;
        margin-bottom: 16px;
    }
    .mvp-footer-contact { margin-bottom: 16px; }
    .mvp-footer-contact p { margin: 0 0 6px 0; color: #ccc; font-size: 13px; line-height: 1.6; }
    .mvp-footer-contact a { color: #F29F05; text-decoration: none; }
    .mvp-footer-contact a:hover { color: #fff; }
    .mvp-footer-phone { font-size: 16px !important; font-weight: 600; color: #fff !important; }
    .mvp-footer-reg { font-size: 12px; color: #888; margin-bottom: 16px; }
    .mvp-footer-reg p { margin: 0 0 2px 0; }
    .mvp-footer-payments { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
    .mvp-footer-payments .pay-icon {
        background: #fff;
        color: #333;
        border-radius: 4px;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.3px;
        display: inline-flex;
        align-items: center;
        height: 28px;
    }
    .mvp-footer-bottom {
        border-top: 1px solid #2a2a3e;
        background: #151525;
    }
    .mvp-footer-bottom-inner {
        max-width: 1300px;
        margin: 0 auto;
        padding: 18px 30px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
    }
    .mvp-footer-copyright { color: #888; font-size: 13px; margin: 0; }
    .mvp-footer-bottom-links { display: flex; gap: 8px; align-items: center; font-size: 13px; }
    .mvp-footer-bottom-links a { color: #888; text-decoration: none; transition: color 0.2s ease; }
    .mvp-footer-bottom-links a:hover { color: #F29F05; }
    .mvp-footer-bottom-links .sep { color: #555; }
    @media (max-width: 1024px) {
        .mvp-footer-main { grid-template-columns: 1fr 1fr; gap: 24px 30px; padding: 40px 24px 30px; }
        .mvp-footer-col:first-child { grid-column: 1 / -1; }
    }
    @media (max-width: 768px) {
        .mvp-footer-main { grid-template-columns: 1fr; gap: 20px; padding: 30px 20px 24px; }
        .mvp-footer-bottom-inner { flex-direction: column; text-align: center; line-height: 48px; padding: 14px 20px; }
    }

    
    /* === Why Use Us icon mask-images (Elementor can't resolve media IDs) === */
    .elementor-element-c73c57f > .elementor-widget-container > .et-icon-box .icon:before {
        mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/shield-check.svg) !important;
        -webkit-mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/shield-check.svg) !important;
    }
    .elementor-element-bd73a19 > .elementor-widget-container > .et-icon-box .icon:before {
        mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/headset.svg) !important;
        -webkit-mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/headset.svg) !important;
    }
    .elementor-element-a272fa2 > .elementor-widget-container > .et-icon-box .icon:before {
        mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/toolbox.svg) !important;
        -webkit-mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/toolbox.svg) !important;
    }
    .elementor-element-99bbea6 > .elementor-widget-container > .et-icon-box .icon:before {
        mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/clipboard-check.svg) !important;
        -webkit-mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/clipboard-check.svg) !important;
    }
    .elementor-element-4103e18 > .elementor-widget-container > .et-icon-box .icon:before {
        mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/telephone-call.svg) !important;
        -webkit-mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/telephone-call.svg) !important;
    }
    .elementor-element-d981530 > .elementor-widget-container > .et-icon-box .icon:before {
        mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/shipping.svg) !important;
        -webkit-mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/shipping.svg) !important;
    }
    /* === Product loop tweaks to match target === */
    body.home ul.products .product .button,
    body.home ul.products .product .added_to_cart {
        background-color: transparent !important;
        color: #888 !important;
        box-shadow: none !important;
    }
    body.home ul.products .product .button:hover,
    body.home ul.products .product .added_to_cart:hover {
        background-color: transparent !important;
        color: #333 !important;
    }
    body.home ul.products .product .button:before,
    body.home ul.products .product .button:after,
    body.home ul.products .product .added_to_cart:before,
    body.home ul.products .product .added_to_cart:after {
        display: none !important;
    }
    body.home ul.products .product .star-rating-wrap {
        display: none !important;
    }

    /* === Hide extra Elementor sections === */
    body.home .elementor-element-1eaa1c9, body.home .elementor-element-f5b0776,
    body.home .elementor-element-1fb0185, body.home .elementor-element-b14d001,
    body.home .elementor-element-09f258e, body.home .elementor-element-1b38164,
    body.home .elementor-element-1af2051, body.home .elementor-element-4a31403,
    body.home .elementor-element-25b37be, body.home .elementor-element-099500a { display: none !important; }
    body.home .mvp-search-bar-wrap { display: block !important; }

    /* === Hide small custom Why Us (keep bigger Elementor version) === */
    .mvp-why-us { display: none !important; }

    /* === Vehicle filter bar (DESKTOP ONLY) === */
    @media (min-width: 1025px) {
    body.home .elementor-element-3e78bee, body.home .elementor-element-3e78bee.breakpoint-767 { display: none !important; }
    body.home .elementor-element-3e78bee .vehicle-filter-mobile-toggle { display: none !important; }
    body.home .elementor-element-3e78bee form.product-vehicle-filter { display: flex !important; visibility: visible !important; }
    body.home .elementor-element-3e78bee .atts { display: flex !important; flex: 0 0 336px !important; gap: 8px !important; height: 36px !important; align-items: center !important; }
    body.home .elementor-element-3e78bee .vf-item { margin: 0 !important; height: 36px !important; }
    body.home .elementor-element-3e78bee .vf-item.model { flex: 0 0 208px !important; }
    body.home .elementor-element-3e78bee .vf-item.year { flex: 0 0 120px !important; }
    body.home .elementor-element-3e78bee .last { flex: 1 !important; display: flex !important; align-items: center !important; }
    body.home .elementor-element-3e78bee .vin { display: flex !important; align-items: center !important; }
    body.home .elementor-element-3e78bee .vin span { color: #444 !important; font-weight: 700 !important; font-size: 12px !important; padding: 0 8px !important; }
    body.home .elementor-element-3e78bee .vin input { padding: 0 10px !important; border: none !important; border-radius: 4px !important; font-size: 13px !important; height: 36px !important; width: 180px !important; }
    body.home .elementor-element-3e78bee .reg, body.home .elementor-element-3e78bee .reg-input { width: 180px !important; min-width: 180px !important; flex: 0 0 180px !important; }
    body.home .elementor-element-3e78bee .reg-input { padding: 0 10px !important; font-size: 13px !important; height: 36px !important; border: none !important; border-radius: 4px !important; }
    body.home .elementor-element-3e78bee input[type="submit"] { background-color: #BF3617 !important; color: #fff !important; border: none !important; border-radius: 6px !important; font-size: 13px !important; font-weight: 700 !important; height: 36px !important; width: 75px !important; }
    body.home .elementor-element-3e78bee input[type="submit"]:hover { background-color: #111 !important; }
    body.home .elementor-element-3e78bee .select2-container, body.home .elementor-element-3e78bee .select2-selection--single { height: 36px !important; }
    body.home .elementor-element-3e78bee .select2-selection__rendered { line-height: 36px !important; padding: 0 10px !important; font-size: 13px !important; }
    body.home .elementor-element-3e78bee .select2-selection__arrow { height: 36px !important; }
    }

    /* === Why Use Us icons (Elementor - fix mask-image URLs) === */
    .elementor-element-c73c57f .et-icon-box .icon:before { mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/shield-check.svg) !important; -webkit-mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/shield-check.svg) !important; }
    .elementor-element-bd73a19 .et-icon-box .icon:before { mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/headset.svg) !important; -webkit-mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/headset.svg) !important; }
    .elementor-element-a272fa2 .et-icon-box .icon:before { mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/toolbox.svg) !important; -webkit-mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/toolbox.svg) !important; }
    .elementor-element-99bbea6 .et-icon-box .icon:before { mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/clipboard-check.svg) !important; -webkit-mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/clipboard-check.svg) !important; }
    .elementor-element-4103e18 .et-icon-box .icon:before { mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/telephone-call.svg) !important; -webkit-mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/telephone-call.svg) !important; }
    .elementor-element-d981530 .et-icon-box .icon:before { mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/shipping.svg) !important; -webkit-mask-image: url(https://shane.maxusvanparts.co.uk/wp-content/uploads/shipping.svg) !important; }
    .why-use-us-grid > .e-con-inner { display: flex !important; align-items: stretch !important; }
    .why-use-us-grid > .e-con-inner > .e-child { display: flex !important; flex-direction: column !important; }
    .why-use-us-grid .elementor-widget-et_icon_box { flex: 1 !important; }
    .why-use-us-grid { flex: 1 !important; }
    .elementor-element-fca08fb > .e-con-inner { align-items: flex-start !important; }

    /* ══════════════════════════════════════════════════════════
       MOBILE OVERRIDES — show Elementor defaults on mobile
       (our custom desktop injections dont run on mobile,
       so we need the original Elementor sections visible)
       ══════════════════════════════════════════════════════════ */
    @media (max-width: 1024px) {
        /* Show RevSlider on mobile */
        body.home .elementor-element-a40da3e,
        body.home sr7-module,
        body.home .wp-block-themepunch-revslider,
        body.home .elementor-widget-slider_revolution {
            display: none !important;
        }

        /* HIDE Elementor filter on mobile — replaced by custom mobile filter */
        body.home .elementor-element-3e78bee,
        body.home .elementor-element-3e78bee.breakpoint-767 {
            display: none !important;
        }
        /* Hide the toggle — form always visible */
        body.home .elementor-element-3e78bee .vehicle-filter-mobile-toggle {
            display: none !important;
        }
        /* Force form visible (theme hides it behind toggle on mobile) */
        body.home .elementor-element-3e78bee form.product-vehicle-filter,
        body.home .et-vehicle-filter.breakpoint-767 form.product-vehicle-filter {
            display: flex !important;
            visibility: visible !important;
            flex-direction: column !important;
            flex-wrap: wrap !important;
            gap: 10px !important;
            padding: 12px !important;
        }
        body.home .elementor-element-3e78bee .atts {
            flex: 1 1 100% !important;
            width: 100% !important;
            gap: 8px !important;
            height: auto !important;
            flex-direction: column !important;
        }
        body.home .elementor-element-3e78bee .vf-item,
        body.home .elementor-element-3e78bee .vf-item.model,
        body.home .elementor-element-3e78bee .vf-item.year {
            flex: 1 1 100% !important;
            width: 100% !important;
            min-width: 0 !important;
        }
        body.home .elementor-element-3e78bee .last {
            flex: 1 1 100% !important;
            width: 100% !important;
            flex-wrap: wrap !important;
            flex-direction: column !important;
            gap: 8px !important;
        }
        body.home .elementor-element-3e78bee .vin {
            width: 100% !important;
            flex: 1 1 100% !important;
            flex-direction: column !important;
        }
        body.home .elementor-element-3e78bee .vin span {
            display: none !important;
        }
        body.home .elementor-element-3e78bee .vin input,
        body.home .elementor-element-3e78bee .reg-input {
            width: 100% !important;
            flex: 1 1 auto !important;
            box-sizing: border-box !important;
        }
        body.home .elementor-element-3e78bee .reg,
        body.home .elementor-element-3e78bee .reg-input {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 0 !important;
        }
        body.home .elementor-element-3e78bee input[type=submit] {
            width: 100% !important;
            flex: 1 1 auto !important;
        }
        body.home .elementor-element-3e78bee .select2-container {
            width: 100% !important;
        }
        body.home .elementor-element-3e78bee .reset {
            text-align: center !important;
            display: block !important;
        }

        /* Show original category carousel */
        body.home .elementor-element-25b37be,
        body.home .elementor-element-099500a {
            display: none !important;
        }

        /* Show the extra Elementor sections */
        body.home .elementor-element-1eaa1c9,
        body.home .elementor-element-f5b0776,
        body.home .elementor-element-1fb0185,
        body.home .elementor-element-b14d001,
        body.home .elementor-element-09f258e,
        body.home .elementor-element-1b38164,
        body.home .elementor-element-1af2051,
        body.home .elementor-element-4a31403 {
            display: block !important;
        }

        /* Show Why Use Us Elementor section */
        body.home .elementor-element-8b07793 {
            height: auto !important;
            min-height: 0 !important;
            max-height: none !important;
            overflow: visible !important;
            display: block !important;
        }

        /* Show hero area on mobile but hide hero banner, keep carousel */
        #mvp-facelift-hero-area {
            display: block !important;
            padding: 12px 0 !important;
        }
        #mvp-facelift-hero-area > .mvp-hero {
            display: none !important;
        }
        .mvp-hero {
            height: 200px !important;
            border-radius: 0 !important;
            margin: 0 !important;
        }
        .mvp-hero-content {
            padding: 20px 20px !important;
            max-width: 100% !important;
        }
        .mvp-hero-content h1 {
            font-size: 28px !important;
            white-space: normal !important;
        }
        .mvp-hero-content h1 .hero-sub {
            font-size: 18px !important;
        }
        .mvp-hero-content p {
            font-size: 13px !important;
            display: none !important;
        }

        body.home .mvp-search-bar-wrap {
            display: none !important;
        }

        /* Show original department icons / categories row */
        body.home .elementor-element-9f85e6f,
        body.home .elementor-element-e540d81,
        body.home .elementor-element-23763df,
        body.home .elementor-element-20e40c9,
        body.home .elementor-element-7033a3b {
            display: block !important;
        }

        /* Show vehicle circles on mobile — horizontal scroll */
        .mvp-vehicles {
            display: block !important;
            padding: 10px 0;
            overflow-x: auto;
        }
        .mvp-carousel-track {
            display: flex !important;
            gap: 10px;
            padding: 0 16px;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }
        .mvp-vehicle-card {
            flex: 0 0 80px !important;
        }
        .mvp-vehicle-circle {
            width: 70px !important;
            height: 70px !important;
        }
        .mvp-vehicle-name {
            font-size: 10px !important;
        }
        .mvp-carousel-nav {
            display: none !important;
        }

        /* Why Use Us — stack vertically on mobile, show all cards */
        .elementor-element-8b07793 {
            height: auto !important;
            min-height: 0 !important;
            max-height: none !important;
            overflow: visible !important;
            display: block !important;
        }
        .elementor-element-8b07793 .e-con-inner {
            height: auto !important;
            display: block !important;
            flex-direction: column !important;
        }
        .elementor-element-8b07793 .e-child {
            width: 100% !important;
            max-width: 100% !important;
            flex-basis: 100% !important;
        }
        .elementor-element-8b07793 .et-icon-box {
            margin-bottom: 16px;
        }

        }
    }
    </style>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Oswald:wght@700&display=swap" rel="stylesheet">
    <?php
}

// ============================================================
// 2. INJECT HERO + VEHICLE CAROUSEL via JavaScript
//    (places them inside #wrap after the header, before content)
// ============================================================
add_action( 'wp_footer', 'mvp_facelift_inject_hero_and_carousel', 1 );
function mvp_facelift_inject_hero_and_carousel() {
    if ( ! is_front_page() && ! is_home() ) return;

    // Build vehicle cards from DB term meta (organic)
    $maxus_term_id = mvp_get_maxus_term_id();
    $vin_terms = get_terms( array(
        'taxonomy'   => 'product_cat',
        'parent'     => $maxus_term_id,
        'hide_empty' => false,
        'orderby'    => 'name',
    ) );

    $cards = '';
    if ( ! is_wp_error( $vin_terms ) ) {
        foreach ( $vin_terms as $term ) {
            $model = get_term_meta( $term->term_id, 'vehicle_model', true );
            $year  = get_term_meta( $term->term_id, 'vehicle_year', true );
            $img   = get_term_meta( $term->term_id, 'vehicle_image', true );
            $slug  = get_term_meta( $term->term_id, 'vehicle_slug', true );
            if ( ! $model || ! $slug ) continue;
            $url = home_url( '/vehicle/' . $slug . '/' );
            $cards .= '<a href="' . esc_url( $url ) . '" class="mvp-vehicle-card">'
                . '<div class="mvp-vehicle-circle"><img src="' . esc_url( $img ) . '" alt="' . esc_attr( $model ) . '" loading="lazy"></div>'
                . '<div class="mvp-vehicle-name">' . esc_html( $model ) . '</div>'
                . '<div class="mvp-vehicle-years">' . esc_html( $year ) . '</div>'
                . '</a>';
        }
    }

    $hero_html = '<div class="mvp-hero">'
        . '<div class="mvp-hero-content">'
        . '<h1>Genuine OEM Parts<span class="hero-sub">Direct From Maxus</span></h1>'
        . '<p>Original factory parts at competitive prices.<br>Perfect fit. Guaranteed quality.</p>'
        /* Shop All Parts button removed */
        . '</div></div>';

    $carousel_html = '<section id="mvp-vehicles" class="mvp-vehicles">'
        . '<div class="mvp-carousel-wrapper">'
        . '<button class="mvp-carousel-nav prev" onclick="document.querySelector(\'.mvp-carousel-track\').scrollBy({left:-220,behavior:\'smooth\'})">&#8249;</button>'
        . '<div class="mvp-carousel-track">' . $cards . '</div>'
        . '<button class="mvp-carousel-nav next" onclick="document.querySelector(\'.mvp-carousel-track\').scrollBy({left:220,behavior:\'smooth\'})">&#8250;</button>'
        . '</div></section>';

    $combined_json = json_encode( $hero_html . $carousel_html );
    ?>
    <script>
    document.addEventListener("DOMContentLoaded", function() {
        var target = document.querySelector(".elementor-11641");
        if (!target) return;
        var heroDiv = document.createElement("div");
        heroDiv.id = "mvp-facelift-hero-area";
        heroDiv.innerHTML = <?php echo $combined_json; ?>;
        target.parentNode.insertBefore(heroDiv, target);
    });
    </script>
    <?php
}

// ============================================================
// 3. "WHY USE US?" — Injected before the footer
// ============================================================
add_action( 'wp_footer', 'mvp_facelift_why_us', 5 );
function mvp_facelift_why_us() {
    if ( ! is_front_page() && ! is_home() ) return;
    ?>
    <section class="mvp-why-us">
        <h2>Why Use Us?</h2>
        <div class="mvp-why-grid">
            <div class="mvp-why-card">
                <div class="mvp-why-icon"><svg viewBox="0 0 48 48"><path d="M24 4L6 12v12c0 11 8 18 18 20 10-2 18-9 18-20V12L24 4z"/><polyline points="16 24 22 30 34 18"/></svg></div>
                <h3>Genuine OEM Parts</h3>
                <p>All parts are original Maxus or OEM-equivalent, ensuring the right fit and quality for your vehicle.</p>
            </div>
            <div class="mvp-why-card">
                <div class="mvp-why-icon"><svg viewBox="0 0 48 48"><circle cx="24" cy="14" r="8"/><path d="M8 42c0-9 7-16 16-16s16 7 16 16"/></svg></div>
                <h3>Professional Team</h3>
                <p>Expert staff with deep knowledge of the full Maxus range.</p>
            </div>
            <div class="mvp-why-card">
                <div class="mvp-why-icon"><svg viewBox="0 0 48 48"><path d="M24 44s-18-10-18-24a10 10 0 0118-6 10 10 0 0118 6c0 14-18 24-18 24z"/></svg></div>
                <h3>Happy to Help</h3>
                <p>Friendly support to help you find exactly the right part.</p>
            </div>
            <div class="mvp-why-card">
                <div class="mvp-why-icon"><svg viewBox="0 0 48 48"><path d="M4 24c0-11 9-20 20-20s20 9 20 20"/><path d="M4 28v6a4 4 0 004 4h2a2 2 0 002-2v-8a2 2 0 00-2-2H6a4 4 0 00-2 4zm40 0v6a4 4 0 01-4 4h-2a2 2 0 01-2-2v-8a2 2 0 012-2h4a4 4 0 012 4z"/><path d="M40 38c0 4-7 6-16 6"/></svg></div>
                <h3>Great Customer Service</h3>
                <p>Friendly, knowledgeable support from order to delivery.</p>
            </div>
            <div class="mvp-why-card">
                <div class="mvp-why-icon"><svg viewBox="0 0 48 48"><rect x="6" y="8" width="36" height="32" rx="3"/><polyline points="16 24 22 30 34 18"/><line x1="6" y1="16" x2="42" y2="16"/></svg></div>
                <h3>Verified Before Dispatch</h3>
                <p>Every order is checked against your vehicle details before dispatch to ensure the right part is sent.</p>
            </div>
            <div class="mvp-why-card">
                <div class="mvp-why-icon"><svg viewBox="0 0 48 48"><rect x="2" y="10" width="28" height="20" rx="2"/><path d="M30 16h8l6 8v6h-14V16z"/><circle cx="12" cy="34" r="4"/><circle cx="38" cy="34" r="4"/></svg></div>
                <h3>UK Wide Delivery</h3>
                <p>Fast, tracked delivery to anywhere in the United Kingdom.</p>
            </div>
        </div>
    </section>
    <?php
}

// ============================================================
// 4. CUSTOM FOOTER — Matching target site
// ============================================================
add_action( 'wp_footer', 'mvp_facelift_footer', 10 );
function mvp_facelift_footer() {
    ?>
    <footer class="mvp-footer">
        <div class="mvp-footer-main">
            <div class="mvp-footer-col">
                <h4>Maxus Parts Direct</h4>
                <div class="mvp-footer-trading">A trading name of Van Parts Direct Ltd</div>
                <div class="mvp-footer-contact">
                    <p>Unit 1-10, Cherry Tree Road,<br>Tibenham, NR16 1PH</p>
                    <p class="mvp-footer-phone"><a href="tel:01953528800">01953 528 800</a></p>
                    <p><a href="mailto:accounts@vanparts-direct.co.uk">accounts@vanparts-direct.co.uk</a></p>
                </div>
                <div class="mvp-footer-reg">
                    <p>Company Reg: 16322863</p>
                    <p>VAT No: 490 9953 39</p>
                </div>
                <div class="mvp-footer-payments">
                    <span class="pay-icon">VISA</span>
                    <span class="pay-icon">Mastercard</span>
                    <span class="pay-icon">AMEX</span>
                    <span class="pay-icon">Maestro</span>
                </div>
            </div>
            <div class="mvp-footer-col">
                <h4>Quick Links</h4>
                <ul>
                    <li><a href="/">Home</a></li>
                    <li><a href="/shop/">Shop</a></li>
                    <li><a href="/my-account/">My Account</a></li>
                    <li><a href="/cart/">Cart</a></li>
                </ul>
            </div>
            <div class="mvp-footer-col">
                <h4>Information</h4>
                <ul>
                    <li><a href="/about-us/">About Us</a></li>
                    <li><a href="/contact-us/">Contact Us</a></li>
                    <li><a href="/terms-and-conditions/">Terms &amp; Conditions</a></li>
                    <li><a href="/privacy-policy/">Privacy Policy</a></li>
                    <li><a href="/gdpr-data-protection/">GDPR Data Protection</a></li>
                    <li><a href="/returns-and-exchanges/">Returns &amp; Exchanges</a></li>
                </ul>
            </div>
            <div class="mvp-footer-col">
                <h4>Vehicles</h4>
                <ul>
                <?php
                $maxus_id = mvp_get_maxus_term_id();
                if ($maxus_id) {
                    $vterms = get_terms(array("taxonomy"=>"product_cat","parent"=>$maxus_id,"hide_empty"=>false,"orderby"=>"name"));
                    if (!is_wp_error($vterms)) {
                        foreach ($vterms as $vt) {
                            $vslug = get_term_meta($vt->term_id, "vehicle_slug", true);
                            $vmodel = get_term_meta($vt->term_id, "vehicle_model", true);
                            if ($vslug && $vmodel) {
                                echo "<li><a href=\"/vehicle/" . esc_attr($vslug) . "/\">" . esc_html($vmodel) . "</a></li>";
                            }
                        }
                    }
                }
                ?>
                </ul>
            </div>
            <div class="mvp-footer-col">
                <h4>Customer Service</h4>
                <ul>
                    <li><a href="/my-account/">Login</a></li>
                    <li><a href="/my-account/">Register</a></li>
                    <li><a href="/my-account/orders/">Order History</a></li>
                    <li><a href="/shipping-information/">Shipping Info</a></li>
                    <li><a href="/faq/">FAQ</a></li>
                    <li><a href="/trade-account/">Trade Account</a></li>
                </ul>
            </div>
            <div class="mvp-footer-col">
                <h4>Our Other Services</h4>
                <ul>
                    <li><a href="https://vansalesdirect.uk" target="_blank" rel="noopener">vansalesdirect.uk</a></li>
                    <li><a href="https://direct-vanhire.co.uk" target="_blank" rel="noopener">direct-vanhire.co.uk</a></li>
                    <li><a href="https://rapidfit.co.uk" target="_blank" rel="noopener">rapidfit.co.uk</a></li>
                </ul>
            </div>
        </div>
        <div class="mvp-footer-bottom">
            <div class="mvp-footer-bottom-inner">
                <p class="mvp-footer-copyright">&copy; <?php echo date('Y'); ?> Van Parts Direct Ltd. All rights reserved.</p>
                <div class="mvp-footer-bottom-links">
                    <a href="/privacy-policy/">Privacy Policy</a>
                    <span class="sep">|</span>
                    <a href="/terms-and-conditions/">Terms &amp; Conditions</a>
                </div>
            </div>
        </div>
    </footer>
    <?php
}

// ============================================================
// 4b. MAXUS ROOT TERM HELPER — resolves by slug, not hardcoded ID
// ============================================================

function mvp_get_maxus_term_id() {
    static $id = null;
    if ( $id !== null ) return $id;
    $term = get_term_by( 'slug', 'maxus', 'product_cat' );
    $id   = ( $term && ! is_wp_error( $term ) ) ? (int) $term->term_id : 0;
    return $id;
}


// ============================================================
// 4b. SINGLE PRODUCT PAGE — Match target layout
// ============================================================

// Remove default WooCommerce meta (SKU, categories, tags) — we show our own
add_action( 'wp', function() {
    if ( is_product() ) {
        remove_action( 'woocommerce_single_product_summary', 'woocommerce_template_single_meta', 25 );
    }
});

// Remove reviews tab and additional information tab
add_filter( 'woocommerce_product_tabs', 'mvp_remove_product_tabs', 98 );
function mvp_remove_product_tabs( $tabs ) {
    unset( $tabs['reviews'] );
    unset( $tabs['additional_information'] );
    return $tabs;
}

// Add SKU / Part No / Weight row after title (priority 6, after title at 5)
add_action( 'woocommerce_single_product_summary', 'mvp_product_meta_info', 6 );
function mvp_product_meta_info() {
    global $product;
    $sku    = $product->get_sku();
    $weight = $product->get_weight();
    $w_unit = get_option( 'woocommerce_weight_unit', 'kg' );
    if ( ! $sku && ! $weight ) return;
    echo '<div class="mvp-product-meta-info">';
    if ( $sku ) {
        echo '<span class="meta-label">SKU:</span> <span class="meta-value">' . esc_html( $sku ) . '</span>';
    }
    if ( $weight && $weight > 0 ) {
        if ( $sku ) echo '<span class="meta-sep">|</span>';
        echo '<span class="meta-label">Weight:</span> <span class="meta-value">' . esc_html( $weight . $w_unit ) . '</span>';
    }
    echo '</div>';
}

// Replace Add to Cart with "Request a Price" for products without a price
// ============================================================
// Request Price Modal — for products with no price
// ============================================================
add_action( 'woocommerce_single_product_summary', 'mvp_request_price_button', 29 );
function mvp_request_price_button() {
    global $product;
    if ( $product->get_price() === '' || $product->get_price() === null ) {
        $lr = get_post_meta( $product->get_id(), 'lr', true );
        $remark = get_post_meta( $product->get_id(), 'remark', true );
        echo '<div class="mvp-price-request-text">Price on request</div>';
        echo '<button type="button" class="mvp-request-price-btn" '
            . 'data-lr="' . esc_attr( $lr ) . '" '
            . 'data-remark="' . esc_attr( $remark ) . '" '
            . 'onclick="mvpOpenPriceModal(this)">REQUEST A PRICE</button>';
        echo '<style>body.single-product .product form.cart { display: none !important; }</style>';
    }
}

// Replace "Add to cart" on archive/loop pages for no-price products
add_filter( 'woocommerce_loop_add_to_cart_link', 'mvp_loop_request_price', 10, 2 );
function mvp_loop_request_price( $link, $product ) {
    if ( $product->get_price() === '' || $product->get_price() === null ) {
        return '<a href="' . esc_url( get_permalink( $product->get_id() ) ) . '" class="button mvp-request-price-loop">Request Price</a>';
    }
    return $link;
}

// AJAX handler for price request form
add_action( 'wp_ajax_mvp_price_request', 'mvp_handle_price_request' );
add_action( 'wp_ajax_nopriv_mvp_price_request', 'mvp_handle_price_request' );
function mvp_handle_price_request() {
    check_ajax_referer( 'mvp_price_request_nonce', 'nonce' );

    $name    = sanitize_text_field( $_POST['name'] ?? '' );
    $email   = sanitize_email( $_POST['email'] ?? '' );
    $phone   = sanitize_text_field( $_POST['phone'] ?? '' );
    $sku     = sanitize_text_field( $_POST['sku'] ?? '' );
    $product_name = sanitize_text_field( $_POST['product_name'] ?? '' );
    $product_url  = esc_url_raw( $_POST['product_url'] ?? '' );
    $product_meta = sanitize_text_field( $_POST['product_meta'] ?? '' );

    if ( ! $name || ! $email ) {
        wp_send_json_error( 'Name and email are required.' );
    }

    $to      = 'neil@rapidfit.co.uk';
    $subject = 'Price Request: ' . $sku . ' - ' . $product_name;
    $body    = "New price request received:\n\n";
    $body   .= "Product: " . $product_name . "\n";
    $body   .= "SKU: " . $sku . "\n";
    if ( $product_meta ) {
        $body .= "Details: " . $product_meta . "\n";
    }
    $body   .= "URL: " . $product_url . "\n\n";
    $body   .= "Customer Details:\n";
    $body   .= "Name: " . $name . "\n";
    $body   .= "Email: " . $email . "\n";
    $body   .= "Phone: " . $phone . "\n";

    $headers = array(
        'Content-Type: text/plain; charset=UTF-8',
        'Reply-To: ' . $name . ' <' . $email . '>',
    );

    $sent = wp_mail( $to, $subject, $body, $headers );

    if ( $sent ) {
        wp_send_json_success( 'Your request has been sent. We will be in touch shortly.' );
    } else {
        wp_send_json_error( 'Failed to send. Please try calling us on 01953 528300.' );
    }
}

// Output the modal HTML + CSS + JS in the footer
add_action( 'wp_footer', 'mvp_price_request_modal', 50 );
function mvp_price_request_modal() {
    $nonce = wp_create_nonce( 'mvp_price_request_nonce' );
    $ajax_url = admin_url( 'admin-ajax.php' );
    ?>
    <style>
    .mvp-request-price-btn {
        display: inline-block;
        background: #BF3617;
        color: #fff !important;
        font-weight: 700;
        font-size: 15px;
        padding: 12px 28px;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        text-decoration: none;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        transition: background 0.2s;
    }
    .mvp-request-price-btn:hover { background: #a82e13; color: #fff !important; }
    .mvp-request-price-loop { background: #BF3617 !important; color: #fff !important; font-weight: 600 !important; border-radius: 6px !important; }
    .mvp-request-price-loop:hover { background: #a82e13 !important; }
    .mvp-price-request-text { font-size: 18px; font-weight: 700; color: #BF3617; margin-bottom: 12px; }
    .mvp-price-modal-overlay {
        display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.6); z-index: 99999; align-items: center; justify-content: center;
    }
    .mvp-price-modal-overlay.active { display: flex; }
    .mvp-price-modal {
        background: #fff; border-radius: 12px; padding: 32px; max-width: 480px; width: 90%;
        max-height: 90vh; overflow-y: auto; position: relative; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    .mvp-price-modal h3 { font-size: 20px; font-weight: 700; color: #1a1a2e; margin: 0 0 6px; }
    .mvp-price-modal-close {
        position: absolute; top: 12px; right: 16px; font-size: 24px; color: #999;
        cursor: pointer; background: none; border: none; line-height: 1;
    }
    .mvp-price-modal-close:hover { color: #333; }
    .mvp-price-modal-product {
        background: #f5f5f5; border-radius: 8px; padding: 12px 16px; margin: 16px 0; font-size: 13px; color: #666;
    }
    .mvp-price-modal-product strong { color: #333; }
    .mvp-price-modal label { display: block; font-size: 13px; font-weight: 600; color: #333; margin: 14px 0 4px; }
    .mvp-price-modal input[type=text],
    .mvp-price-modal input[type=email],
    .mvp-price-modal input[type=tel] {
        width: 100%; padding: 10px 14px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box;
    }
    .mvp-price-modal input:focus { border-color: #F29F05; outline: none; box-shadow: 0 0 0 2px rgba(242,159,5,0.2); }
    .mvp-price-modal-submit {
        width: 100%; margin-top: 20px; padding: 14px; background: #BF3617; color: #fff;
        border: none; border-radius: 6px; font-size: 16px; font-weight: 700; cursor: pointer; transition: background 0.2s;
    }
    .mvp-price-modal-submit:hover { background: #a82e13; }
    .mvp-price-modal-submit:disabled { background: #ccc; cursor: not-allowed; }
    .mvp-price-modal-msg { margin-top: 12px; padding: 10px 14px; border-radius: 6px; font-size: 14px; display: none; }
    .mvp-price-modal-msg.success { display: block; background: #e8f5e9; color: #2e7d32; }
    .mvp-price-modal-msg.error { display: block; background: #fbe9e7; color: #c62828; }
    @media (max-width: 600px) { .mvp-price-modal { padding: 24px 20px; } }
    </style>

    <div class="mvp-price-modal-overlay" id="mvpPriceModal">
        <div class="mvp-price-modal">
            <button class="mvp-price-modal-close" onclick="mvpClosePriceModal()">&times;</button>
            <h3>Request a Price</h3>
            <div class="mvp-price-modal-product">
                <strong id="mvpPriceProductName"></strong><br>
                SKU: <span id="mvpPriceProductSku"></span>
                <span id="mvpPriceMetaWrap" style="display:none"><br><span id="mvpPriceMeta" style="color:#333;font-weight:600"></span></span>
            </div>
            <form id="mvpPriceForm" onsubmit="return mvpSubmitPriceForm(event)">
                <input type="hidden" id="mvpPriceSku" name="sku">
                <input type="hidden" id="mvpPriceProductNameHidden" name="product_name">
                <input type="hidden" id="mvpPriceProductUrl" name="product_url">
                <input type="hidden" id="mvpPriceProductMeta" name="product_meta">
                <label for="mvpPriceName">Your Name *</label>
                <input type="text" id="mvpPriceName" name="name" required placeholder="Full name">
                <label for="mvpPriceEmail">Email Address *</label>
                <input type="email" id="mvpPriceEmail" name="email" required placeholder="your@email.com">
                <label for="mvpPricePhone">Phone Number</label>
                <input type="tel" id="mvpPricePhone" name="phone" placeholder="Optional">
                <button type="submit" class="mvp-price-modal-submit" id="mvpPriceSubmitBtn">Submit Enquiry</button>
                <div class="mvp-price-modal-msg" id="mvpPriceMsg"></div>
            </form>
        </div>
    </div>

    <script>
    function mvpOpenPriceModal(btn) {
        var modal = document.getElementById('mvpPriceModal');
        var nameEl = document.querySelector('.product_title, h1.entry-title, .entry-title');
        var skuEl = document.querySelector('.sku, .meta-value');
        var productName = nameEl ? nameEl.textContent.trim() : '';
        var sku = skuEl ? skuEl.textContent.trim() : '';
        var lr = btn ? (btn.getAttribute('data-lr') || '') : '';
        var remark = btn ? (btn.getAttribute('data-remark') || '') : '';
        var metaParts = [];
        if (lr) metaParts.push('Orientation: ' + lr);
        if (remark) metaParts.push(remark);
        var metaText = metaParts.join(' | ');
        document.getElementById('mvpPriceProductName').textContent = productName;
        document.getElementById('mvpPriceProductSku').textContent = sku;
var metaWrap = document.getElementById('mvpPriceMetaWrap');        var metaSpan = document.getElementById('mvpPriceMeta');        if (metaWrap) { if (metaText) { metaSpan.textContent = metaText; metaWrap.style.display = 'inline'; } else { metaWrap.style.display = 'none'; } }
        document.getElementById('mvpPriceSku').value = sku;
        document.getElementById('mvpPriceProductNameHidden').value = productName;
        document.getElementById('mvpPriceProductUrl').value = window.location.href;
        document.getElementById('mvpPriceForm').reset();
        document.getElementById('mvpPriceSku').value = sku;
        document.getElementById('mvpPriceProductNameHidden').value = productName;
        document.getElementById('mvpPriceProductUrl').value = window.location.href;
        if (document.getElementById('mvpPriceProductMeta')) document.getElementById('mvpPriceProductMeta').value = metaText || '';
        document.getElementById('mvpPriceMsg').className = 'mvp-price-modal-msg';
        document.getElementById('mvpPriceSubmitBtn').disabled = false;
        document.getElementById('mvpPriceSubmitBtn').textContent = 'Submit Enquiry';
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    function mvpOpenPriceModalFromTable(btn) {
        var modal = document.getElementById('mvpPriceModal');
        var sku = btn.getAttribute('data-sku') || '';
        var productName = btn.getAttribute('data-name') || '';
        var productUrl = btn.getAttribute('data-url') || '';
        var lr = btn.getAttribute('data-lr') || '';
        var remark = btn.getAttribute('data-remark') || '';
        var metaParts = [];
        if (lr) metaParts.push('Orientation: ' + lr);
        if (remark) metaParts.push(remark);
        var metaText = metaParts.join(' | ');
        document.getElementById('mvpPriceProductName').textContent = productName;
        document.getElementById('mvpPriceProductSku').textContent = sku;
        var metaWrap = document.getElementById('mvpPriceMetaWrap');
        var metaSpan = document.getElementById('mvpPriceMeta');
        if (metaWrap) {
            if (metaText) { metaSpan.textContent = metaText; metaWrap.style.display = 'inline'; }
            else { metaWrap.style.display = 'none'; }
        }
        document.getElementById('mvpPriceForm').reset();
        document.getElementById('mvpPriceSku').value = sku;
        document.getElementById('mvpPriceProductNameHidden').value = productName;
        document.getElementById('mvpPriceProductUrl').value = productUrl;
        if (document.getElementById('mvpPriceProductMeta')) document.getElementById('mvpPriceProductMeta').value = metaText || '';
        document.getElementById('mvpPriceMsg').className = 'mvp-price-modal-msg';
        document.getElementById('mvpPriceSubmitBtn').disabled = false;
        document.getElementById('mvpPriceSubmitBtn').textContent = 'Submit Enquiry';
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    function mvpClosePriceModal() {
        document.getElementById('mvpPriceModal').classList.remove('active');
        document.body.style.overflow = '';
    }
    document.getElementById('mvpPriceModal').addEventListener('click', function(e) {
        if (e.target === this) mvpClosePriceModal();
    });
    document.addEventListener('keydown', function(e) { if (e.key === 'Escape') mvpClosePriceModal(); });
    function mvpSubmitPriceForm(e) {
        e.preventDefault();
        var btn = document.getElementById('mvpPriceSubmitBtn');
        var msg = document.getElementById('mvpPriceMsg');
        btn.disabled = true;
        btn.textContent = 'Sending...';
        msg.className = 'mvp-price-modal-msg';
        var fd = new FormData();
        fd.append('action', 'mvp_price_request');
        fd.append('nonce', '<?php echo esc_js( $nonce ); ?>');
        fd.append('name', document.getElementById('mvpPriceName').value);
        fd.append('email', document.getElementById('mvpPriceEmail').value);
        fd.append('phone', document.getElementById('mvpPricePhone').value);
        fd.append('sku', document.getElementById('mvpPriceSku').value);
        fd.append('product_name', document.getElementById('mvpPriceProductNameHidden').value);
        fd.append('product_url', document.getElementById('mvpPriceProductUrl').value);
        fd.append('product_meta', document.getElementById('mvpPriceProductMeta') ? document.getElementById('mvpPriceProductMeta').value : '');
        fetch('<?php echo esc_url( $ajax_url ); ?>', { method: 'POST', body: fd })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.success) {
                msg.className = 'mvp-price-modal-msg success';
                msg.textContent = data.data;
                btn.textContent = 'Sent!';
                setTimeout(mvpClosePriceModal, 3000);
            } else {
                msg.className = 'mvp-price-modal-msg error';
                msg.textContent = data.data || 'Something went wrong.';
                btn.disabled = false;
                btn.textContent = 'Submit Enquiry';
            }
        })
        .catch(function() {
            msg.className = 'mvp-price-modal-msg error';
            msg.textContent = 'Network error. Please try again.';
            btn.disabled = false;
            btn.textContent = 'Submit Enquiry';
        });
        return false;
    }
    </script>
    <?php
}

// Add estimated delivery time (priority 35, after add to cart at 30)
add_action( 'woocommerce_single_product_summary', 'mvp_estimated_delivery', 35 );
function mvp_estimated_delivery() {
    global $product;
    $delivery = get_post_meta( $product->get_id(), '_estimated_delivery_time', true );
    if ( empty( $delivery ) ) {
        $delivery = '2-3 working days';
    }
    echo '<div class="mvp-delivery-time">';
    echo '<span class="delivery-label">Estimated Delivery:</span> ';
    echo '<span class="delivery-value">' . esc_html( $delivery ) . '</span>';
    echo '</div>';
}

// Add Compatible Vehicles section (placeholder — blank for now)
add_action( 'woocommerce_single_product_summary', 'mvp_compatible_vehicles', 45 );
function mvp_compatible_vehicles() {
    global $product;
    if ( ! $product ) return;

    $original_sku = get_post_meta( $product->get_id(), 'original_sku', true );
    if ( ! $original_sku ) {
        // Fallback: no original_sku, show current vehicle only
        $original_sku = $product->get_sku();
    }
    if ( ! $original_sku ) {
        echo '<div class="mvp-vehicle-compat">';
        echo '<h4>Compatible Vehicles:</h4>';
        echo '<p class="v-empty">Vehicle compatibility data coming soon.</p>';
        echo '</div>';
        return;
    }

    // Check transient cache first
    $cache_key = 'mvp_compat_' . md5( $original_sku );
    $vehicles = get_transient( $cache_key );

    if ( false === $vehicles ) {
        // Find all products with the same original_sku
        $matching = get_posts( array(
            'post_type'      => 'product',
            'post_status'    => 'publish',
            'posts_per_page' => 100,
            'fields'         => 'ids',
            'meta_query'     => array(
                array(
                    'key'   => 'original_sku',
                    'value' => $original_sku,
                ),
            ),
        ) );

        if ( empty( $matching ) ) {
            // Try matching by _sku prefix (strip the hash suffix)
            $base_sku = preg_replace( '/-[A-F0-9]{4,}$/i', '', $product->get_sku() );
            if ( $base_sku && $base_sku !== $product->get_sku() ) {
                $matching = get_posts( array(
                    'post_type'      => 'product',
                    'post_status'    => 'publish',
                    'posts_per_page' => 100,
                    'fields'         => 'ids',
                    'meta_query'     => array(
                        array(
                            'key'     => 'original_sku',
                            'value'   => $base_sku,
                        ),
                    ),
                ) );
            }
        }

        // Also include current product
        if ( ! in_array( $product->get_id(), $matching ) ) {
            $matching[] = $product->get_id();
        }

        $maxus_id = mvp_get_maxus_term_id();
        $vehicles = array();

        foreach ( $matching as $pid ) {
            $cats = wp_get_post_terms( $pid, 'product_cat', array( 'fields' => 'ids' ) );
            if ( is_wp_error( $cats ) ) continue;
            foreach ( $cats as $cat_id ) {
                $ancestors = get_ancestors( $cat_id, 'product_cat', 'taxonomy' );
                foreach ( $ancestors as $anc_id ) {
                    if ( isset( $vehicles[ $anc_id ] ) ) continue;
                    $anc_term = get_term( $anc_id, 'product_cat' );
                    if ( ! $anc_term || (int) $anc_term->parent !== $maxus_id ) continue;
                    $model = get_term_meta( $anc_id, 'vehicle_model', true );
                    $year  = get_term_meta( $anc_id, 'vehicle_year', true );
                    $slug  = get_term_meta( $anc_id, 'vehicle_slug', true );
                    if ( $model ) {
                        $vehicles[ $anc_id ] = array(
                            'model' => $model,
                            'year'  => $year,
                            'slug'  => $slug,
                        );
                    }
                }
            }
        }

        // Sort by model name
        uasort( $vehicles, function( $a, $b ) {
            return strcmp( $a['model'], $b['model'] );
        } );

        // Cache for 24 hours
        set_transient( $cache_key, $vehicles, DAY_IN_SECONDS );
    }

    echo '<div class="mvp-vehicle-compat">';
    echo '<h4>Compatible Vehicles:</h4>';

    if ( ! empty( $vehicles ) ) {
        echo '<ul>';
        foreach ( $vehicles as $v ) {
            $url = $v['slug'] ? home_url( '/vehicle/' . $v['slug'] . '/' ) : '#';
            echo '<li>';
            echo '<a href="' . esc_url( $url ) . '" class="v-name">' . esc_html( $v['model'] ) . '</a>';
            if ( $v['year'] ) {
                echo '<span class="v-year">(' . esc_html( $v['year'] ) . ')</span>';
            }
            echo '</li>';
        }
        echo '</ul>';
    } else {
        echo '<p class="v-empty">Vehicle compatibility data coming soon.</p>';
    }

    echo '</div>';
}

// Hide "Callout: X / Qty: Y" text in summary via JS
add_action( 'wp_footer', 'mvp_hide_callout_text' );
function mvp_hide_callout_text() {
    if ( ! is_product() ) return;
    ?>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        var summary = document.querySelector('.summary, .entry-summary');
        if (!summary) return;
        var walker = document.createTreeWalker(summary, NodeFilter.SHOW_TEXT, null, false);
        var node;
        while (node = walker.nextNode()) {
            if (node.textContent && node.textContent.match(/Callout:\s*\d+|Qty:\s*[\d.]/i)) {
                var parent = node.parentElement;
                if (parent) parent.style.display = 'none';
            }
        }
    });
    </script>
    <?php
}

// Add description section below the product summary (via footer hook on product pages)
add_action( 'woocommerce_after_single_product_summary', 'mvp_product_description_section', 5 );
function mvp_product_description_section() {
    global $product;
    $desc = $product->get_description();
    $short = $product->get_short_description();
    $content = $desc ? $desc : $short;
    if ( ! $content ) return;
    echo '<div class="mvp-product-description">';
    echo '<h3>Description</h3>';
    echo '<div>' . wp_kses_post( wpautop( $content ) ) . '</div>';
    echo '</div>';
}

// Replace VIN numbers with vehicle model names in breadcrumbs (all sources)
// 1. WooCommerce breadcrumbs
add_filter( 'woocommerce_get_breadcrumb', 'mvp_breadcrumb_replace_vin', 10, 1 );
function mvp_breadcrumb_replace_vin( $crumbs ) {
    if ( empty( $crumbs ) ) return $crumbs;
    $maxus_id = mvp_get_maxus_term_id();
    foreach ( $crumbs as &$crumb ) {
        $term = get_term_by( 'name', $crumb[0], 'product_cat' );
        if ( ! $term || (int) $term->parent !== $maxus_id ) continue;
        $model = get_term_meta( $term->term_id, 'vehicle_model', true );
        if ( ! $model ) continue;
        $year = get_term_meta( $term->term_id, 'vehicle_year', true );
        $crumb[0] = $model . ( $year ? ' (' . $year . ')' : '' );
    }
    return $crumbs;
}

// 2. Theme breadcrumbs (enovathemes) — JS replacement for VIN terms
add_action( 'wp_footer', function() {
    if ( ! is_tax( 'product_cat' ) && ! is_product() ) return;
    // Build VIN-to-model map for terms in the current breadcrumb
    $maxus_id = mvp_get_maxus_term_id();
    $vin_terms = get_terms( array(
        'taxonomy' => 'product_cat',
        'parent'   => $maxus_id,
        'hide_empty' => false,
        'fields'   => 'all',
    ) );
    if ( is_wp_error( $vin_terms ) || empty( $vin_terms ) ) return;
    $map = array();
    foreach ( $vin_terms as $vt ) {
        $model = get_term_meta( $vt->term_id, 'vehicle_model', true );
        $year  = get_term_meta( $vt->term_id, 'vehicle_year', true );
        if ( $model ) {
            $display = $model . ( $year ? ' (' . $year . ')' : '' );
            $map[ $vt->name ] = $display;
        }
    }
    if ( empty( $map ) ) return;
    ?>
    <script>
    (function(){
        var vinMap = <?php echo json_encode( $map ); ?>;
        var bc = document.querySelector('.et-breadcrumbs');
        if (!bc) return;
        var links = bc.querySelectorAll('a');
        links.forEach(function(a) {
            var text = a.textContent.trim();
            if (vinMap[text]) {
                a.textContent = vinMap[text];
            }
        });
        // Also check text nodes (the last crumb might not be a link)
        bc.childNodes.forEach(function(node) {
            if (node.nodeType === 3) {
                var text = node.textContent.trim();
                if (vinMap[text]) {
                    node.textContent = node.textContent.replace(text, vinMap[text]);
                }
            }
        });
    })();
    </script>
    <?php
}, 99 );

// Filter out utility categories from breadcrumbs
add_filter( 'get_the_terms', 'mvp_filter_breadcrumb_terms', 10, 3 );
function mvp_filter_breadcrumb_terms( $terms, $post_id, $taxonomy ) {
    if ( $taxonomy !== 'product_cat' || ! is_product() ) return $terms;
    if ( empty( $terms ) || is_wp_error( $terms ) ) return $terms;
    $exclude = array( 'priceupdated', 'imageupdated', 'uncategorized' );
    return array_filter( $terms, function( $term ) use ( $exclude ) {
        return ! in_array( $term->slug, $exclude );
    });
}


// ============================================================
// 5. VEHICLE LANDING PAGES — Rewrite rules + template
// ============================================================

// Register rewrite rule: /vehicle/{slug}/ → index.php?mvp_vehicle={slug}
add_action( 'init', 'mvp_vehicle_rewrite_rules' );
function mvp_vehicle_rewrite_rules() {
    add_rewrite_rule(
        '^vehicle/([^/]+)/?$',
        'index.php?mvp_vehicle=$matches[1]',
        'top'
    );
}

// Register query var
add_filter( 'query_vars', 'mvp_vehicle_query_vars' );
function mvp_vehicle_query_vars( $vars ) {
    $vars[] = 'mvp_vehicle';
    return $vars;
}

// Prevent WordPress from treating vehicle pages as 404
add_action( 'pre_get_posts', 'mvp_vehicle_prevent_404' );
function mvp_vehicle_prevent_404( $query ) {
    if ( ! $query->is_main_query() ) return;
    $vehicle_slug = $query->get( 'mvp_vehicle' );
    if ( $vehicle_slug ) {
        $query->is_404 = false;
    }
}

// Render vehicle page via template_redirect (before any template loads)
add_action( 'template_redirect', 'mvp_vehicle_template_redirect' );
function mvp_vehicle_template_redirect() {
    $vehicle_slug = get_query_var( 'mvp_vehicle' );
    if ( ! $vehicle_slug ) return;

    // Find the VIN term by its vehicle_slug meta
    $maxus_term_id = mvp_get_maxus_term_id();
    $vin_terms = get_terms( array(
        'taxonomy'   => 'product_cat',
        'parent'     => $maxus_term_id,
        'hide_empty' => false,
        'meta_query' => array( array( 'key' => 'vehicle_slug', 'value' => sanitize_title( $vehicle_slug ) ) ),
    ) );

    if ( is_wp_error( $vin_terms ) || empty( $vin_terms ) ) {
        return; // Let WP handle 404
    }

    $vin_term = $vin_terms[0];

    // Store data in global
    global $mvp_vehicle_data;
    $mvp_vehicle_data = array(
        'vin_term'     => $vin_term,
        'vin_serial'   => $vin_term->name,
        'vehicle_slug' => sanitize_title( $vehicle_slug ),
        'model'        => get_term_meta( $vin_term->term_id, 'vehicle_model', true ),
        'year'         => get_term_meta( $vin_term->term_id, 'vehicle_year', true ),
        'img'          => get_term_meta( $vin_term->term_id, 'vehicle_image', true ),
        'categories'   => get_terms( array(
            'taxonomy'   => 'product_cat',
            'parent'     => $vin_term->term_id,
            'hide_empty' => true,
            'orderby'    => 'name',
        ) ),
        'cat_img_base' => 'https://shane.maxusvanparts.co.uk/wp-content/uploads/categories/',
    );

    // Reset 404 status and set 200
    global $wp_query;
    $wp_query->is_404 = false;
    status_header( 200 );

    // Render and exit
    mvp_vehicle_render_full_page();
    exit;
}

// Render full vehicle landing page
function mvp_vehicle_render_full_page() {
    global $mvp_vehicle_data;
    $vin_term     = $mvp_vehicle_data['vin_term'];
    $model        = $mvp_vehicle_data['model'];
    $year         = $mvp_vehicle_data['year'];
    $img          = $mvp_vehicle_data['img'];
    $categories   = $mvp_vehicle_data['categories'];
    $cat_img_base = $mvp_vehicle_data['cat_img_base'];

    // Set page title
    add_filter( "document_title_parts", function( $title ) use ( $model ) {
        $title["title"] = $model ? $model . " - Maxus Parts Direct" : "Vehicle - Maxus Parts Direct";
        return $title;
    } );
    get_header();
    ?>
    <style>
    /* Vehicle Landing Page Styles */
    .mvp-vehicle-page {
        max-width: 1300px;
        margin: 0 auto;
        padding: 30px 20px 60px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .mvp-vehicle-header {
        display: flex;
        align-items: center;
        gap: 30px;
        margin-bottom: 35px;
        padding-bottom: 25px;
        border-bottom: 2px solid #f0f0f0;
    }
    .mvp-vehicle-header-img {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        border: 3px solid #ccc;
        background: #f8f8f8;
        overflow: hidden;
        flex-shrink: 0;
    }
    .mvp-vehicle-header-img img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .mvp-vehicle-header-info h1 {
        font-size: 32px;
        font-weight: 700;
        color: #1a1a2e;
        margin: 0 0 6px;
    }
    .mvp-vehicle-header-info .mvp-vh-years {
        font-size: 16px;
        color: #888;
        margin: 0 0 10px;
    }
    .mvp-vehicle-header-info .mvp-vh-breadcrumb {
        font-size: 14px;
        color: #aaa;
    }
    .mvp-vehicle-header-info .mvp-vh-breadcrumb a {
        color: #034C8C;
        text-decoration: none;
    }
    .mvp-vehicle-header-info .mvp-vh-breadcrumb a:hover {
        color: #F29F05;
    }
    .mvp-category-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 20px;
    }
    .mvp-category-card {
        background: #fff;
        border: 1px solid #eee;
        border-radius: 10px;
        overflow: hidden;
        text-decoration: none;
        color: #333;
        transition: transform 0.3s, box-shadow 0.3s;
        display: flex;
        flex-direction: column;
    }
    .mvp-category-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    .mvp-category-card-img {
        width: 100%;
        height: 150px;
        background: #f5f5f5;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }
    .mvp-category-card-img img {
        max-width: 90%;
        max-height: 130px;
        object-fit: contain;
    }
    .mvp-category-card-body {
        padding: 14px 16px;
        text-align: center; line-height: 48px;
    }
    .mvp-category-card-body h3 {
        font-size: 15px;
        font-weight: 600;
        color: #1a1a2e;
        margin: 0 0 4px;
    }
    .mvp-category-card-body .mvp-cat-count {
        font-size: 12px;
        color: #999;
    }
    @media (max-width: 768px) {
        .mvp-vehicle-header { flex-direction: column; text-align: center; line-height: 48px; gap: 16px; }
        .mvp-vehicle-header-img { width: 120px; height: 120px; }
        .mvp-vehicle-header-info h1 { font-size: 24px; }
        .mvp-category-grid { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 14px; }
        .mvp-category-card-img { height: 120px; }
    }
    @media (max-width: 480px) {
        .mvp-category-grid { grid-template-columns: 1fr 1fr; gap: 10px; }
        .mvp-category-card-img { height: 100px; }
        .mvp-category-card-body { padding: 10px 12px; }
        .mvp-category-card-body h3 { font-size: 13px; }
    }
    </style>

    <div class="mvp-vehicle-page">
        <div class="mvp-vehicle-header">
            <?php if ( $img ) : ?>
            <div class="mvp-vehicle-header-img">
                <img src="<?php echo esc_url( $img ); ?>" alt="<?php echo esc_attr( $model ); ?>">
            </div>
            <?php endif; ?>
            <div class="mvp-vehicle-header-info">
                <p class="mvp-vh-breadcrumb"><a href="<?php echo home_url('/'); ?>">Home</a> &rsaquo; <a href="<?php echo home_url('/'); ?>">Vehicles</a> &rsaquo; <?php echo esc_html( $model ); ?></p>
                <h1><?php echo esc_html( $model ); ?></h1>
                <p class="mvp-vh-years"><?php echo esc_html( $year ); ?></p>
            </div>
        </div>

        <?php if ( ! empty( $categories ) && ! is_wp_error( $categories ) ) : ?>
        <div class="mvp-category-grid">
            <?php foreach ( $categories as $cat ) :
                // Build category image filename: replace spaces with underscores
                $cat_img_file = mvp_category_icon_file( $cat->name );
                $cat_img_url  = $cat_img_file ? $cat_img_base . $cat_img_file : '';
                // Link directly to the WooCommerce category archive for this vehicle's category
                $cat_url = get_term_link( $cat );
                if ( is_wp_error( $cat_url ) ) {
                    $cat_url = home_url( '/department/' . sanitize_title( $cat->name ) . '/' );
                }
                // WordPress counts already include all descendant products
                $product_count = $cat->count;
            ?>
            <a href="<?php echo esc_url( $cat_url ); ?>" class="mvp-category-card">
                <div class="mvp-category-card-img">
                    <?php if ( $cat_img_url ) : ?><img src="<?php echo esc_url( $cat_img_url ); ?>" alt="<?php echo esc_attr( $cat->name ); ?>" loading="lazy" onerror="this.style.display='none'"><?php endif; ?>
                </div>
                <div class="mvp-category-card-body">
                    <h3><?php echo esc_html( $cat->name ); ?></h3>
                    <span class="mvp-cat-count"><?php echo $product_count; ?> part<?php echo $product_count !== 1 ? 's' : ''; ?></span>
                </div>
            </a>
            <?php endforeach; ?>
        </div>
        <?php else : ?>
            <?php
            // No child categories - check if products are directly in this VIN category
            if ( $vin_term->count > 0 ) :
                // Products exist directly in VIN category - redirect to it
                $vin_cat_url = get_term_link( $vin_term );
                if ( ! is_wp_error( $vin_cat_url ) ) {
                    wp_redirect( $vin_cat_url, 302 );
                    exit;
                }
            endif;
            ?>
        <p style="text-align:center;color:#888;padding:40px 0;">No parts categories found for this vehicle yet.</p>
        <?php endif; ?>
    </div>

    <script>
    (function() {
        var expires = new Date();
        expires.setDate(expires.getDate() + 30);
        var exp = expires.toUTCString();
        var secure = location.protocol === 'https:' ? '; Secure' : '';
        var path = 'path=/; SameSite=Lax' + secure;
        document.cookie = 'mvp_vehicle_slug='   + encodeURIComponent('<?php echo esc_js( $mvp_vehicle_data['vehicle_slug'] ); ?>') + '; expires=' + exp + '; ' + path;
        document.cookie = 'mvp_vehicle_serial=' + encodeURIComponent('<?php echo esc_js( $mvp_vehicle_data['vin_serial'] ); ?>')   + '; expires=' + exp + '; ' + path;
        document.cookie = 'mvp_vehicle_model='  + encodeURIComponent('<?php echo esc_js( $model ); ?>')                             + '; expires=' + exp + '; ' + path;
        document.cookie = 'mvp_vehicle_year='   + encodeURIComponent('<?php echo esc_js( $year ); ?>')                              + '; expires=' + exp + '; ' + path;
    });
    </script>

    <?php
    get_footer();
}

// Rewrite hardcoded domain in nav menu department links to the current site URL.
// This means the same DB works on localhost and production without changes.
add_filter( 'wp_nav_menu_objects', 'mvp_fix_menu_dept_urls', 10, 2 );
function mvp_fix_menu_dept_urls( $items, $args ) {
    foreach ( $items as &$item ) {
        if ( ! empty( $item->url ) && strpos( $item->url, '/department/' ) !== false ) {
            $parsed = parse_url( $item->url );
            if ( ! empty( $parsed['path'] ) ) {
                $item->url = home_url( $parsed['path'] );
            }
        }
    }
    return $items;
}

// ============================================================
// 5b-i. DEPARTMENT SLUG → CATEGORY NAMES MAP
// ============================================================

function mvp_dept_get_slug_map() {
    return array(
        'air-conditioning' => array(
            'Air conditioning compressor',
            'Coolant Plumbing and Hardware',
            'Coolant Plumbing and Hardware-EV',
            'Coolant Plumbing and Hardware-FCV',
            'Coolant Plumbing and Hardware-PHEV',
            'Coolant Pump And Inl and Otlt TubeThermostat-EURO 5-6',
            'Coolant Pump And InlandOtltTube-D20',
            'CoolantPlumbingandHardware',
            'CoolantPumpAndInlandOtltTubeThermostat-EURO 4',
            'Front Interior HVAC Airflow',
            'FrontInteriorHVACAirflow',
            'FrontInteriorHVACAirflow-Left rudder',
            'FrontInteriorHVACAirflow-Right rudder',
            'Rear Interior Airflow',
            'Refrigerant Plumbing and Hardware',
            'Refrigerant Plumbing and Hardware-Electric vehicle',
            'Refrigerant Plumbing and Hardware-FCV',
            'Refrigerant Plumbing and Hardware-PHEV',
            'RefrigerantPlumbingandHardware',
            'Interior Heating Pipe',
            'Interior Heating Pipe-FCV',
            'InteriorHeatingPipeFront',
            'InteriorHeatingPipeRear',
        ),
        'belts-rollers' => array(
            'Safety Belts',
            'Seat Belts',
            'SAFETY BELTDRIVER、COPILOT',
            'Side PanelandRoof Safety Belt',
            'Second Row Seat Belts',
            'Third Row Safety Belts',
            'TimingDrive',
            'Timing Drive-D20',
            'DamperPulleyGearDrive',
            'AccessoryAccessory Drive-EURO 5-6',
            'AccessoryAccessoryDrive-EURO 4',
            'AccessoryandAccessory Drive-D20',
        ),
        'body' => array(
            'Body Attachment',
            'BodyAttachment',
            'Body Exterior Trim',
            'BodyExteriorTrim',
            'Body Interior and Exterior Electronics',
            'BodyInteriorandExteriorElectronics',
            'Body Lower Structure',
            'BodyLower Structure',
            'BodyLowerStructure',
            'body lower stucture',
            'Body Lower Structure Garnish Trim',
            'BodyLowerStructureGarnishTrim',
            'BodyUpperStructureGarnishTrim',
            'Body accessories harness',
            'BodyHarness',
            'Outer Framing',
            'Outer Framingleft side',
            'Outer Framingright side',
            'Outer Framing（left side）',
            'OuterFramingLeft Side',
            'OuterFramingRight Side',
            'Inner Framing',
            'inner framingleft side',
            'inner framingright side',
            'Inner Framing（left side）',
            'InnerFramingLeft Side',
            'InnerFramingRight Side',
            'Roof Framing',
            'RoofFraming',
            'RoofFramingChassis',
            'Rear Framing',
            'Frame',
            'Frame to Body Mounts',
            'Fenders',
            'Front Bumper',
            'FrontBumper',
            'Rear Bumper',
            'RearBumper',
            'Rear Panel',
            'Front Side Closure',
            'FrontSideClosure',
            'FrontSideClosureGarnishTrim',
            'Rear Side Closure',
            'SideClosureGarnishTrim',
            'Grille',
            'Hood',
            'Hood Lock',
            'HoodLock',
            'Endgate',
            'Mud Guard',
            'MudGuard',
            'Wheelhouse Liner',
            'WheelhouseLiner',
            'Exterior Emblem-Decal-Nameplate',
            'ExteriorEmblem-Decal-Nameplate',
            'Window',
            'SideWindows',
            'Front-RearWindow',
            'Assist Step',
            'On Vehicle Attachments',
            'OnVehicleAttachments',
            'On Vehicle Tools',
            'OnVehicleTools',
            'QE43BA001 - Body Structure Garnish Trim',
            'SE43BA001 - Body Structure Garnish Trim',
            'QE5A0A001 - cargo car body assembly',
            'QE5A1A001 - Platform Assembly',
            'QE5A2A001 - Side Panel-Inner Assembly',
            'QE5A4A001 - Front Panel Assembly',
            'QE5A5A001 - Side Panel-Outer Assembly',
            'SE5A1A001 - Platform Assembly',
            'SE5A4A001 - Front Panel Assembly',
            'SE5A5A001 - Side Panel-Outer Assembly',
            'PANEL ASM-BODY SI and R-END ASM-RR',
            'Baffle Plate-Ware',
            'Sound Insulation、Heat Insulation',
            'SoundInsulation、HeatInsulation',
            'Roof Trim',
            'RoofTrim',
            'MerchandiseTetherTreatment',
        ),
        'brakes' => array(
            'Brake Apply',
            'BrakeApplyandPlumbing',
            'Brake Modulator',
            'BrakeModulator',
            'Brake Pedal',
            'BrakePedals',
            'Brake Pipes',
            'Brake PipesABS',
            'Brake PipesESP',
            'BrakePlumbing',
            'Front Brakes',
            'FrontBrakeCorner',
            'Rear Brakes',
            'RearBrakeCorner',
            'Park Brake',
            'ParkBrake（LEFT Hand）',
            'ParkBrake（Right Hand）',
            'Mechanical Parking Brakes',
            'Rear Electric Parking Brakes',
            'Rear Mechanical Brakes',
            'Rear Disc Brake Corner',
            'REAR AXLE ASM-BRK',
        ),
        'damping' => array(
            'Front Shock Absorber',
            'FrontShockAbsorber',
            'Rear Shock Absorber',
            'RearShockAbsorber',
            'Five Bar Linkage Spiral Spring Rear Suspension',
            'Rear Leaf-spring Suspension',
            'Powertrain Mounts',
            'Powertrain Mounts-Electric vehicle',
            'PowertrainMounts5MT',
            'PowertrainMounts6MT-6AMT-9AT',
            'PowertrainMounts6MT-AMT',
            'EPT Mounts',
            'Frame to Body Mounts',
        ),
        'electrics' => array(
            'Air Bag Control Unit',
            'AirBag',
            'AirBagControlUnit',
            'FrontAirBag',
            'Antenna',
            'Auxiliary Information Electronics',
            'Battery and electric drive system',
            'Battery and Electrical Energy Storage',
            'BatteryandElectrical Energy Storage',
            'Battery Harness',
            'Battery Harnesses',
            'BatteryCable',
            'Body accessories harness',
            'BodyHarness',
            'Body Interior and Exterior Electronics',
            'BodyInteriorandExteriorElectronics',
            'Chassis Harness',
            'Chassis Harnesses',
            'ChassisHarness',
            'Clusters',
            'Door Harness',
            'DoorHarness',
            'Door Wire Harnesses',
            'Door Switches',
            'DoorSwitches',
            'Accessory Switch',
            'Accessory Switches',
            'AccessorySwitches',
            'Engine Compartment Fuse Box',
            'EngineCompartmentHarness',
            'Engine Management',
            'EngineManagement',
            'EPT System',
            'Fusebox-CabinCompartment',
            'Fusebox-Engine Compartment',
            'Fusebox-EngineCompartment',
            'GroundDistribution',
            'High Voltage Harness',
            'High Voltage Harness（EVandPHEV）',
            'High Voltage Harness（FCV）',
            'Infotainment System',
            'Instrument Panel Harness',
            'Instrument Panel Wire Harnesses',
            'InstrumentPanelHarness',
            'LightingSwitch',
            'Motor controller and accessories',
            'Moudule-Electric Vehicle Control Unit',
            'Moudule-Electric Vehicle Control UnitandEVCC',
            'Multi-Function Column Switch',
            'Multi-FunctionColumnSwitch',
            'Park Distance Control',
            'Park Distance Control System',
            'ParkDistanceControlSystem',
            'Passive Entry Passive Start',
            'Player',
            'Power assembly installation',
            'POWER BATTERY ASM',
            'power battery-EV',
            'Power Outlet and Cigarette Lighter Application',
            'Power Outlet and Cigarette Lighter Device',
            'Power Outlet and Cigarette Lighter HEvice',
            'PowerOutletandCigaretteLighterApplication',
            'PowerInverter',
            'BASEandMODULE-BATTERY（77KWhand88.8KWh）',
            'ChargingandEnergyStorage',
            'electric drive system',
            'Inside the power battery（CATL-88.55Kwh）',
            'The internal parts of power battery',
            'The internal parts of power battery-（CATL-88.55KWh）',
            'The internal parts of power battery（51.5KWh）',
            'The internal parts of power battery（77KWhand88.8KWh）',
            'RoofHarness',
            'SchoolbusElectronics',
            'SensorandHarness-D20',
            'SensorHarness-EURO 4',
            'SensorHarness-EURO 5',
            'SensorHarness-EURO 5-6',
            'Vehicle Date Recorder',
            'Vehicle Tele-Communication',
            'Window Lift Switch',
            'WindowLiftSwitch',
        ),
        'engine' => array(
            'Engine Accessory-D20',
            'Engine Accessory-EURO 5-6',
            'EngineAccessory',
            'Engine ASM-D20',
            'Engine ASM-D20（STP）',
            'Engine Management',
            'EngineManagement',
            'Engine-EURO 5-6',
            'Engine Compartment Fuse Box',
            'EngineCompartmentHarness',
            'Crankshaft Rod-D20',
            'CrankshaftRod',
            'Cylinder BlockandAccessory-D20',
            'Cylinder Head-D20',
            'CylinderBlockAccessory',
            'CylinderBlockCylinderLinerFlywheel',
            'CylinderHead',
            'DamperPulleyGearDrive',
            'EGR ASM-D20',
            'EGR ASM-EURO 4',
            'EGR ASM-EURO 5-6',
            'EmissionExhaustSystem',
            'EmissionExhaustSystem-Euro VI',
            'Exhaust ElbowandTurbocharger-D20',
            'Exhaust ElbowTurbocharger-EURO 5-6',
            'ExhaustElbowTurbocharger-EURO 4',
            'Exhaust system',
            'Exhaust system - D20',
            'Exhaust system - gasoline engine',
            'Fuel Heating System',
            'Fuel Plumbing and Hardware',
            'FuelPlumbingandHardware',
            'FuelPlumbingandHardware-D20',
            'FuelSystem',
            'Fuel Tank and Canister',
            'FuelTankandCanister',
            'HalfCylinderBlockGroup-EURO 5-6',
            'Head CoverandPCV-D20',
            'HeadCoverPCV',
            'Intake and Exhaust Manifold-EURO 5-6',
            'IntakeandExhaustManifold-EURO 4',
            'MANIFOLD ASM-INT-D20',
            'Lubricant',
            'Oil Cooler And Inl and Otlt TubeFilter-EURO 5-6',
            'Oil Cooler And InlandOtltTubeandFilter-D20',
            'OilCoolerAndInlandOtltTubeFilter-EURO 4',
            'Oil pumpsandvacuum pumpsandvacuum tube components-D20',
            'SHAFT-BALANCER-D20',
            'SumpandOil Suction PipeandDipstick-D20',
            'SumpOil Suction PipeDipstickBalancer-EURO 5-6',
            'Sump，OilSuctionPipeDipstickBalancer-EURO 4',
            'Timing Drive-D20',
            'TimingDrive',
            'Urea system',
            'Urea system-D20',
            'Urea system-Euro VI',
            'Air Cleaner',
            'AirCleaner',
            'Air Filter',
            'Air filter',
            'AccessoryAccessory Drive-EURO 5-6',
            'AccessoryAccessoryDrive-EURO 4',
            'AccessoryandAccessory Drive-D20',
            'Coolant Pump And Inl and Otlt TubeThermostat-EURO 5-6',
            'Coolant Pump And InlandOtltTube-D20',
            'CoolantPumpAndInlandOtltTubeThermostat-EURO 4',
            'JE11CA001 - Engine ASM',
            'JE11CA002 - Block Group',
            'JE11CB001 - Cylinder BlockandAccessory',
            'JE11CC001 - Cylinder Head',
            'JE11CD001 - Head CoverandPCV',
            'JE11CE001 - Crankshaft Rod',
            'JE11CF001 - SHAFT-BALANCER',
            'JE11CG001 - MANIFOLD ASM-INT',
            'JE11CH001 - Exhaust ElbowandTurbocharger',
            'JE11CI001 - Fuel System',
            'JE11CJ001 - Oil Cooler And InlandOtltTubeandFilter',
            'JE11CK001 - SumpandOil Suction PipeandDipstick',
            'JE11CL001 - Coolant Pump And InlandOtltTubeandThermostat',
            'JE11CM001 - Damper PulleyandGearDrive',
            'JE11CP001 - Timing Drive',
            'JE11CQ001 - AccessoryandAccessoryDrive',
            'JE11CR001 - SensorandHarness',
            'JE11CS001 - EGR ASM',
            'JE11CT001 - Engine Accessory',
            'JE11CU001 - LP-EGR intake pipeandAccessory',
            'JE11CW001 - Engine wiring harness',
            'JE11CX001 - Engine shield',
            'XE11CA001 - Engine ASM',
            'XE11CA002 - Block Group',
            'XE11CB001 - Cylinder BlockandAccessory',
            'XE11CC001 - Cylinder Head',
            'XE11CD001 - Head CoverandPCV',
            'XE11CE001 - Crankshaft Rod',
            'XE11CF001 - SHAFT-BALANCER',
            'XE11CG001 - MANIFOLD ASM-INT',
            'XE11CH001 - Exhaust ElbowandTurbocharger',
            'XE11CI001 - Fuel System',
            'XE11CJ001 - Oil Cooler And InlandOtltTubeandFilter',
            'XE11CK001 - SumpandOil Suction PipeandDipstick',
            'XE11CL001 - Coolant Pump And InlandOtltTubeandThermostat',
            'XE11CM001 - Damper PulleyandGearDrive',
            'XE11CP001 - Timing Drive',
            'XE11CQ001 - AccessoryandAccessoryDrive',
            'XE11CR001 - SensorandHarness',
            'XE11CS001 - EGR ASM',
            'XE11CT001 - Engine Accessory',
            'XE11CW001 - Engine wiring harness',
            'XE11CX001 - Engine shield',
        ),
        'filters' => array(
            'Air Filter',
            'Air filter',
            'Air Cleaner',
            'AirCleaner',
            'Coarse Filter and HardwareCuba',
            'Oil Cooler And Inl and Otlt TubeFilter-EURO 5-6',
            'Oil Cooler And InlandOtltTubeandFilter-D20',
            'OilCoolerAndInlandOtltTubeFilter-EURO 4',
            'Fuel Tank and Canister',
            'FuelTankandCanister',
            'Lubricant',
            'Urea system',
            'Urea system-D20',
            'Urea system-Euro VI',
            'TNK FIL DR',
        ),
        'induction' => array(
            'Air Cleaner',
            'AirCleaner',
            'Air Filter',
            'Air filter',
            'Coarse Filter and HardwareCuba',
            'Intake and Exhaust Manifold-EURO 5-6',
            'IntakeandExhaustManifold-EURO 4',
            'MANIFOLD ASM-INT-D20',
            'EGR ASM-D20',
            'EGR ASM-EURO 4',
            'EGR ASM-EURO 5-6',
            'Exhaust ElbowandTurbocharger-D20',
            'Exhaust ElbowTurbocharger-EURO 5-6',
            'ExhaustElbowTurbocharger-EURO 4',
            'JE11CG001 - MANIFOLD ASM-INT',
            'JE11CU001 - LP-EGR intake pipeandAccessory',
            'JE11CS001 - EGR ASM',
            'XE11CG001 - MANIFOLD ASM-INT',
            'XE11CS001 - EGR ASM',
        ),
        'ignition' => array(
            'Ignition Switch and Key',
            'IgnitionSwitchandKey',
            'Engine Management',
            'EngineManagement',
            'Accessory Switch',
            'Accessory Switches',
            'AccessorySwitches',
            'Passive Entry Passive Start',
            'Clusters',
        ),
        'interior' => array(
            '2014 Schoolbus Seat',
            '2015 School Seat',
            'CE42AQ002 - 62RIGHT RUDDER',
            'CE42BE001 - 11-SEATS',
            'CE42CA001 - Ix-SEAT',
            'CE42CB001 - RR DBL SEAT（W- RECL）',
            'CE42CC001 - OLD LUXURY H-SEAT',
            'CE42CD001 - RR DBL SEAT（W-O RECL）',
            'CE42CG001 - FRT SIN SEAT',
            'CE42CH001 - RR SIN SEAT（W- RECL）',
            'CE42CI001 - RR DBL SEAT（W- RECL）',
            'CE42CN001 - Single seat-Type 1',
            'CE42CP001 - DRIVER SEAT',
            'CE42CQ001 - DRIVER SEATright-hand',
            'CE42CR001 - DRIVER SEAT',
            'CE42CS001 - DRIVER SEAT',
            'CE42CT001 - FRT SIN SEAT',
            'CE42CT002 - FRT SIN SEAT',
            'CE42CU001 - FRT SIN SEAT',
            'CF1-CF2-SEAT',
            'Driver seat',
            'DRIVER SEAT left-hand',
            'Floor Console',
            'FloorConsole',
            'Floor Trim',
            'FloorTrim',
            'Front Door Trim',
            'Front double seats',
            'Front Electirc Seatleft',
            'Front Electirc Seatright',
            'Front Electrical Seat LH',
            'Front Electrical Seat RH',
            'Front Interior Control',
            'FrontInteriorControl',
            'Front Manual Seat LEFT',
            'Front Manual Seat LH',
            'Front Manual Seat RH',
            'Front Manual Seat（LH）',
            'Front Manual Seat（RH）',
            'Front Manual Seat（Right）',
            'Front SEAT left',
            'Front Seat Right',
            'Front SeatLeft',
            'Front Seat（left ）',
            'Front Seat（Left）',
            'Front Seat（Right）',
            'Frong Seat（right ）',
            'FRT DBL SEAT',
            'FRT DBL SEATW - RECL',
            'Infotainment System',
            'Instrument Panel',
            'Instrument Panel Crossmember',
            'Instrument Panel Crossmember（LHD）',
            'Instrument Panel Crossmember（RHD）',
            'Instrument Panel（LHD）',
            'Instrument Panel（RHD）',
            'InstrumentPanel',
            'InstrumentPanelCrossmember',
            'Interior Lamp',
            'InteriorLamp',
            'JE421AE001 - Seat Arrangement of Shang Jie\'s 11 12and 14 Seats Australia',
            'JE421AF001 - Three Seats Arrangement for VAN Vehicle Australia、New Zealand',
            'JE421AG001 - Two-Three Seats Arrangement for Chassis Vehicle Australia、New Zealand',
            'JE421AH001 - Arrangement for VAN Vehicle UK、Hong Kong',
            'JE421AI001 - Three Seats Arrangement for Chassis Vehicle UK、Hong Kong',
            'Player',
            'Power Outlet and Cigarette Lighter Application',
            'Power Outlet and Cigarette Lighter Device',
            'Power Outlet and Cigarette Lighter HEvice',
            'PowerOutletandCigaretteLighterApplication',
            'Rear Door trim',
            'Rear Door Trim',
            'RearDoortrim',
            'Rear Roll Double Seat',
            'Rear Row Seat',
            'RR 3-SEAT（W- RECL）',
            'RR SIN SEAT（W- RECL）',
            'RR SIN WIDE SEAT',
            'Safety Belts',
            'Seat Belts',
            'SAFETY BELTDRIVER、COPILOT',
            'Seats Layout',
            'Second Row Double seat',
            'Second Row Seat Belts',
            'Second Row Three Seat（Two head rest - three head rest）',
            'Side PanelandRoof Safety Belt',
            'Side Sliding Door',
            'Side Sliding Door guide rail',
            'Side Sliding Door Handle and Door Lock',
            'Side Sliding Door trim',
            'SideSlidingDoor',
            'SideSlidingDoorHandle',
            'SideSlidingDoorLock',
            'SideSlidingDoortrim',
            'Side Trim',
            'Sound Insulation、Heat Insulation',
            'SoundInsulation、HeatInsulation',
            'Speaker',
            'STANDARD 12 -16-SEAT',
            'Subdrivers Integral Double Seat',
            'Subdrivers Split Double Seat',
            'Third Row Safety Belts',
            'VAN 2-SEAT',
            'VAN 3-SEAT',
            'Window Lift Switch',
            'WindowLiftSwitch',
            'Door Trim',
            'Door Switches',
            'DoorSwitches',
            'ELEC SWINGING DR',
            'Assist Step',
            'Roof Trim',
            'RoofTrim',
        ),
        'lighting' => array(
            'Front Lamp',
            'FrontLamp',
            'Interior Lamp',
            'InteriorLamp',
            'Rear Lamp',
            'RearLamp',
            'LightingSwitch',
            'LSH14C4C5NA129710',
        ),
        'oils-and-fluids' => array(
            'Fluids and Lubrications',
            'FluidsandLubrications',
            'Lubricant',
            'Urea system',
            'Urea system-D20',
            'Urea system-Euro VI',
        ),
        'wiper-and-washers' => array(
            'Wiper',
            'Wiper（LHD）',
            'Wiper（RHD）',
            'Front Wiper',
            'Front Washer',
            'Washer',
            'Washer System',
        ),
        'suspension' => array(
            'Front Suspension',
            'FrontSuspension',
            'Rear Suspension',
            'RearSuspension',
            'Front Sub-frame',
            'FrontSub-frame',
            'Front Shock Absorber',
            'FrontShockAbsorber',
            'Rear Shock Absorber',
            'RearShockAbsorber',
            'Five Bar Linkage Spiral Spring Rear Suspension',
            'Rear Leaf-spring Suspension',
            'Front Drive Axle',
            'Front Half Shaft',
            'Front Half Shafts',
            'Rear Axle （Front drive vehicle）',
            'Rear Drive Axle',
            'Rear Drive Axle（YUE JIN）',
            'Rear Driven Axle',
            'Rear Electric Drive Axle',
            'REAR AXLE ASM-BRK',
        ),
        'tires' => array(
            'TireWheelsWheelTrim',
            'TireWheelTrim',
            'Spare Tire Device',
            'SpareTireBracket',
            'Wheelhouse Liner',
            'WheelhouseLiner',
        ),
        'steering' => array(
            'Steering Column',
            'SteeringColumn',
            'Steering Wheel and AirBag',
            'SteeringWheel',
            'PowerSteeringPlumbingandPipe',
            'Redirector',
            'Redirectorleft hand）',
            'Redirectorright hand）',
            'Redirector（Left Hand-Right Hand）',
            'Electirc redirector（Left-Right Hand',
            'Multi-Function Column Switch',
            'Multi-FunctionColumnSwitch',
            'Air Bag Control Unit',
            'AirBag',
            'AirBagControlUnit',
            'FrontAirBag',
        ),
        'transmission' => array(
            'Clutch Apply',
            'ClutchApply5MT',
            'ClutchApply6MT',
            'ClutchMT',
            'ClutchPHEV',
            'CLUTCH HOUSING-6MT Front Driveand6AMT',
            'CLUTCH HOUSING-6MTand6AMT',
            'Clutch-5MT',
            'Clutch-6MT-6AMT',
            'Differential-SAGW 6AMTand6MT',
            'Differential-WIA 6MT',
            'Manual transmission assembly',
            'Manual transmission assembly（6MT Front-Back drive）',
            'Propeller Shaft',
            'Propshaft',
            'QE121AA01 - Oil Pan Kit',
            'QE121AA04 - Mechatronic Kit',
            'QE121AA05 - Shaft Sealing Ring Output',
            'QE121AA07 - Converter Kit',
            'QE121AA08 - Converter Sealing Elements Kit',
            'QE121AA09 - Selector Shaft Sealing Ring Kit',
            'QE121AA10 - Breather Tube Kit',
            'QE121AA11 - Mechatronic Sealing elements replacement',
            'The internal parts of reduction',
            'Transfer CasePart time 4WD',
            'Transfer Casetorque on demand',
            'Transmission accessory-5MT',
            'Transmission accessory-6MT Front Drive',
            'Transmission accessory-SAGW 6AMT',
            'Transmission assembly6AT',
            'Transmission assembly8AT',
            'Transmission assemblySAGW-6MT',
            'Transmission body-5MT',
            'Transmission body-SAGW 6MTand6AMT',
            'Transmission body-WIA 6MT',
            'Transmission CSC and Operating Mechanism6MT back drive',
            'Transmission Differential-6MT Front Drive',
            'Transmission Differential-6MT Front Driveand6AMT',
            'Transmission Fork ComponentsSAGW-6MT back drive',
            'Transmission fork-6MT Front Drive',
            'Transmission fork-6MT Front Driveand6MT',
            'Transmission Gear-5MT',
            'Transmission Input Shaft And Gear-WIA 6MT',
            'Transmission Main Shaft And Gear6MT back drive',
            'Transmission Oil Cooler and Plumbing Hardware',
            'Transmission operating mechanism-6MT',
            'Transmission operating mechanism-6MT Front Drive',
            'Transmission operating mechanism-6MT-E5',
            'Transmission operating mechanism-SAGW 6MT',
            'Transmission operating mechanism-WIA 6MT',
            'Transmission operating mechanism6AMT',
            'Transmission Output Shaft And Gear-WIA 6MT',
            'Transmission RVS Idler Shaft Gear-6MT Front Drive',
            'Transmission RVS Idler Shaft Gear-6MT Front Driveand6AMT',
            'Transmission RVS Idler Shaft Gear-SAGW 6AMTand6MT',
            'Transmission RVS Idler Shaft Gear-WIA 6MT',
            'Transmission Seal-6MT Front Drive',
            'Transmission shaft ASM-6MT Front Drive',
            'Transmission shaft ASM-6MT Front Driveand6AMT',
            'Transmission shaft ASM-SAGW 6AMTand6MT',
            'Transmission Shaft INPUT-6MT Front Drive',
            'Transmission Shaft INPUT-6MT Front Driveand6AMT',
            'Transmission Shaft INPUT-SAGW 6MTand6AMT',
            'Transmission Shaft OUTPUT（1256）-6MT Front Drive',
            'Transmission Shaft OUTPUT（1256）-6MT Front Driveand6AMT',
            'Transmission Shaft OUTPUT（1256）-SAGW 6MTand6AMT',
            'Transmission Shaft OUTPUT（34R）-6MT Front Drive',
            'Transmission Shaft OUTPUT（34R）-6MT Front Driveand6AMT',
            'Transmission Shaft OUTPUT（34R）-SAGW 6MTand6AMT',
            'Transmission shell Bearing-6MT Front Drive',
            'Transmission shell Bearing-6MT Front Drive and 6AMT',
            'Transmission shell-6MT Front Drive',
            'Transmission shell-6MTand6AMT',
            'Transmission Shift Actuation',
            'Transmission Shift Actuation-AMT',
            'Transmission Shift Actuation-AT、Electric vehicle',
            'Transmission Shift Actuation-MT',
            'Transmission shift forks-SAGW 6AMTand6MT',
            'Transmissionassembly and accessory-SAGW 6MT',
            'Transmissionassembly and CSC-WIA 6MT',
            'TransmissionassemblyandTCU and CSC-SAGW 6AMT',
            'TransmissionShiftActuation',
            'TransmissionShiftActuation-6AMT',
            'TransmissionShiftActuation-6AMTand9AT',
            'TransmissionShiftActuation-MT5MT',
            'TransmissionShiftActuation-MT6MT',
            'Power assembly installation',
        ),
    );
}

// Sidebar display names keyed by slug
function mvp_dept_get_display_names() {
    return array(
        'air-conditioning' => 'Air Conditioning',
        'belts-rollers'    => 'Belts &amp; Rollers',
        'body'             => 'Body',
        'brakes'           => 'Brakes',
        'damping'          => 'Damping',
        'electrics'        => 'Electrics',
        'engine'           => 'Engine',
        'filters'          => 'Filters',
        'induction'        => 'Induction',
        'ignition'         => 'Ignition',
        'interior'         => 'Interior',
        'lighting'         => 'Lighting',
        'oils-and-fluids'  => 'Oils &amp; Fluids',
        'wiper-and-washers'=> 'Wipers &amp; Washers',
        'suspension'       => 'Suspension',
        'tires'            => 'Tires',
        'steering'         => 'Steering',
        'transmission'     => 'Transmission',
    );
}

// ============================================================
// 5b. DEPARTMENT PAGES — /department/{slug}/ and /department/{slug}/{vehicle-slug}/
// ============================================================

// Auto-flush rewrite rules when theme version changes (e.g. after deployment).
// Bump MVp_REWRITE_VERSION whenever new rewrite rules are added.
define( 'MVP_REWRITE_VERSION', '3' );
add_action( 'init', 'mvp_maybe_flush_rewrite_rules', 99 );
function mvp_maybe_flush_rewrite_rules() {
    if ( get_option( 'mvp_rewrite_version' ) !== MVP_REWRITE_VERSION ) {
        flush_rewrite_rules( false );
        update_option( 'mvp_rewrite_version', MVP_REWRITE_VERSION, false );
    }
}

// Register rewrite rules for department pages
add_action( 'init', 'mvp_department_rewrite_rules' );
function mvp_department_rewrite_rules() {
    // /department/{cat-slug}/{vehicle-slug}/ → show products for that vehicle's category
    add_rewrite_rule(
        '^department/([^/]+)/([^/]+)/?$',
        'index.php?mvp_department=$matches[1]&mvp_dept_vehicle=$matches[2]',
        'top'
    );
    // /department/{cat-slug}/ → show all vehicles with that category
    add_rewrite_rule(
        '^department/([^/]+)/?$',
        'index.php?mvp_department=$matches[1]',
        'top'
    );
}

// Register query vars
add_filter( 'query_vars', 'mvp_department_query_vars' );
function mvp_department_query_vars( $vars ) {
    $vars[] = 'mvp_department';
    $vars[] = 'mvp_dept_vehicle';
    return $vars;
}

// Prevent 404 for department pages
add_action( 'pre_get_posts', 'mvp_department_prevent_404' );
function mvp_department_prevent_404( $query ) {
    if ( ! $query->is_main_query() ) return;
    if ( $query->get( 'mvp_department' ) ) {
        $query->is_404 = false;
    }
}

// Render department pages via template_redirect
add_action( 'template_redirect', 'mvp_department_template_redirect' );
function mvp_department_template_redirect() {
    $dept_slug = get_query_var( 'mvp_department' );
    if ( ! $dept_slug ) return;

    // Add Vary header so caches (Cloudflare) know response depends on cookies
    header( 'Vary: Cookie', false );

    $vehicle_slug = get_query_var( 'mvp_dept_vehicle' );

    // If vehicle slug present, show intermediate category page for that vehicle+department
    if ( $vehicle_slug ) {
        mvp_department_vehicle_redirect( $dept_slug, $vehicle_slug );
        return;
    }

    // No vehicle in URL — check for saved vehicle cookie and auto-redirect if present
    // Skip redirect if ?all=1 (user clicked View all vehicles)
    if ( ! $vehicle_slug && ! empty( $_COOKIE['mvp_vehicle_slug'] ) && empty( $_GET['all'] ) ) {
        $cookie_slug = sanitize_title( wp_unslash( $_COOKIE['mvp_vehicle_slug'] ) );
        if ( $cookie_slug ) {
            // Add nocache header to prevent caching of redirect
            header( 'Cache-Control: no-cache, must-revalidate, max-age=0', false );
            $redirect_url = home_url( '/department/' . $dept_slug . '/' . $cookie_slug . '/' );
            wp_redirect( $redirect_url, 302 );
            exit;
        }
    }

    // Show department page with all vehicles that have this category
    global $wp_query;
    $wp_query->is_404 = false;
    status_header( 200 );

    mvp_department_render_page( $dept_slug );
    exit;
}

// Render an intermediate category-listing page for /department/{cat}/{vehicle}/
function mvp_department_vehicle_redirect( $dept_slug, $vehicle_slug ) {
    $maxus_term_id = mvp_get_maxus_term_id();

    // Find VIN term by vehicle_slug meta
    $vin_terms = get_terms( array(
        'taxonomy'   => 'product_cat',
        'parent'     => $maxus_term_id,
        'hide_empty' => false,
        'meta_query' => array( array( 'key' => 'vehicle_slug', 'value' => sanitize_title( $vehicle_slug ) ) ),
    ) );

    if ( is_wp_error( $vin_terms ) || empty( $vin_terms ) ) {
        global $wp_query;
        $wp_query->set_404();
        status_header( 404 );
        return;
    }

    $vin_term = $vin_terms[0];

    // Build allowed slug set from the map
    $slug_map      = mvp_dept_get_slug_map();
    $display_names = mvp_dept_get_display_names();
    $allowed_names = isset( $slug_map[ $dept_slug ] ) ? $slug_map[ $dept_slug ] : array();
    $allowed_slugs = array_map( 'sanitize_title', $allowed_names );
    $use_fallback  = empty( $allowed_slugs );
    $dept_name_clean = str_replace( '-', ' ', $dept_slug );

    $dept_display_name = isset( $display_names[ $dept_slug ] )
        ? html_entity_decode( $display_names[ $dept_slug ] )
        : ucwords( $dept_name_clean );

    $vehicle_model = get_term_meta( $vin_term->term_id, 'vehicle_model', true );
    $vehicle_year  = get_term_meta( $vin_term->term_id, 'vehicle_year', true );

    // Get all descendants, build parent→children map and identify leaves
    $all_cats = get_terms( array(
        'taxonomy'   => 'product_cat',
        'child_of'   => $vin_term->term_id,
        'hide_empty' => true,
    ) );

    // Build lookup maps
    $cat_by_id        = array();
    $has_children_ids = array();
    $children_of      = array(); // parent_id => [ child, ... ]

    if ( ! is_wp_error( $all_cats ) && ! empty( $all_cats ) ) {
        foreach ( $all_cats as $c ) {
            $cat_by_id[ $c->term_id ] = $c;
            $has_children_ids[ $c->parent ] = true;
            $children_of[ $c->parent ][] = $c;
        }
    }

    // Filter to leaf cats that match the department mapping
    $matching_leaves = array();
    if ( ! empty( $cat_by_id ) ) {
        foreach ( $cat_by_id as $c ) {
            if ( isset( $has_children_ids[ $c->term_id ] ) ) continue; // not a leaf
            $matches = $use_fallback
                ? ( sanitize_title( $c->name ) === sanitize_title( $dept_name_clean ) || sanitize_title( $c->name ) === $dept_slug )
                : in_array( sanitize_title( $c->name ), $allowed_slugs, true );
            if ( $matches ) {
                $matching_leaves[ $c->term_id ] = $c;
            }
        }
    }

    // If only one match, redirect straight to it
    if ( count( $matching_leaves ) === 1 ) {
        $only = reset( $matching_leaves );
        $url  = get_term_link( $only );
        if ( ! is_wp_error( $url ) ) {
            wp_redirect( $url, 302 );
            exit;
        }
    }

    // Show every matching leaf directly so the user sees all individual sub-categories.
    $display_cats = array();
    foreach ( $matching_leaves as $leaf ) {
        $display_cats[ $leaf->term_id ] = array( 'term' => $leaf, 'count' => $leaf->count );
    }

    // Sort by name
    uasort( $display_cats, function( $a, $b ) {
        return strcmp( $a['term']->name, $b['term']->name );
    } );

    // Render the intermediate page
    global $wp_query;
    $wp_query->is_404 = false;
    status_header( 200 );

    get_header();
    ?>
    <style>
    .mvp-vdept-page {
        max-width: 1300px;
        margin: 0 auto;
        padding: 30px 20px 60px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .mvp-vdept-header {
        margin-bottom: 35px;
        padding-bottom: 25px;
        border-bottom: 2px solid #f0f0f0;
    }
    .mvp-vdept-breadcrumb {
        font-size: 14px;
        color: #aaa;
        margin-bottom: 8px;
    }
    .mvp-vdept-breadcrumb a { color: #034C8C; text-decoration: none; }
    .mvp-vdept-breadcrumb a:hover { color: #F29F05; }
    .mvp-vdept-header h1 {
        font-size: 28px;
        font-weight: 700;
        color: #1a1a2e;
        margin: 0 0 4px;
    }
    .mvp-vdept-header .mvp-vdept-subtitle {
        font-size: 15px;
        color: #666;
        margin: 0;
    }
    .mvp-vdept-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
        gap: 18px;
    }
    .mvp-vdept-card {
        background: #fff;
        border: 1px solid #eee;
        border-radius: 12px;
        padding: 22px 20px;
        text-decoration: none;
        color: #1a1a2e;
        transition: transform 0.25s, box-shadow 0.25s;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .mvp-vdept-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.09);
        border-color: #034C8C;
    }
    .mvp-vdept-card-name {
        font-size: 15px;
        font-weight: 700;
        color: #1a1a2e;
    }
    .mvp-vdept-card-count {
        font-size: 13px;
        color: #034C8C;
        font-weight: 600;
    }
    .mvp-vdept-card-img {
        width: 100%;
        height: 150px;
        background: #f5f5f5;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }
    .mvp-vdept-card-img img {
        max-width: 90%;
        max-height: 130px;
        object-fit: contain;
    }
    .mvp-vdept-card.has-img {
        padding: 12px 12px 18px;
    }
    @media (max-width: 600px) {
        .mvp-vdept-grid { grid-template-columns: 1fr 1fr; gap: 12px; }
    }
    .mvp-vehicle-notice {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        background: #f0f5ff;
        border: 1px solid #c7d9f7;
        border-radius: 8px;
        padding: 12px 18px;
        margin-bottom: 28px;
        flex-wrap: wrap;
    }
    .mvp-vehicle-notice-text {
        font-size: 14px;
        color: #333;
        line-height: 1.5;
    }
    .mvp-vehicle-notice-text strong {
        color: #1a1a2e;
    }
    .mvp-vehicle-notice-change {
        display: inline-block;
        font-size: 13px;
        font-weight: 600;
        color: #fff;
        background: #BF3617;
        border-radius: 6px;
        padding: 7px 16px;
        text-decoration: none;
        white-space: nowrap;
        flex-shrink: 0;
        cursor: pointer;
        border: none;
    }
    .mvp-vehicle-notice-change:hover {
        background: #a82e13;
        color: #fff;
    }
    .mvp-vehicle-notice-change.mvp-view-all {
        background: #BF3617;
    }
    .mvp-vehicle-notice-change.mvp-view-all:hover {
        background: #a82e13;
    }
    </style>

    <div class="mvp-vdept-page">
        <div class="mvp-vdept-header">
            <p class="mvp-vdept-breadcrumb">
                <a href="<?php echo home_url('/'); ?>">Home</a> &rsaquo;
                <a href="<?php echo home_url( '/department/' . $dept_slug . '/' ); ?>"><?php echo esc_html( $dept_display_name ); ?></a> &rsaquo;
                <?php echo esc_html( $vehicle_model ); ?>
            </p>
            <h1><?php echo esc_html( $dept_display_name ); ?> &mdash; <?php echo esc_html( $vehicle_model ); ?></h1>
            <p class="mvp-vdept-subtitle"><?php echo esc_html( $vehicle_year ); ?> &bull; Select a category to view parts</p>
        </div>

        <div class="mvp-vehicle-notice">
            <span class="mvp-vehicle-notice-text">
                Showing <strong><?php echo esc_html( $dept_display_name ); ?></strong> parts for your saved vehicle: <strong><?php echo esc_html( $vehicle_model ); ?><?php if ( $vehicle_year ) : ?> (<?php echo esc_html( $vehicle_year ); ?>)<?php endif; ?></strong>
            </span>
            <a class="mvp-vehicle-notice-change" href="#" onclick="mvpClearVehicleCookies(); return false;">&#8635; Change vehicle</a>
            <a class="mvp-vehicle-notice-change mvp-view-all" href="<?php echo esc_url( home_url( '/department/' . $dept_slug . '/?all=1' ) ); ?>">View all vehicles</a>
        </div>

        <?php if ( ! empty( $display_cats ) ) : ?>
        <div class="mvp-vdept-grid">
            <?php foreach ( $display_cats as $dc ) :
                $term_url = get_term_link( $dc['term'] );
                if ( is_wp_error( $term_url ) ) continue;
            ?>
            <?php
                $img_name = mvp_category_icon_file( $dc['term']->name );
                $has_img  = ( $img_name !== '' );
            ?>
            <a href="<?php echo esc_url( $term_url ); ?>" class="mvp-vdept-card<?php echo $has_img ? ' has-img' : ''; ?>">
                <?php if ( $has_img ) : ?>
                <span class="mvp-vdept-card-img"><img src="<?php echo esc_url( content_url( '/uploads/categories/' . $img_name ) ); ?>" alt="<?php echo esc_attr( $dc['term']->name ); ?>" /></span>
                <?php endif; ?>
                <span class="mvp-vdept-card-name"><?php echo esc_html( $dc['term']->name ); ?></span>
                <span class="mvp-vdept-card-count"><?php echo (int) $dc['count']; ?> part<?php echo $dc['count'] !== 1 ? 's' : ''; ?></span>
            </a>
            <?php endforeach; ?>
        </div>
        <?php else : ?>
        <p style="text-align:center;color:#888;padding:40px 0;">No parts found for this vehicle in <?php echo esc_html( $dept_display_name ); ?>.</p>
        <?php endif; ?>
    </div>

    <script>
    (function() {
        var expires = new Date();
        expires.setDate(expires.getDate() + 30);
        var exp = expires.toUTCString();
        var secure = location.protocol === 'https:' ? '; Secure' : '';
        var path = 'path=/; SameSite=Lax' + secure;
        document.cookie = 'mvp_vehicle_slug='   + encodeURIComponent('<?php echo esc_js( $vehicle_slug ); ?>') + '; expires=' + exp + '; ' + path;
        document.cookie = 'mvp_vehicle_serial=' + encodeURIComponent('<?php echo esc_js( $vin_term->slug ); ?>') + '; expires=' + exp + '; ' + path;
        document.cookie = 'mvp_vehicle_model='  + encodeURIComponent('<?php echo esc_js( $vehicle_model ); ?>') + '; expires=' + exp + '; ' + path;
        document.cookie = 'mvp_vehicle_year='   + encodeURIComponent('<?php echo esc_js( $vehicle_year ); ?>') + '; expires=' + exp + '; ' + path;
    });
    function mvpClearVehicleCookies() {
        var past = 'Thu, 01 Jan 1970 00:00:00 UTC';
        var keys = ['mvp_vehicle_slug', 'mvp_vehicle_serial', 'mvp_vehicle_model', 'mvp_vehicle_year'];
        keys.forEach(function(k) {
            document.cookie = k + '=; expires=' + past + '; path=/; SameSite=Lax';
        });
        window.location.href = '<?php echo esc_js( home_url( '/#mvp-vehicles' ) ); ?>';
    }
    </script>

    <?php
    get_footer();
    exit;
}

// Render the department page showing all vehicles with this category
function mvp_department_render_page( $dept_slug ) {
    $maxus_term_id = mvp_get_maxus_term_id();

    // Resolve display name and allowed category list from map
    $slug_map      = mvp_dept_get_slug_map();
    $display_names = mvp_dept_get_display_names();
    $allowed_names = isset( $slug_map[ $dept_slug ] ) ? $slug_map[ $dept_slug ] : array();
    $allowed_slugs = array_map( 'sanitize_title', $allowed_names );
    $use_fallback  = empty( $allowed_slugs );
    $dept_name_clean = str_replace( '-', ' ', $dept_slug );

    $dept_display_name = isset( $display_names[ $dept_slug ] )
        ? html_entity_decode( $display_names[ $dept_slug ] )
        : ucwords( $dept_name_clean );

    // Get all VIN terms
    $vin_terms = get_terms( array(
        'taxonomy'   => 'product_cat',
        'parent'     => $maxus_term_id,
        'hide_empty' => false,
        'orderby'    => 'name',
    ) );

    $vehicles_with_dept = array();
    $cat_img_base = 'https://shane.maxusvanparts.co.uk/wp-content/uploads/categories/';

    if ( ! is_wp_error( $vin_terms ) ) {
        foreach ( $vin_terms as $vin_term ) {
            $model = get_term_meta( $vin_term->term_id, 'vehicle_model', true );
            $slug  = get_term_meta( $vin_term->term_id, 'vehicle_slug', true );
            if ( ! $model || ! $slug ) continue;

            // Get all descendant categories and match against leaf nodes only
            $all_cats = get_terms( array(
                'taxonomy'   => 'product_cat',
                'child_of'   => $vin_term->term_id,
                'hide_empty' => true,
            ) );

            if ( is_wp_error( $all_cats ) || empty( $all_cats ) ) continue;

            $has_children_ids = array();
            foreach ( $all_cats as $c ) {
                $has_children_ids[ $c->parent ] = true;
            }
            $leaf_cats = array_filter( $all_cats, function( $c ) use ( $has_children_ids ) {
                return ! isset( $has_children_ids[ $c->term_id ] );
            } );

            // Accumulate product count across ALL matching leaf cats for this vehicle
            $total_count = 0;
            foreach ( $leaf_cats as $cat ) {
                $matches = $use_fallback
                    ? ( sanitize_title( $cat->name ) === sanitize_title( $dept_name_clean ) || sanitize_title( $cat->name ) === $dept_slug )
                    : in_array( sanitize_title( $cat->name ), $allowed_slugs, true );
                if ( $matches ) {
                    $total_count += $cat->count;
                }
            }

            if ( $total_count > 0 ) {
                $year = get_term_meta( $vin_term->term_id, 'vehicle_year', true );
                $img  = get_term_meta( $vin_term->term_id, 'vehicle_image', true );

                $vehicles_with_dept[] = array(
                    'model'         => $model,
                    'year'          => $year,
                    'img'           => $img,
                    'vehicle_slug'  => $slug,
                    'product_count' => $total_count,
                );
            }
        }
    }

    // Category image with fallback matching
    $cat_img_name  = mvp_category_icon_file( $dept_display_name );
    $cat_img_found = ( $cat_img_name !== '' );
    $cat_img_url   = $cat_img_found ? $cat_img_base . $cat_img_name : '';

    get_header();
    ?>
    <style>
    .mvp-dept-page {
        max-width: 1300px;
        margin: 0 auto;
        padding: 30px 20px 60px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .mvp-dept-header {
        display: flex;
        align-items: center;
        gap: 24px;
        margin-bottom: 35px;
        padding-bottom: 25px;
        border-bottom: 2px solid #f0f0f0;
    }
    .mvp-dept-header-img {
        width: 100px;
        height: 100px;
        background: #f8f8f8;
        border-radius: 12px;
        overflow: hidden;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .mvp-dept-header-img img {
        max-width: 85%;
        max-height: 85%;
        object-fit: contain;
    }
    .mvp-dept-header-info h1 {
        font-size: 32px;
        font-weight: 700;
        color: #1a1a2e;
        margin: 0 0 6px;
    }
    .mvp-dept-header-info .mvp-dept-breadcrumb {
        font-size: 14px;
        color: #aaa;
    }
    .mvp-dept-header-info .mvp-dept-breadcrumb a {
        color: #034C8C;
        text-decoration: none;
    }
    .mvp-dept-header-info .mvp-dept-breadcrumb a:hover { color: #F29F05; }
    .mvp-dept-subtitle {
        font-size: 16px;
        color: #666;
        margin: 6px 0 0;
    }
    .mvp-dept-vehicle-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: 20px;
    }
    .mvp-dept-vehicle-card {
        background: #fff;
        border: 1px solid #eee;
        border-radius: 12px;
        overflow: hidden;
        text-decoration: none;
        color: #333;
        transition: transform 0.3s, box-shadow 0.3s;
        display: flex;
        flex-direction: column;
    }
    .mvp-dept-vehicle-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    .mvp-dept-vehicle-card-img {
        width: 100%;
        height: 160px;
        background: #f5f5f5;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        padding: 15px;
        box-sizing: border-box;
    }
    .mvp-dept-vehicle-card-img img {
        max-width: 100%;
        max-height: 130px;
        object-fit: contain;
    }
    .mvp-dept-vehicle-card-body {
        padding: 16px 18px;
        border-top: 1px solid #f0f0f0;
    }
    .mvp-dept-vehicle-card-body h3 {
        font-size: 16px;
        font-weight: 700;
        color: #1a1a2e;
        margin: 0 0 4px;
    }
    .mvp-dept-vehicle-card-body .mvp-dept-year {
        font-size: 13px;
        color: #888;
        margin: 0 0 8px;
    }
    .mvp-dept-vehicle-card-body .mvp-dept-parts {
        font-size: 13px;
        color: #034C8C;
        font-weight: 600;
    }
    @media (max-width: 768px) {
        .mvp-dept-header { flex-direction: column; text-align: center; line-height: 48px; gap: 16px; }
        .mvp-dept-header-img { width: 80px; height: 80px; }
        .mvp-dept-header-info h1 { font-size: 24px; }
        .mvp-dept-vehicle-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 14px; }
        .mvp-dept-vehicle-card-img { height: 120px; }
    }
    @media (max-width: 480px) {
        .mvp-dept-vehicle-grid { grid-template-columns: 1fr 1fr; gap: 10px; }
        .mvp-dept-vehicle-card-body { padding: 12px 14px; }
        .mvp-dept-vehicle-card-body h3 { font-size: 14px; }
    }
    </style>

    <div class="mvp-dept-page">
        <div class="mvp-dept-header">
            <?php if ( $cat_img_url ) : ?>
            <div class="mvp-dept-header-img">
                <img src="<?php echo esc_url( $cat_img_url ); ?>" alt="<?php echo esc_attr( $dept_display_name ); ?>"
                     onerror="this.parentElement.style.display='none'">
            </div>
            <?php endif; ?>
            <div class="mvp-dept-header-info">
                <p class="mvp-dept-breadcrumb"><a href="<?php echo home_url('/'); ?>">Home</a> &rsaquo; <?php echo esc_html( $dept_display_name ); ?></p>
                <h1><?php echo esc_html( $dept_display_name ); ?></h1>
                <p class="mvp-dept-subtitle">Select your vehicle to view <?php echo esc_html( strtolower( $dept_display_name ) ); ?> parts</p>
            </div>
        </div>

        <?php if ( ! empty( $vehicles_with_dept ) ) : ?>
        <div class="mvp-dept-vehicle-grid">
            <?php foreach ( $vehicles_with_dept as $v ) :
                $cat_url = home_url( '/department/' . $dept_slug . '/' . $v['vehicle_slug'] . '/' );
            ?>
            <a href="<?php echo esc_url( $cat_url ); ?>" class="mvp-dept-vehicle-card">
                <div class="mvp-dept-vehicle-card-img">
                    <?php if ( $v['img'] ) : ?>
                    <img src="<?php echo esc_url( $v['img'] ); ?>" alt="<?php echo esc_attr( $v['model'] ); ?>" loading="lazy">
                    <?php endif; ?>
                </div>
                <div class="mvp-dept-vehicle-card-body">
                    <h3><?php echo esc_html( $v['model'] ); ?></h3>
                    <p class="mvp-dept-year"><?php echo esc_html( $v['year'] ); ?></p>
                    <p class="mvp-dept-parts"><?php echo $v['product_count']; ?> part<?php echo $v['product_count'] !== 1 ? 's' : ''; ?></p>
                </div>
            </a>
            <?php endforeach; ?>
        </div>
        <?php else : ?>
        <p style="text-align:center;color:#888;padding:40px 0;">No vehicles found with <?php echo esc_html( $dept_display_name ); ?> parts.</p>
        <?php endif; ?>
    </div>
    <?php
    get_footer();
}

// ============================================================
// 6. VEHICLE DATA HELPER — Returns all VIN-to-vehicle mappings
// ============================================================
function mvp_get_vehicle_vins() {
    $maxus_term_id = mvp_get_maxus_term_id();
    $vin_terms = get_terms( array(
        'taxonomy'   => 'product_cat',
        'parent'     => $maxus_term_id,
        'hide_empty' => false,
    ) );

    $vehicles = array();
    if ( is_wp_error( $vin_terms ) ) return $vehicles;

    foreach ( $vin_terms as $term ) {
        $model = get_term_meta( $term->term_id, 'vehicle_model', true );
        $year  = get_term_meta( $term->term_id, 'vehicle_year', true );
        $slug  = get_term_meta( $term->term_id, 'vehicle_slug', true );
        $img   = get_term_meta( $term->term_id, 'vehicle_image', true );
        if ( ! $model || ! $slug ) continue;

        $vehicles[ $slug ] = array(
            'vin'     => strtoupper( $term->name ),
            'name'    => $model,
            'year'    => $year,
            'img'     => $img,
            'term_id' => $term->term_id,
        );
    }
    return $vehicles;
}

// ============================================================
// 7. VIN LOOKUP — AJAX handler
// ============================================================
add_action( 'wp_ajax_maxus_vin_lookup', 'mvp_vin_lookup' );
add_action( 'wp_ajax_nopriv_maxus_vin_lookup', 'mvp_vin_lookup' );
function mvp_vin_lookup() {
    $vin = isset( $_POST['vin'] ) ? sanitize_text_field( $_POST['vin'] ) : '';
    $vin = strtoupper( preg_replace( '/[^A-Za-z0-9]/', '', $vin ) );

    if ( strlen( $vin ) !== 17 ) {
        wp_send_json_error( array( 'error' => 'VIN must be exactly 17 characters' ) );
    }
    if ( substr( $vin, 0, 2 ) !== 'LS' ) {
        wp_send_json_error( array( 'error' => 'This does not appear to be a Maxus VIN (should start with LS)' ) );
    }

    // Model year from position 10 of VIN
    $year_codes = array(
        'A'=>2010,'B'=>2011,'C'=>2012,'D'=>2013,'E'=>2014,'F'=>2015,'G'=>2016,
        'H'=>2017,'J'=>2018,'K'=>2019,'L'=>2020,'M'=>2021,'N'=>2022,'P'=>2023,
        'R'=>2024,'S'=>2025,'T'=>2026,'V'=>2027,'W'=>2028,'X'=>2029,'Y'=>2030,
    );
    $customer_pattern = substr( $vin, 0, 8 );
    $customer_year_code = substr( $vin, 9, 1 );
    $customer_year = isset( $year_codes[ $customer_year_code ] ) ? $year_codes[ $customer_year_code ] : null;
    $home_url = home_url( '/' );
    $vehicles = mvp_get_vehicle_vins();

    // 1. Try exact VIN match first (VIN categories ARE full VINs)
    foreach ( $vehicles as $slug => $v ) {
        if ( strtoupper( $v['vin'] ) === $vin ) {
            wp_send_json_success( array(
                'vehicle_name'  => $v['name'],
                'customer_year' => $customer_year,
                'shop_url'      => $home_url . 'vehicle/' . $slug . '/',
            ) );
        }
    }

    // 2. Pattern match by first 8 chars of VIN
    $matches = array();
    foreach ( $vehicles as $slug => $v ) {
        $v_pattern = substr( strtoupper( $v['vin'] ), 0, 8 );
        if ( $v_pattern === $customer_pattern ) {
            $matches[ $slug ] = $v;
        }
    }

    if ( empty( $matches ) ) {
        wp_send_json_error( array(
            'error'            => 'No vehicle found for VIN pattern: ' . $customer_pattern,
            'suggestion'       => 'We may not have parts for this specific Maxus model yet. Please contact us for assistance.',
            'customer_pattern' => $customer_pattern,
            'customer_year'    => $customer_year,
        ) );
    }

    // Single match
    if ( count( $matches ) === 1 ) {
        $slug = array_key_first( $matches );
        $v = $matches[ $slug ];
        wp_send_json_success( array(
            'vehicle_name'  => $v['name'],
            'customer_year' => $customer_year,
            'shop_url'      => $home_url . 'vehicle/' . $slug . '/',
        ) );
    }

    // Multiple matches — narrow by year
    $best_slug = null;
    if ( $customer_year ) {
        foreach ( $matches as $slug => $v ) {
            if ( preg_match( '/(\d{4})\s*-\s*(\S+)/', $v['year'], $m ) ) {
                $start = intval( $m[1] );
                $end = ( $m[2] === 'Present' ) ? 2030 : intval( $m[2] );
                if ( $customer_year >= $start && $customer_year <= $end ) {
                    $best_slug = $slug;
                    break;
                }
            }
        }
    }
    if ( ! $best_slug ) $best_slug = array_key_first( $matches );

    $v = $matches[ $best_slug ];
    wp_send_json_success( array(
        'vehicle_name'  => $v['name'],
        'customer_year' => $customer_year,
        'shop_url'      => $home_url . 'vehicle/' . $best_slug . '/',
    ) );
}

// ============================================================
// Registration lookup shortcode
add_shortcode("maxus_reg_search", "mvp_reg_search_shortcode");
function mvp_reg_search_shortcode() {
    ob_start();
    ?>
    <div class="maxus-reg-search-wrap" style="max-width:700px;margin:40px auto;text-align:center;">
        <h2 style="font-family:Inter,sans-serif;font-size:28px;margin-bottom:10px;">Registration Lookup</h2>
        <p style="color:#666;margin-bottom:24px;">Enter your UK vehicle registration to find compatible parts.</p>
        <form id="mvp-reg-form" style="display:flex;gap:10px;max-width:500px;margin:0 auto 12px;">
            <input type="text" id="mvp-reg-input" placeholder="e.g. AB12 CDE" maxlength="10" autocomplete="off"
                style="flex:1;height:48px;padding:0 16px;font-size:16px;border:2px solid #ddd;border-radius:6px;text-transform:uppercase;">
            <button type="submit" style="height:48px;padding:0 24px;background:#BF3617;color:#fff;border:none;border-radius:6px;font-size:16px;font-weight:600;cursor:pointer;">Search Parts</button>
        </form>
        <p style="font-size:13px;color:#999;">UK registration plate number</p>
        <div id="mvp-reg-result" style="margin-top:20px;text-align:left;display:none;"></div>
    </div>
    <script>
    document.addEventListener("DOMContentLoaded", function() {
        var form = document.getElementById("mvp-reg-form");
        var input = document.getElementById("mvp-reg-input");
        var result = document.getElementById("mvp-reg-result");
        if (!form) return;
        input.addEventListener("input", function() { this.value = this.value.toUpperCase(); });
        form.addEventListener("submit", function(e) {
            e.preventDefault();
            var reg = input.value.trim().replace(/\s+/g, "");
            if (reg.length < 2) { showReg("error", "Please enter a valid registration."); return; }
            showReg("loading", "Looking up " + input.value.trim() + "...");
            var fd = new FormData();
            fd.append("action", "maxus_reg_lookup");
            fd.append("reg", reg);
            fetch("<?php echo admin_url("admin-ajax.php"); ?>", {method:"POST", body:fd})
                .then(function(r){return r.json();})
                .then(function(data) {
                    if (data.success && data.data) {
                        // Multiple variants — show picker
                        if (data.data.variants && data.data.variants.length > 1) {
                            showVariantPicker(data.data);
                        } else if (data.data.shop_url) {
                            window.location.href = data.data.shop_url;
                        } else {
                            showReg("error", "Vehicle not found.");
                        }
                    } else {
                        showReg("error", data.data && data.data.error ? data.data.error : "Vehicle not found.");
                    }
                }).catch(function(){ showReg("error", "Network error. Please try again."); });
        });
        function showReg(type, msg) {
            result.style.display = "block";
            result.style.padding = "14px 20px";
            result.style.borderRadius = "6px";
            result.style.background = type === "error" ? "#fff5f5" : type === "loading" ? "#f0f0f0" : "#f0fff0";
            result.style.color = type === "error" ? "#c00" : "#333";
            result.innerHTML = "";
            result.textContent = msg;
        }
        function showVariantPicker(d) {
            result.style.display = "block";
            result.style.padding = "0";
            result.style.borderRadius = "8px";
            result.style.background = "#fff";
            result.style.color = "#333";
            result.style.border = "1px solid #e0e0e0";
            result.style.boxShadow = "0 2px 8px rgba(0,0,0,0.08)";
            var html = '<div style="background:#f8f8f8;padding:16px 20px;border-radius:8px 8px 0 0;border-bottom:1px solid #e0e0e0;">';
            html += '<div style="font-size:18px;font-weight:700;color:#111;">' + d.vehicle_name + '</div>';
            html += '<div style="font-size:14px;color:#666;margin-top:4px;">';
            html += d.customer_year + (d.colour ? ' &middot; ' + d.colour : '') + (d.fuel ? ' &middot; ' + d.fuel : '');
            html += '</div>';
            html += '</div>';
            html += '<div style="padding:16px 20px;">';
            html += '<p style="font-size:14px;color:#666;margin:0 0 14px;">We found multiple variants for this model. Please select yours:</p>';
            html += '<div style="display:flex;flex-direction:column;gap:8px;">';
            d.variants.forEach(function(v) {
                html += '<a href="' + v.url + '" style="display:flex;align-items:center;gap:14px;padding:12px 16px;border:2px solid #e0e0e0;border-radius:8px;text-decoration:none;color:#111;transition:border-color 0.2s,background 0.2s;" onmouseover="this.style.borderColor=\'#D18A0C\';this.style.background=\'#fffbf0\';" onmouseout="this.style.borderColor=\'#e0e0e0\';this.style.background=\'#fff\';">';
                if (v.img) {
                    html += '<img src="' + v.img + '" alt="" style="width:60px;height:40px;object-fit:contain;flex-shrink:0;">';
                }
                html += '<div style="flex:1;">';
                html += '<div style="font-size:16px;font-weight:600;">' + v.name + '</div>';
                if (v.year) { html += '<div style="font-size:13px;color:#888;">' + v.year + '</div>'; }
                html += '</div>';
                html += '<div style="flex-shrink:0;background:#BF3617;color:#fff;padding:8px 16px;border-radius:6px;font-size:13px;font-weight:600;">View Parts</div>';
                html += '</a>';
            });
            html += '</div></div>';
            result.innerHTML = html;
        }
        // Auto-submit if ?reg= parameter is present
        var urlParams = new URLSearchParams(window.location.search);
        var autoReg = urlParams.get("reg");
        if (autoReg) {
            input.value = autoReg.toUpperCase();
            form.dispatchEvent(new Event("submit"));
        }
    });
    </script>
    <?php
    return ob_get_clean();
}

// 8. REGISTRATION LOOKUP — AJAX handler (checkcardetails API)
// ============================================================
add_action( 'wp_ajax_maxus_reg_lookup', 'mvp_reg_lookup' );
add_action( 'wp_ajax_nopriv_maxus_reg_lookup', 'mvp_reg_lookup' );
function mvp_reg_lookup() {
    $reg = isset( $_POST['reg'] ) ? sanitize_text_field( $_POST['reg'] ) : '';
    $reg = preg_replace( '/\s+/', '', strtoupper( $reg ) );

    if ( empty( $reg ) || strlen( $reg ) < 2 ) {
        wp_send_json_error( array( 'error' => 'Please enter a valid registration number' ) );
    }

    // Call checkcardetails.co.uk API
    $api_key = 'd54fb43716925ad8f4dc415a4e2f962d';
    $api_url = 'https://api.checkcardetails.co.uk/vehicledata/vehicleregistration?apikey=' . $api_key . '&vrm=' . urlencode( $reg );
    $response = wp_remote_get( $api_url, array( 'timeout' => 10 ) );

    if ( is_wp_error( $response ) ) {
        wp_send_json_error( array( 'error' => 'Could not connect to vehicle lookup service' ) );
    }

    $code = wp_remote_retrieve_response_code( $response );
    $body = json_decode( wp_remote_retrieve_body( $response ), true );

    if ( $code === 404 || empty( $body ) ) {
        wp_send_json_error( array( 'error' => 'No vehicle found for registration: ' . $reg ) );
    }
    if ( $code !== 200 ) {
        wp_send_json_error( array( 'error' => 'Vehicle lookup failed. Please try again.' ) );
    }

    $make  = isset( $body['make'] ) ? strtoupper( trim( $body['make'] ) ) : '';
    $model_name = isset( $body['model'] ) ? trim( $body['model'] ) : '';
    $year  = isset( $body['yearOfManufacture'] ) ? intval( $body['yearOfManufacture'] ) : '';
    $fuel  = isset( $body['fuelType'] ) ? trim( $body['fuelType'] ) : '';

    // Check if Maxus/LDV
    if ( ! in_array( $make, array( 'MAXUS', 'LDV', 'SAIC', 'MG' ) ) ) {
        wp_send_json_error( array(
            'error' => 'This is a ' . ucwords( strtolower( $make ) ) . ' ' . $model_name . ' (' . $year . '). We only stock Maxus/LDV parts.',
        ) );
    }

    // Match model to vehicle landing page
    $vehicles = mvp_get_vehicle_vins();
    $home_url = home_url( '/' );
    $model_upper = strtoupper( $model_name );
    $is_electric = ( stripos( $fuel, 'ELECTRIC' ) !== false );
    $display_name = ucwords( strtolower( $make . ' ' . $model_name ) );

    // Collect ALL matching variants for this model
    $all_matches = array();
    $keywords = array( 'DELIVER 9', 'DELIVER 7', 'E DELIVER 9', 'E DELIVER 7', 'E DELIVER 3', 'E-DELIVER', 'T60', 'T90', 'V80', 'A80' );

    foreach ( $vehicles as $slug => $v ) {
        $v_name = strtoupper( $v['name'] );
        $v_is_electric = ( stripos( $v_name, 'E DELIVER' ) !== false || stripos( $v_name, 'EV' ) !== false );

        // Skip electric/non-electric mismatch
        if ( $is_electric !== $v_is_electric ) continue;

        $matched = false;

        // Direct match
        if ( stripos( $model_upper, $v_name ) !== false || stripos( $v_name, $model_upper ) !== false ) {
            $matched = true;
        }

        // Keyword matching
        if ( ! $matched ) {
            foreach ( $keywords as $kw ) {
                if ( stripos( $model_upper, $kw ) !== false && stripos( $v_name, $kw ) !== false ) {
                    $matched = true;
                    break;
                }
            }
        }

        if ( $matched ) {
            $all_matches[] = array(
                'slug' => $slug,
                'name' => $v['name'],
                'year' => $v['year'],
                'img'  => $v['img'],
                'url'  => $home_url . 'vehicle/' . $slug . '/',
            );
        }
    }

    // Single match — redirect directly (same as before)
    if ( count( $all_matches ) === 1 ) {
        wp_send_json_success( array(
            'vehicle_name'  => $display_name,
            'customer_year' => $year,
            'shop_url'      => $all_matches[0]['url'],
        ) );
    }

    // Multiple matches — return variants so frontend can show picker
    if ( count( $all_matches ) > 1 ) {
        wp_send_json_success( array(
            'vehicle_name'  => $display_name,
            'customer_year' => $year,
            'colour'        => isset( $body['colour'] ) ? ucwords( strtolower( $body['colour'] ) ) : '',
            'fuel'          => ucwords( strtolower( $fuel ) ),
            'variants'      => $all_matches,
        ) );
    }

    // No match — fallback to shop
    wp_send_json_success( array(
        'vehicle_name'  => $display_name,
        'customer_year' => $year,
        'shop_url'      => $home_url . 'shop/',
        'note'          => 'Could not match exact model. Showing all parts.',
    ) );
}

// ============================================================
// 9. HEADER VEHICLE PANEL — Dropdown for VIN/Reg search
//    Attaches to nav menu items: VIN Lookup, Registration Lookup
// ============================================================
add_action( 'wp_footer', 'mvp_vehicle_lookup_panel', 20 );
function mvp_vehicle_lookup_panel() {
    $ajax_url = admin_url( 'admin-ajax.php' );
    $home_url = home_url( '/' );

    // Build vehicle data for model/year selector
    $vehicles = mvp_get_vehicle_vins();
    $vehicle_data = array();
    foreach ( $vehicles as $slug => $v ) {
        $name = $v['name'];
        if ( ! isset( $vehicle_data[ $name ] ) ) {
            $vehicle_data[ $name ] = array( 'slug' => $slug, 'years' => array() );
        }
        if ( $v['year'] ) {
            $vehicle_data[ $name ]['years'][] = $v['year'];
        }
    }
    ?>
    <style>
    /* Vehicle lookup panel */
    #mvp-lookup-panel {
        display: none;
        position: fixed;
        background: #F29F05;
        padding: 20px 24px;
        border-radius: 0 0 8px 8px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        z-index: 999999;
        min-width: 380px;
        max-width: 440px;
        box-sizing: border-box;
    }
    #mvp-lookup-panel.is-open { display: block; }
    #mvp-lookup-panel .mvp-lp-label {
        color: #fff;
        font-size: 13px;
        font-weight: 600;
        margin: 0 0 8px 0;
    }
    #mvp-lookup-panel .mvp-lp-row {
        display: flex;
        gap: 0;
    }
    #mvp-lookup-panel .mvp-lp-row input {
        flex: 1;
        padding: 10px 14px;
        border: none;
        border-radius: 4px 0 0 4px;
        font-size: 14px;
        outline: none;
        color: #333;
        background: #fff;
        height: 42px;
        box-sizing: border-box;
    }
    #mvp-lookup-panel .mvp-lp-row input::placeholder { color: #999; }
    #mvp-lookup-panel .mvp-lp-row button {
        background: #BF3617;
        color: #fff;
        border: none;
        padding: 10px 18px;
        border-radius: 0 4px 4px 0;
        font-size: 14px;
        font-weight: 700;
        cursor: pointer;
        white-space: nowrap;
        height: 42px;
        box-sizing: border-box;
        transition: background 0.2s;
    }
    #mvp-lookup-panel .mvp-lp-row button:hover { background: #a02e13; }
    #mvp-lookup-panel .mvp-lp-hint {
        color: rgba(255,255,255,0.85);
        font-size: 11px;
        margin: 6px 0 0 0;
    }
    #mvp-lookup-panel .mvp-lp-divider {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 14px 0;
        color: rgba(255,255,255,0.8);
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    #mvp-lookup-panel .mvp-lp-divider::before,
    #mvp-lookup-panel .mvp-lp-divider::after {
        content: '';
        flex: 1;
        height: 1px;
        background: rgba(255,255,255,0.35);
    }
    #mvp-lookup-panel .mvp-lp-select {
        flex: 1;
        padding: 10px 12px;
        border: none;
        border-radius: 4px;
        font-size: 14px;
        color: #333;
        background: #fff;
        height: 42px;
        box-sizing: border-box;
        outline: none;
        cursor: pointer;
    }
    #mvp-lookup-panel .mvp-lp-select:disabled {
        background: #e8e8e8;
        color: #999;
        cursor: not-allowed;
    }
    #mvp-lookup-panel .mvp-lp-go {
        background: #BF3617;
        color: #fff;
        border: none;
        padding: 10px 20px;
        border-radius: 4px;
        font-size: 14px;
        font-weight: 700;
        cursor: pointer;
        white-space: nowrap;
        height: 42px;
        box-sizing: border-box;
        transition: background 0.2s;
    }
    #mvp-lookup-panel .mvp-lp-go:hover { background: #a02e13; }
    #mvp-lookup-panel .mvp-lp-go:disabled { background: #9a7a6a; cursor: not-allowed; }
    #mvp-lookup-panel .mvp-lp-model-row {
        display: flex;
        gap: 8px;
        margin-bottom: 10px;
    }
    #mvp-lookup-panel .mvp-lp-result {
        margin-top: 10px;
        padding: 10px 14px;
        border-radius: 4px;
        font-size: 13px;
        display: none;
    }
    #mvp-lookup-panel .mvp-lp-result.show { display: block; }
    #mvp-lookup-panel .mvp-lp-result.success { background: rgba(255,255,255,0.95); color: #333; }
    #mvp-lookup-panel .mvp-lp-result.error { background: rgba(0,0,0,0.15); color: #fff; }
    @keyframes mvp-spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .mvp-lp-loader { display: inline-flex; align-items: center; gap: 8px; }
    .mvp-lp-loader svg { animation: mvp-spin 1s linear infinite; flex-shrink: 0; }
    </style>

    <div id="mvp-lookup-panel">
        <!-- Model/Year selector -->
        <div class="mvp-lp-section mvp-lp-sec-model">
            <p class="mvp-lp-label">Find parts for your vehicle</p>
            <div class="mvp-lp-model-row">
                <select id="mvp-lp-model" class="mvp-lp-select"><option value="">Select Model</option></select>
                <select id="mvp-lp-year" class="mvp-lp-select" disabled><option value="">Select Year</option></select>
                <button type="button" id="mvp-lp-go" class="mvp-lp-go" disabled>Go</button>
            </div>
        </div>
        <!-- VIN search -->
        <div class="mvp-lp-section mvp-lp-sec-divider-vin"><div class="mvp-lp-divider">or</div></div>
        <div class="mvp-lp-section mvp-lp-sec-vin">
            <p class="mvp-lp-label">Search by VIN</p>
            <div class="mvp-lp-row">
                <input type="text" id="mvp-lp-vin" placeholder="Enter 17-character VIN" maxlength="17" autocomplete="off">
                <button type="button" id="mvp-lp-vin-btn">Search</button>
            </div>
            <p class="mvp-lp-hint">VIN is found on your V5C document or driver's side dashboard</p>
            <div class="mvp-lp-result" id="mvp-lp-vin-result"></div>
        </div>
        <!-- Registration search -->
        <div class="mvp-lp-section mvp-lp-sec-divider-reg"><div class="mvp-lp-divider">or</div></div>
        <div class="mvp-lp-section mvp-lp-sec-reg">
            <p class="mvp-lp-label">Search by Registration</p>
            <div class="mvp-lp-row">
                <input type="text" id="mvp-lp-reg" placeholder="e.g. AB12 CDE" maxlength="10" autocomplete="off">
                <button type="button" id="mvp-lp-reg-btn">Search</button>
            </div>
            <p class="mvp-lp-hint">UK registration plate number</p>
            <div class="mvp-lp-result" id="mvp-lp-reg-result"></div>
        </div>
    </div>

    <script>
    document.addEventListener('DOMContentLoaded', function() {
        var ajaxUrl = <?php echo json_encode( $ajax_url ); ?>;
        var homeUrl = <?php echo json_encode( $home_url ); ?>;
        var vehicleData = <?php echo json_encode( $vehicle_data, JSON_UNESCAPED_UNICODE ); ?>;
        var loaderHtml = '<span class="mvp-lp-loader"><svg width="18" height="18" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2.5" opacity="0.25"/><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2.5" stroke-dasharray="32" stroke-dashoffset="16" stroke-linecap="round"/></svg> Looking up vehicle...</span>';

        var panel = document.getElementById('mvp-lookup-panel');
        var isOpen = false;
        var closeTimer = null;

        function cancelClose() { clearTimeout(closeTimer); }
        function scheduleClose() {
            closeTimer = setTimeout(function() { panel.classList.remove('is-open'); isOpen = false; }, 300);
        }

        // Section elements
        var secModel = panel.querySelector('.mvp-lp-sec-model');
        var secDivVin = panel.querySelector('.mvp-lp-sec-divider-vin');
        var secVin = panel.querySelector('.mvp-lp-sec-vin');
        var secDivReg = panel.querySelector('.mvp-lp-sec-divider-reg');
        var secReg = panel.querySelector('.mvp-lp-sec-reg');
        var allSections = [secModel, secDivVin, secVin, secDivReg, secReg];

        function setPanelMode(mode) {
            if (mode === 'vin') {
                allSections.forEach(function(el) { el.style.display = 'none'; });
                secVin.style.display = '';
            } else if (mode === 'reg') {
                allSections.forEach(function(el) { el.style.display = 'none'; });
                secReg.style.display = '';
            } else {
                allSections.forEach(function(el) { el.style.display = ''; });
            }
        }

        function openPanel(anchor, mode) {
            cancelClose();
            setPanelMode(mode || 'full');
            var rect = anchor.getBoundingClientRect();
            var pw = panel.offsetWidth || 380;
            var left = rect.left;
            if (left + pw > window.innerWidth - 8) left = window.innerWidth - pw - 8;
            if (left < 8) left = 8;
            panel.style.top = rect.bottom + 'px';
            panel.style.left = left + 'px';
            panel.classList.add('is-open');
            isOpen = true;
        }

        function togglePanel(anchor, mode) {
            if (isOpen) { panel.classList.remove('is-open'); isOpen = false; }
            else { openPanel(anchor, mode); }
        }

        panel.addEventListener('mouseenter', cancelClose);
        panel.addEventListener('mouseleave', scheduleClose);

        // Close on outside click
        document.addEventListener('click', function(e) {
            if (!isOpen || panel.contains(e.target)) return;
            // Don't close if clicking the menu items that triggered it
            if (e.target.closest('a[href*="vin-search"]') || e.target.closest('a[href*="registration-lookup"]') || e.target.closest('a[href*="vehicle-lookup"]')) return;
            panel.classList.remove('is-open');
            isOpen = false;
        });

        // ── Model/Year selector ──
        var modelSel = document.getElementById('mvp-lp-model');
        var yearSel = document.getElementById('mvp-lp-year');
        var goBtn = document.getElementById('mvp-lp-go');

        Object.keys(vehicleData).sort().forEach(function(model) {
            var opt = document.createElement('option');
            opt.value = model;
            opt.textContent = model;
            modelSel.appendChild(opt);
        });

        modelSel.addEventListener('change', function() {
            var model = this.value;
            yearSel.innerHTML = '<option value="">Select Year</option>';
            yearSel.disabled = true;
            goBtn.disabled = true;
            if (!model || !vehicleData[model]) return;
            var years = vehicleData[model].years;
            if (years.length <= 1) { goBtn.disabled = false; return; }
            years.forEach(function(y) {
                var opt = document.createElement('option');
                opt.value = y; opt.textContent = y;
                yearSel.appendChild(opt);
            });
            yearSel.disabled = false;
        });

        yearSel.addEventListener('change', function() { goBtn.disabled = !this.value && !modelSel.value; });

        goBtn.addEventListener('click', function() {
            var model = modelSel.value;
            if (!model || !vehicleData[model]) return;
            window.location.href = homeUrl + 'vehicle/' + vehicleData[model].slug + '/';
        });

        // ── VIN search ──
        var vinInput = document.getElementById('mvp-lp-vin');
        var vinBtn = document.getElementById('mvp-lp-vin-btn');
        var vinResult = document.getElementById('mvp-lp-vin-result');

        vinInput.addEventListener('input', function() {
            this.value = this.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
        });

        function doVinSearch() {
            var vin = vinInput.value.trim();
            if (vin.length !== 17) {
                vinResult.className = 'mvp-lp-result show error';
                vinResult.textContent = 'VIN must be 17 characters (' + vin.length + ' entered)';
                return;
            }
            vinResult.className = 'mvp-lp-result show';
            vinResult.innerHTML = loaderHtml;
            var fd = new FormData();
            fd.append('action', 'maxus_vin_lookup');
            fd.append('vin', vin);
            fetch(ajaxUrl, { method: 'POST', body: fd })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.success && data.data) {
                        if (data.data.variants && data.data.variants.length > 1) {
                            vinResult.className = 'mvp-lp-result show success';
                            vinResult.innerHTML = '<strong>Multiple variants found</strong> — Select yours...';
                            window.location.href = homeUrl + 'vin-search-test/?vin=' + encodeURIComponent(vin);
                        } else if (data.data.shop_url) {
                            vinResult.className = 'mvp-lp-result show success';
                            vinResult.innerHTML = '<strong>' + data.data.vehicle_name + ' (' + data.data.customer_year + ')</strong> — Redirecting...';
                            window.location.href = data.data.shop_url;
                        } else {
                            vinResult.className = 'mvp-lp-result show error';
                            vinResult.textContent = 'No match found';
                        }
                    } else {
                        vinResult.className = 'mvp-lp-result show error';
                        vinResult.textContent = (data.data && data.data.error) || 'No match found';
                    }
                })
                .catch(function() {
                    vinResult.className = 'mvp-lp-result show error';
                    vinResult.textContent = 'An error occurred. Please try again.';
                });
        }

        vinBtn.addEventListener('click', function(e) { e.preventDefault(); doVinSearch(); });
        vinInput.addEventListener('keydown', function(e) { if (e.key === 'Enter') { e.preventDefault(); doVinSearch(); } });

        // ── Registration search ──
        var regInput = document.getElementById('mvp-lp-reg');
        var regBtn = document.getElementById('mvp-lp-reg-btn');
        var regResult = document.getElementById('mvp-lp-reg-result');

        regInput.addEventListener('input', function() { this.value = this.value.toUpperCase(); });

        function doRegSearch() {
            var reg = regInput.value.trim().replace(/\s+/g, '');
            if (reg.length < 2) {
                regResult.className = 'mvp-lp-result show error';
                regResult.textContent = 'Please enter a valid registration number';
                return;
            }
            regResult.className = 'mvp-lp-result show';
            regResult.innerHTML = loaderHtml;
            var fd = new FormData();
            fd.append('action', 'maxus_reg_lookup');
            fd.append('reg', reg);
            fetch(ajaxUrl, { method: 'POST', body: fd })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.success && data.data) {
                        if (data.data.variants && data.data.variants.length > 1) {
                            // Multiple variants — go to registration lookup page with picker
                            regResult.className = 'mvp-lp-result show success';
                            regResult.innerHTML = '<strong>' + data.data.vehicle_name + '</strong> — Select your variant...';
                            window.location.href = homeUrl + 'registration-lookup/?reg=' + encodeURIComponent(reg);
                        } else if (data.data.shop_url) {
                            regResult.className = 'mvp-lp-result show success';
                            regResult.innerHTML = '<strong>' + data.data.vehicle_name + ' (' + data.data.customer_year + ')</strong> — Redirecting...';
                            window.location.href = data.data.shop_url;
                        } else {
                            regResult.className = 'mvp-lp-result show error';
                            regResult.textContent = 'No match found';
                        }
                    } else {
                        regResult.className = 'mvp-lp-result show error';
                        regResult.textContent = (data.data && data.data.error) || 'No match found';
                    }
                })
                .catch(function() {
                    regResult.className = 'mvp-lp-result show error';
                    regResult.textContent = 'An error occurred. Please try again.';
                });
        }

        regBtn.addEventListener('click', function(e) { e.preventDefault(); doRegSearch(); });
        regInput.addEventListener('keydown', function(e) { if (e.key === 'Enter') { e.preventDefault(); doRegSearch(); } });

        // ── Attach to nav menu items ──
        // Find menu items by href containing our target URLs
        var allLinks = document.querySelectorAll('#site-navigation a, .header-menu a, nav a');
        allLinks.forEach(function(link) {
            var href = link.getAttribute('href') || '';
            var mode = null;

            if (href.indexOf('vin-search') !== -1) mode = 'vin';
            else if (href.indexOf('registration-lookup') !== -1) mode = 'reg';
            else if (href.indexOf('vehicle-lookup') !== -1) mode = 'full';

            if (!mode) return;

            // Prevent navigation
            link.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                togglePanel(link, mode);
            });

            // Hover to open
            var menuItem = link.closest('li') || link;
            menuItem.addEventListener('mouseenter', function() { openPanel(link, mode); });
            menuItem.addEventListener('mouseleave', function() { scheduleClose(); });
        });
    });
    </script>
    <?php
}

// ============================================================
// 10. VEHICLE SEARCH BAR — Replaces Elementor 6-dropdown filter
// ============================================================
// Matches source site layout: Model | Year | OR | VIN | OR | Registration | Search
// All lookups redirect to /vehicle/{slug}/ landing pages.

add_action( 'wp_footer', 'mvp_vehicle_search_bar', 25 );
function mvp_vehicle_search_bar() {
    if ( ! is_front_page() && ! is_home() ) return;

    // Build model → slug + year data from DB term meta
    $maxus_term_id = mvp_get_maxus_term_id();
    $vin_terms = get_terms( array(
        'taxonomy'   => 'product_cat',
        'parent'     => $maxus_term_id,
        'hide_empty' => false,
        'orderby'    => 'name',
    ) );

    $models = array();
    if ( ! is_wp_error( $vin_terms ) ) {
        foreach ( $vin_terms as $t ) {
            $model = get_term_meta( $t->term_id, 'vehicle_model', true );
            $slug  = get_term_meta( $t->term_id, 'vehicle_slug', true );
            $year  = get_term_meta( $t->term_id, 'vehicle_year', true );
            if ( $model && $slug ) {
                $models[ $model ] = array( 'slug' => $slug, 'year' => $year ? $year : '' );
            }
        }
    }
    ksort( $models );

    $home_url = home_url( '/' );
    $ajax_url = admin_url( 'admin-ajax.php' );
    ?>
    <style id="mvp-search-bar-css">
    .mvp-search-bar-wrap { max-width: 100%; margin: 0; position: relative; }
    .mvp-search-bar {
        display: flex; flex-wrap: nowrap; align-items: center; justify-content: space-between; gap: 10px;
        padding: 0 16px; height: 68px;
        background: var(--e-global-color-secondary, #F29F05);
        border-radius: 6px; box-shadow: rgba(0,0,0,0.1) 0px 0px 6px 0px; position: relative;
    }
    .mvp-search-bar .mvp-sb-select {
        box-sizing: border-box; margin: 0;
        height: 36px; padding: 0 28px 0 10px; font-size: 13px; font-family: inherit;
        border: 1px solid #e0e0e0; border-radius: 6px; outline: none; color: #444; background: #fff;
        cursor: pointer; min-width: 0;
        -webkit-appearance: none; -moz-appearance: none; appearance: none;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%23999'/%3E%3C/svg%3E");
        background-repeat: no-repeat; background-position: right 10px center;
    }
    .mvp-search-bar .mvp-sb-model { width: 208px; min-width: 208px; flex: 0 0 208px; }
    .mvp-search-bar .mvp-sb-year { width: 120px; min-width: 120px; flex: 0 0 120px; }
    .mvp-search-bar .mvp-sb-atts { display: flex; align-items: center; gap: 8px; flex: 0 0 auto; }
    .mvp-search-bar .mvp-sb-last { display: flex; align-items: center; justify-content: flex-end; gap: 8px; flex: 1 1 auto; }
    .mvp-search-bar .mvp-sb-or {
        white-space: nowrap; font-weight: 700; font-size: 12px;
        text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.85;
        color: #444; padding: 0 2px; flex-shrink: 0;
    }
    .mvp-search-bar .mvp-sb-input { flex-shrink: 0;
        height: 36px; padding: 0 10px; font-size: 13px; font-family: inherit;
        border: none; border-radius: 4px; outline: none; color: #333; background: #fff;
        box-sizing: border-box; margin: 0; width: 180px; min-width: 180px; flex: 0 0 180px;
    }
    .mvp-search-bar .mvp-sb-input::placeholder { color: #999; font-size: 13px; }
    .mvp-search-bar .mvp-sb-submit {
        height: 48px; padding: 0 16px; font-size: 13px; font-weight: 600;
        font-family: inherit; white-space: nowrap;
        border: none; border-radius: 6px; background: #BF3617; color: #fff; flex: 0 0 auto; display: flex; align-items: center; justify-content: center; margin: 0; box-sizing: border-box;
        cursor: pointer; text-transform: none; transition: background 0.2s;
    }
    .mvp-search-bar .mvp-sb-submit:hover { background: #a02e13; }
    .mvp-search-bar .mvp-sb-reset { display: none !important;
        font-size: 11px; color: rgba(255,255,255,0.7); cursor: pointer;
        text-decoration: underline; flex-shrink: 0; white-space: nowrap;
    }
    .mvp-search-bar .mvp-sb-reset:hover { color: #fff; }
    .mvp-sb-result {
        position: absolute; top: 100%; right: 20px; z-index: 100;
        font-size: 12px; margin-top: 4px; padding: 8px 14px; border-radius: 4px;
        display: none; min-width: 260px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .mvp-sb-result.show { display: block; }
    .mvp-sb-result.success { background: rgba(255,255,255,0.95); color: #333; }
    .mvp-sb-result.error { background: rgba(0,0,0,0.15); color: #fff; }
    @keyframes mvp-sb-spin { 0%{transform:rotate(0deg)} 100%{transform:rotate(360deg)} }
    .mvp-sb-loader { display: inline-flex; align-items: center; gap: 8px; }
    .mvp-sb-loader svg { animation: mvp-sb-spin 1s linear infinite; flex-shrink: 0; }
    .mvp-sb-mobile-toggle {
        display: none; background: var(--e-global-color-secondary, #F29F05);
        color: #fff; font-weight: 600; font-size: 14px; text-align: center; line-height: 48px;
        padding: 0 16px; height: 68px; border-radius: 6px; cursor: pointer;
    }
    @media (max-width: 960px) {
        .mvp-search-bar { flex-wrap: wrap; gap: 8px; padding: 12px 16px; }
        .mvp-search-bar .mvp-sb-model, .mvp-search-bar .mvp-sb-year { min-width: 0; flex: 1 1 45%; }
        .mvp-search-bar .mvp-sb-input { flex-shrink: 0; width: auto; flex: 1 1 40%; }
    }
    @media (max-width: 600px) {
        .mvp-sb-mobile-toggle { display: block; }
        .mvp-search-bar { display: none; flex-direction: column; }
        .mvp-search-bar.mvp-sb-open { display: flex; margin-top: 4px; border-radius: 0 0 6px 6px; }
        .mvp-sb-mobile-toggle.mvp-sb-open { border-radius: 6px 6px 0 0; margin-bottom: 0; }
        .mvp-search-bar .mvp-sb-model, .mvp-search-bar .mvp-sb-year,
        .mvp-search-bar .mvp-sb-input { flex-shrink: 0; width: 100% !important; min-width: 0; flex: 1 1 100%; }
        .mvp-search-bar .mvp-sb-submit { width: 100%; }
        .mvp-search-bar .mvp-sb-or { display: none; }
    }
    </style>
    <script>
    document.addEventListener("DOMContentLoaded", function(){
        var mvpModels = <?php echo json_encode( $models ); ?>;
        var mvpHomeUrl = <?php echo json_encode( $home_url ); ?>;
        var mvpAjaxUrl = <?php echo json_encode( $ajax_url ); ?>;
        var loaderHtml = '<span class="mvp-sb-loader"><svg width="18" height="18" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2.5" opacity="0.25"/><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2.5" stroke-dasharray="32" stroke-dashoffset="16" stroke-linecap="round"/><circle cx="12" cy="12" r="5" stroke="currentColor" stroke-width="1.5"/><line x1="12" y1="2" x2="12" y2="5" stroke="currentColor" stroke-width="1.5"/><line x1="12" y1="19" x2="12" y2="22" stroke="currentColor" stroke-width="1.5"/><line x1="2" y1="12" x2="5" y2="12" stroke="currentColor" stroke-width="1.5"/><line x1="19" y1="12" x2="22" y2="12" stroke="currentColor" stroke-width="1.5"/></svg> Looking up&hellip;</span>';

        var modelOpts = '<option value="">Model</option>';
        var yearMap = {};
        for (var m in mvpModels) {
            modelOpts += '<option value="' + m + '">' + m + '</option>';
            if (mvpModels[m].year) yearMap[m] = mvpModels[m].year;
        }

        var barHtml = '<div class="mvp-search-bar-wrap">' +
            '<div class="mvp-sb-mobile-toggle">Vehicle Filter</div>' +
            '<div class="mvp-search-bar">' +
                '<div class="mvp-sb-atts">' +
                '<select class="mvp-sb-select mvp-sb-model">' + modelOpts + '</select>' +
                '<select class="mvp-sb-select mvp-sb-year" disabled><option value="">Year</option></select>' +
                '</div>' +
                '<div class="mvp-sb-last">' +
                '<span class="mvp-sb-or">OR</span>' +
                '<input type="text" class="mvp-sb-input mvp-sb-vin" placeholder="Search by VIN" maxlength="17" autocomplete="off">' +
                '<span class="mvp-sb-or">OR</span>' +
                '<input type="text" class="mvp-sb-input mvp-sb-reg" placeholder="Search by Registration" maxlength="10" autocomplete="off">' +
                '<button type="button" class="mvp-sb-submit">Search</button>' +
                '<span class="mvp-sb-reset">Reset</span>' +
                '</div>' +
                '<div class="mvp-sb-result"></div>' +
            '</div></div>';

        // Inject into the filter container (631db85) or fallback after carousel
        var target = document.querySelector('.elementor-element-631db85');
        if (target) {
            target.insertAdjacentHTML('afterbegin', barHtml);
        } else {
            var hero = document.querySelector('.mvp-vehicles');
            if (hero) hero.insertAdjacentHTML('afterend', barHtml);
        }

        var wrap = document.querySelector('.mvp-search-bar-wrap');
        if (!wrap) return;
        var bar = wrap.querySelector('.mvp-search-bar');
        var modelSel = wrap.querySelector('.mvp-sb-model');
        var yearSel = wrap.querySelector('.mvp-sb-year');
        var vinInput = wrap.querySelector('.mvp-sb-vin');
        var regInput = wrap.querySelector('.mvp-sb-reg');
        var submitBtn = wrap.querySelector('.mvp-sb-submit');
        var resetBtn = wrap.querySelector('.mvp-sb-reset');
        var resultEl = wrap.querySelector('.mvp-sb-result');
        var mobileToggle = wrap.querySelector('.mvp-sb-mobile-toggle');

        mobileToggle.addEventListener('click', function() {
            this.classList.toggle('mvp-sb-open');
            bar.classList.toggle('mvp-sb-open');
        });

        // Model change → populate year dropdown
        modelSel.addEventListener('change', function() {
            var model = this.value;
            yearSel.innerHTML = '<option value="">Year</option>';
            vinInput.value = ''; regInput.value = ''; hideResult();
            if (model && yearMap[model]) {
                var parts = yearMap[model].split('-');
                if (parts.length === 2) {
                    for (var y = parseInt(parts[1]); y >= parseInt(parts[0]); y--)
                        yearSel.innerHTML += '<option value="' + y + '">' + y + '</option>';
                } else {
                    yearSel.innerHTML += '<option value="' + yearMap[model] + '">' + yearMap[model] + '</option>';
                }
                yearSel.disabled = false;
            } else { yearSel.disabled = true; }
        });

        // Clear dropdowns when typing VIN or Reg
        vinInput.addEventListener('input', function() {
            if (this.value.trim()) { modelSel.value = ''; yearSel.innerHTML = '<option value="">Year</option>'; yearSel.disabled = true; regInput.value = ''; }
            hideResult();
        });
        regInput.addEventListener('input', function() {
            if (this.value.trim()) { modelSel.value = ''; yearSel.innerHTML = '<option value="">Year</option>'; yearSel.disabled = true; vinInput.value = ''; }
            hideResult();
        });

        resetBtn.addEventListener('click', function() {
            modelSel.value = ''; yearSel.innerHTML = '<option value="">Year</option>'; yearSel.disabled = true;
            vinInput.value = ''; regInput.value = ''; hideResult();
        });

        submitBtn.addEventListener('click', doSearch);
        vinInput.addEventListener('keydown', function(e) { if (e.key === 'Enter') { e.preventDefault(); doSearch(); } });
        regInput.addEventListener('keydown', function(e) { if (e.key === 'Enter') { e.preventDefault(); doSearch(); } });

        function hideResult() { resultEl.className = 'mvp-sb-result'; resultEl.innerHTML = ''; }

        function doSearch() {
            var reg = regInput.value.trim();
            var vin = vinInput.value.trim().toUpperCase().replace(/[^A-Z0-9]/g, '');
            var model = modelSel.value;
            if (reg.length >= 2) { doRegSearch(reg); }
            else if (vin.length > 0) { doVinSearch(vin); }
            else if (model && mvpModels[model]) { window.location.href = mvpHomeUrl + 'vehicle/' + mvpModels[model].slug + '/'; }
            else { resultEl.className = 'mvp-sb-result show error'; resultEl.textContent = 'Please select a model, enter a VIN, or enter a registration'; }
        }

        function doVinSearch(vin) {
            if (vin.length !== 17) { resultEl.className = 'mvp-sb-result show error'; resultEl.textContent = 'VIN must be 17 characters (' + vin.length + ' entered)'; return; }
            resultEl.className = 'mvp-sb-result show'; resultEl.innerHTML = loaderHtml;
            var fd = new FormData(); fd.append('action', 'maxus_vin_lookup'); fd.append('vin', vin);
            fetch(mvpAjaxUrl, { method: 'POST', body: fd })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.success && data.data) {
                        if (data.data.variants && data.data.variants.length > 1) {
                            resultEl.className = 'mvp-sb-result show success';
                            resultEl.innerHTML = '<strong>Multiple variants found</strong> &mdash; Select yours...';
                            window.location.href = mvpHomeUrl + 'vin-search-test/?vin=' + encodeURIComponent(vin);
                        } else if (data.data.shop_url) {
                            resultEl.className = 'mvp-sb-result show success';
                            resultEl.innerHTML = '<strong>' + (data.data.vehicle_name || 'Vehicle found') + '</strong> &mdash; Redirecting...';
                            window.location.href = data.data.shop_url;
                        } else { resultEl.className = 'mvp-sb-result show error'; resultEl.textContent = 'No match found'; }
                    } else { resultEl.className = 'mvp-sb-result show error'; resultEl.textContent = (data.data && data.data.error) || 'No match found for this VIN'; }
                }).catch(function() { resultEl.className = 'mvp-sb-result show error'; resultEl.textContent = 'An error occurred. Please try again.'; });
        }

        function doRegSearch(reg) {
            reg = reg.replace(/\s+/g, '');
            if (reg.length < 2) { resultEl.className = 'mvp-sb-result show error'; resultEl.textContent = 'Please enter a valid registration number'; return; }
            resultEl.className = 'mvp-sb-result show'; resultEl.innerHTML = loaderHtml;
            var fd = new FormData(); fd.append('action', 'maxus_reg_lookup'); fd.append('reg', reg);
            fetch(mvpAjaxUrl, { method: 'POST', body: fd })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.success && data.data) {
                        if (data.data.variants && data.data.variants.length > 1) {
                            resultEl.className = 'mvp-sb-result show success';
                            resultEl.innerHTML = '<strong>' + data.data.vehicle_name + '</strong> &mdash; Select your variant...';
                            window.location.href = mvpHomeUrl + 'registration-lookup/?reg=' + encodeURIComponent(reg);
                        } else if (data.data.shop_url) {
                            resultEl.className = 'mvp-sb-result show success';
                            resultEl.innerHTML = '<strong>' + data.data.vehicle_name + ' (' + data.data.customer_year + ')</strong> &mdash; Redirecting...';
                            window.location.href = data.data.shop_url;
                        } else { resultEl.className = 'mvp-sb-result show error'; resultEl.textContent = 'No match found'; }
                    } else { resultEl.className = 'mvp-sb-result show error'; resultEl.textContent = (data.data && data.data.error) || 'No match found'; }
                }).catch(function() { resultEl.className = 'mvp-sb-result show error'; resultEl.textContent = 'An error occurred. Please try again.'; });
        }
    });
    </script>
    <?php
}


// ============================================================
// 11. VEHICLE META FIELDS ON PRODUCT CATEGORY EDIT SCREEN
// ============================================================

/**
 * Render editable vehicle meta fields on the Edit Category screen.
 */
add_action( 'product_cat_edit_form_fields', 'mvp_vehicle_meta_edit_fields', 10, 2 );
function mvp_vehicle_meta_edit_fields( $term, $taxonomy ) {
    $model = get_term_meta( $term->term_id, 'vehicle_model', true );
    $slug  = get_term_meta( $term->term_id, 'vehicle_slug',  true );
    $year  = get_term_meta( $term->term_id, 'vehicle_year',  true );
    $image = get_term_meta( $term->term_id, 'vehicle_image', true );
    wp_nonce_field( 'mvp_vehicle_meta_save', 'mvp_vehicle_meta_nonce' );
    ?>
    <tr class="form-field">
        <th scope="row"><label for="mvp_vehicle_model"><?php esc_html_e( 'Vehicle Model', 'mobex-child' ); ?></label></th>
        <td>
            <input type="text" id="mvp_vehicle_model" name="mvp_vehicle_model" value="<?php echo esc_attr( $model ); ?>" />
            <p class="description"><?php esc_html_e( 'e.g. Maxus Deliver 9', 'mobex-child' ); ?></p>
        </td>
    </tr>
    <tr class="form-field">
        <th scope="row"><label for="mvp_vehicle_slug"><?php esc_html_e( 'Vehicle Slug', 'mobex-child' ); ?></label></th>
        <td>
            <input type="text" id="mvp_vehicle_slug" name="mvp_vehicle_slug" value="<?php echo esc_attr( $slug ); ?>" />
            <p class="description"><?php esc_html_e( 'URL-safe identifier, e.g. deliver-9', 'mobex-child' ); ?></p>
        </td>
    </tr>
    <tr class="form-field">
        <th scope="row"><label for="mvp_vehicle_year"><?php esc_html_e( 'Vehicle Year', 'mobex-child' ); ?></label></th>
        <td>
            <input type="text" id="mvp_vehicle_year" name="mvp_vehicle_year" value="<?php echo esc_attr( $year ); ?>" />
            <p class="description"><?php esc_html_e( 'e.g. 2022', 'mobex-child' ); ?></p>
        </td>
    </tr>
    <tr class="form-field">
        <th scope="row"><label for="mvp_vehicle_image"><?php esc_html_e( 'Vehicle Image URL', 'mobex-child' ); ?></label></th>
        <td>
            <input type="url" id="mvp_vehicle_image" name="mvp_vehicle_image" value="<?php echo esc_attr( $image ); ?>" style="width:100%;" />
            <?php if ( $image ) : ?>
                <img src="<?php echo esc_url( $image ); ?>" alt="Vehicle preview" style="margin-top:8px;max-height:80px;" />
            <?php endif; ?>
            <p class="description"><?php esc_html_e( 'Full URL to the vehicle image.', 'mobex-child' ); ?></p>
        </td>
    </tr>
    <?php
}

/**
 * Render vehicle meta fields on the Add New Category screen.
 */
add_action( 'product_cat_add_form_fields', 'mvp_vehicle_meta_add_fields', 10, 1 );
function mvp_vehicle_meta_add_fields( $taxonomy ) {
    wp_nonce_field( 'mvp_vehicle_meta_save', 'mvp_vehicle_meta_nonce' );
    ?>
    <div class="form-field">
        <label for="mvp_vehicle_model"><?php esc_html_e( 'Vehicle Model', 'mobex-child' ); ?></label>
        <input type="text" id="mvp_vehicle_model" name="mvp_vehicle_model" value="" />
        <p><?php esc_html_e( 'e.g. Maxus Deliver 9', 'mobex-child' ); ?></p>
    </div>
    <div class="form-field">
        <label for="mvp_vehicle_slug"><?php esc_html_e( 'Vehicle Slug', 'mobex-child' ); ?></label>
        <input type="text" id="mvp_vehicle_slug" name="mvp_vehicle_slug" value="" />
        <p><?php esc_html_e( 'URL-safe identifier, e.g. deliver-9', 'mobex-child' ); ?></p>
    </div>
    <div class="form-field">
        <label for="mvp_vehicle_year"><?php esc_html_e( 'Vehicle Year', 'mobex-child' ); ?></label>
        <input type="text" id="mvp_vehicle_year" name="mvp_vehicle_year" value="" />
        <p><?php esc_html_e( 'e.g. 2022', 'mobex-child' ); ?></p>
    </div>
    <div class="form-field">
        <label for="mvp_vehicle_image"><?php esc_html_e( 'Vehicle Image URL', 'mobex-child' ); ?></label>
        <input type="url" id="mvp_vehicle_image" name="mvp_vehicle_image" value="" />
        <p><?php esc_html_e( 'Full URL to the vehicle image.', 'mobex-child' ); ?></p>
    </div>
    <?php
}

/**
 * Save vehicle meta fields when a product category is created or updated.
 */
add_action( 'created_product_cat', 'mvp_vehicle_meta_save_fields', 10, 2 );
add_action( 'edited_product_cat',  'mvp_vehicle_meta_save_fields', 10, 2 );
function mvp_vehicle_meta_save_fields( $term_id, $tt_id ) {
    if ( ! isset( $_POST['mvp_vehicle_meta_nonce'] ) ||
         ! wp_verify_nonce( $_POST['mvp_vehicle_meta_nonce'], 'mvp_vehicle_meta_save' ) ) {
        return;
    }
    $fields = array( 'vehicle_model', 'vehicle_slug', 'vehicle_year', 'vehicle_image' );
    foreach ( $fields as $field ) {
        $post_key = 'mvp_' . $field;
        if ( isset( $_POST[ $post_key ] ) ) {
            $value = sanitize_text_field( $_POST[ $post_key ] );
            if ( $value !== '' ) {
                update_term_meta( $term_id, $field, $value );
            } else {
                delete_term_meta( $term_id, $field );
            }
        }
    }
}


// ============================================================
// 12. VEHICLE NOTICE BAR — STICKY TOP BAR ON ALL PAGES
// ============================================================

// Set vehicle cookies on WooCommerce product_cat pages when a Maxus VIN term is an ancestor
add_action( 'wp_footer', 'mvp_set_vehicle_cookies_from_product_cat' );
function mvp_set_vehicle_cookies_from_product_cat() {
    if ( ! is_tax( 'product_cat' ) ) return;

    $maxus_term_id = mvp_get_maxus_term_id();
    $queried = get_queried_object();
    if ( ! ( $queried instanceof WP_Term ) ) return;

    // Walk up the ancestor chain to find the VIN-level term (direct child of Maxus)
    $vin_term = null;
    if ( (int) $queried->parent === $maxus_term_id ) {
        $vin_term = $queried;
    } else {
        $ancestors = get_ancestors( $queried->term_id, 'product_cat', 'taxonomy' );
        foreach ( $ancestors as $anc_id ) {
            $anc = get_term( (int) $anc_id, 'product_cat' );
            if ( $anc && ! is_wp_error( $anc ) && (int) $anc->parent === $maxus_term_id ) {
                $vin_term = $anc;
                break;
            }
        }
    }

    if ( ! $vin_term ) return;

    $vehicle_slug  = get_term_meta( $vin_term->term_id, 'vehicle_slug', true );
    $vehicle_model = get_term_meta( $vin_term->term_id, 'vehicle_model', true );
    $vehicle_year  = get_term_meta( $vin_term->term_id, 'vehicle_year', true );
    $vin_serial    = $vin_term->slug;

    if ( empty( $vehicle_slug ) || empty( $vehicle_model ) ) return;
    ?>
    <script>
    (function() {
        var expires = new Date();
        expires.setDate(expires.getDate() + 30);
        var exp = expires.toUTCString();
        var secure = location.protocol === 'https:' ? '; Secure' : '';
        var path = 'path=/; SameSite=Lax' + secure;
        document.cookie = 'mvp_vehicle_slug='   + encodeURIComponent('<?php echo esc_js( $vehicle_slug ); ?>') + '; expires=' + exp + '; ' + path;
        document.cookie = 'mvp_vehicle_serial=' + encodeURIComponent('<?php echo esc_js( $vin_serial ); ?>') + '; expires=' + exp + '; ' + path;
        document.cookie = 'mvp_vehicle_model='  + encodeURIComponent('<?php echo esc_js( $vehicle_model ); ?>') + '; expires=' + exp + '; ' + path;
        document.cookie = 'mvp_vehicle_year='   + encodeURIComponent('<?php echo esc_js( $vehicle_year ); ?>') + '; expires=' + exp + '; ' + path;
    });
    </script>
    <?php
}

add_action( 'wp_body_open', 'mvp_vehicle_sticky_notice_bar' );
function mvp_vehicle_sticky_notice_bar() {
    if ( empty( $_COOKIE['mvp_vehicle_slug'] ) || empty( $_COOKIE['mvp_vehicle_model'] ) ) return;

    $model = sanitize_text_field( wp_unslash( $_COOKIE['mvp_vehicle_model'] ) );
    $year  = ! empty( $_COOKIE['mvp_vehicle_year'] ) ? sanitize_text_field( wp_unslash( $_COOKIE['mvp_vehicle_year'] ) ) : '';
    $slug  = sanitize_title( wp_unslash( $_COOKIE['mvp_vehicle_slug'] ) );
    $vehicle_url = home_url( '/vehicle/' . $slug . '/' );
    ?>
    <style>
    #mvp-vehicle-bar {
        width: 100%;
        background: #F29F05;
        color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 18px;
        padding: 9px 20px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 13px;
        line-height: 1.4;
        flex-wrap: wrap;
        position: relative;
        z-index: 100;
        box-sizing: border-box;
    }
    #mvp-vehicle-bar .mvp-bar-label {
        opacity: 0.75;
    }
    #mvp-vehicle-bar .mvp-bar-vehicle {
        font-weight: 700;
        color: #fff;
    }
    #mvp-vehicle-bar .mvp-bar-change {
        display: inline-block;
        font-size: 12px;
        font-weight: 600;
        color: #F29F05;
        background: #F29F05;
        border-radius: 4px;
        padding: 4px 12px;
        text-decoration: none;
        white-space: nowrap;
        cursor: pointer;
        border: none;
    }
    #mvp-vehicle-bar .mvp-bar-change:hover {
        background: #fff;
        color: #F29F05;
    }
    </style>

    <div id="mvp-vehicle-bar">
        <span class="mvp-bar-label">Viewing parts for:</span>
        <span class="mvp-bar-vehicle"><?php echo esc_html( $model ); ?><?php if ( $year ) echo ' (' . esc_html( $year ) . ')'; ?></span>
        <a class="mvp-bar-change" href="<?php echo esc_url( home_url( '/#mvp-vehicles' ) ); ?>" onclick="mvpClearVehicleCookies(event);">&#8635; Change vehicle</a>
    </div>

    <script>
    function mvpClearVehicleCookies(e) {
        if (e) e.preventDefault();
        var past = 'Thu, 01 Jan 1970 00:00:00 UTC';
        ['mvp_vehicle_slug', 'mvp_vehicle_serial', 'mvp_vehicle_model', 'mvp_vehicle_year'].forEach(function(k) {
            document.cookie = k + '=; expires=' + past + '; path=/; SameSite=Lax';
        });
        window.location.href = '<?php echo esc_js( home_url( '/#mvp-vehicles' ) ); ?>';
    }
    </script>
    <?php
}

// ============================================================
// DYNAMIC SEO META TAGS & JSON-LD SCHEMA FOR PRODUCT PAGES
// ============================================================

/**
 * Inject dynamic SEO meta tags and JSON-LD schema for product pages.
 * Outputs original_sku (Oscar part number) and vehicle model for Google indexing.
 */
add_action( 'wp_head', 'mvp_inject_product_seo_meta', 1 );
function mvp_inject_product_seo_meta() {
    // Only run on single product pages
    if ( ! is_product() ) {
        return;
    }

    global $post;
    if ( ! $post ) {
        return;
    }

    // Get the product object
    $product = wc_get_product( $post->ID );
    if ( ! $product ) {
        return;
    }

    // Get original_sku (Oscar part number)
    $original_sku = get_post_meta( $product->get_id(), 'original_sku', true );
    if ( ! $original_sku ) {
        // Fallback to WordPress SKU if original_sku doesn't exist
        $original_sku = $product->get_sku();
    }

    // Get product name
    $product_name = $product->get_name();

    // Get vehicle model from the product's VIN category
    $vehicle_models = array();
    $categories = get_the_terms( $product->get_id(), 'product_cat' );
    
    if ( $categories && ! is_wp_error( $categories ) ) {
        $maxus_term_id = mvp_get_maxus_term_id();
        
        foreach ( $categories as $cat ) {
            // Check if this category is a VIN (direct child of Maxus)
            if ( $cat->parent === $maxus_term_id ) {
                $vehicle_model = get_term_meta( $cat->term_id, 'vehicle_model', true );
                $vehicle_year  = get_term_meta( $cat->term_id, 'vehicle_year', true );
                
                if ( $vehicle_model ) {
                    $display_model = $vehicle_model;
                    if ( $vehicle_year ) {
                        $display_model .= ' (' . $vehicle_year . ')';
                    }
                    $vehicle_models[] = $display_model;
                }
            }
        }
    }

    // Build meta description
    $description = $product_name;
    if ( ! empty( $vehicle_models ) ) {
        $description .= ' for ' . implode( ', ', $vehicle_models );
    }
    $description .= '. Part Number: ' . $original_sku;
    
    // Add short description if available
    $short_desc = $product->get_short_description();
    if ( $short_desc ) {
        $short_desc = wp_strip_all_tags( $short_desc );
        $short_desc = substr( $short_desc, 0, 100 );
        $description .= '. ' . $short_desc;
    }

    // Get product price
    $price = $product->get_price();
    $currency = get_woocommerce_currency();

    // Get product image
    $image_url = wp_get_attachment_image_url( $product->get_image_id(), 'full' );

    // Get product URL
    $product_url = get_permalink( $product->get_id() );

    // Get availability
    $availability = $product->is_in_stock() ? 'InStock' : 'OutOfStock';

    // Output meta tags
    echo "\n<!-- Dynamic Product SEO Meta Tags -->\n";
    echo '<meta name="description" content="' . esc_attr( $description ) . '">' . "\n";
    
    // Output JSON-LD Schema for Product
    echo '<script type="application/ld+json">' . "\n";
    $schema = array(
        '@context' => 'https://schema.org',
        '@type' => 'Product',
        'name' => $product_name,
        'sku' => $original_sku,
        'description' => $description,
        'url' => $product_url,
    );

    // Add image if available
    if ( $image_url ) {
        $schema['image'] = $image_url;
    }

    // Add offers (price info)
    if ( $price ) {
        $schema['offers'] = array(
            '@type' => 'Offer',
            'price' => $price,
            'priceCurrency' => $currency,
            'availability' => 'https://schema.org/' . $availability,
            'url' => $product_url,
        );
    }

    // Add vehicle model as additionalProperty if available
    if ( ! empty( $vehicle_models ) ) {
        $schema['additionalProperty'] = array();
        foreach ( $vehicle_models as $model ) {
            $schema['additionalProperty'][] = array(
                '@type' => 'PropertyValue',
                'name' => 'Vehicle Model',
                'value' => $model,
            );
        }
    }

    // Add brand (Maxus)
    $schema['brand'] = array(
        '@type' => 'Brand',
        'name' => 'Maxus',
    );

    echo wp_json_encode( $schema, JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT );
    echo "\n" . '</script>' . "\n";
    echo "<!-- End Dynamic Product SEO -->\n";
}

// ============================================================
// 13. COMPONENT DIAGRAM — SVG + PARTS TABLE ON LEAF CATEGORY PAGES
// ============================================================

/**
 * On a leaf product_cat page (depth >= 3 below Maxus) that has component_svg_code
 * and component_parts_json term meta set, render an interactive SVG diagram
 * alongside a parts table grouped by call_out_order.
 * Clicking a callout number in the SVG highlights the matching row(s), and vice versa.
 */
add_action( 'woocommerce_before_shop_loop', 'mvp_render_component_diagram', 5 );
function mvp_render_component_diagram() {
    if ( ! is_tax( 'product_cat' ) ) return;

    $term = get_queried_object();
    if ( ! ( $term instanceof WP_Term ) ) return;

    // Must be at least 3 levels below Maxus root (Maxus > VIN > mid-category > leaf)
    $maxus_id  = mvp_get_maxus_term_id();
    $ancestors = get_ancestors( $term->term_id, 'product_cat', 'taxonomy' );
    if ( count( $ancestors ) < 2 || ! in_array( $maxus_id, $ancestors, true ) ) return;

    $svg_code   = get_term_meta( $term->term_id, 'component_svg_code',   true );
    $parts_json = get_term_meta( $term->term_id, 'component_parts_json', true );
    if ( ! $svg_code || ! $parts_json ) return;

    $parts = json_decode( $parts_json, true );
    if ( ! is_array( $parts ) || empty( $parts ) ) return;

    // Build lookup: original_sku (uppercase) -> product post
    // The import stores original_sku = JSON part_number (e.g. "C00157255")
    $products_by_sku = array();
    $loop = new WP_Query( array(
        'post_type'      => 'product',
        'post_status'    => 'publish',
        'posts_per_page' => 500,
        'tax_query'      => array( array(
            'taxonomy' => 'product_cat',
            'field'    => 'term_id',
            'terms'    => $term->term_id,
        ) ),
    ) );
    foreach ( $loop->posts as $p ) {
        $sku = get_post_meta( $p->ID, 'original_sku', true );
        if ( $sku ) {
            $wc_product = wc_get_product( $p->ID );
            $products_by_sku[ strtoupper( trim( $sku ) ) ] = array(
                'post'       => $p,
                'wc_product' => $wc_product,
            );
        }
    }

    // Group parts by call_out_order
    $grouped = array();
    foreach ( $parts as $part ) {
        $order = (int) ( $part['call_out_order'] ?? 0 );
        $grouped[ $order ][] = $part;
    }
    ksort( $grouped );

    $uid = 'mvp-cd-' . $term->term_id;
    ?>
    <div class="mvp-component-diagram" id="<?php echo esc_attr( $uid ); ?>">

        <div class="mvp-cd-svg-wrap">
            <div class="mvp-cd-zoom-controls" aria-label="Zoom controls">
                <button class="mvp-cd-zoom-btn" data-action="out" aria-label="Zoom out">&#8722;</button>
                <button class="mvp-cd-zoom-btn" data-action="reset" aria-label="Reset zoom">&#8635;</button>
                <button class="mvp-cd-zoom-btn" data-action="in" aria-label="Zoom in">&#43;</button>
            </div>
            <div class="mvp-cd-svg-inner">
            <?php
            // SVG originates from the Oscar EPC database via our own import pipeline —
            // not user-submitted. Direct output is appropriate here.
            echo $svg_code; // phpcs:ignore WordPress.Security.EscapeOutput
            ?>
            </div>
        </div>

        <div class="mvp-cd-table-wrap">
            <table class="mvp-cd-table">
                <thead>
                    <tr>
                        <th class="mvp-cd-th-num">#</th>
                        <th>Part No.</th>
                        <th>Description</th>
                        <th class="mvp-cd-th-price">Price</th>
                        <th class="mvp-cd-th-cart"></th>
                    </tr>
                </thead>
                <tbody>
                <?php foreach ( $grouped as $callout_num => $group_parts ) : ?>
                    <tr class="mvp-cd-row" data-callout="<?php echo esc_attr( $callout_num ); ?>">
                        <td class="mvp-cd-num"><?php echo esc_html( $callout_num ); ?></td>
                        <td class="mvp-cd-part-col">
                        <?php foreach ( $group_parts as $i => $part ) :
                            $sku_key    = strtoupper( trim( $part['part_number'] ?? '' ) );
                            $entry      = $products_by_sku[ $sku_key ] ?? null;
                            $prod       = $entry ? $entry['post']       : null;
                            $wc_product = $entry ? $entry['wc_product'] : null;
                        ?>
                            <div class="mvp-cd-part-line<?php echo $i > 0 ? ' mvp-cd-sep' : ''; ?>">
                                <?php if ( $prod ) : ?>
                                    <a href="<?php echo esc_url( get_permalink( $prod->ID ) ); ?>">
                                        <?php echo esc_html( $part['part_number'] ); ?>
                                    </a>
                                <?php else : ?>
                                    <?php echo esc_html( $part['part_number'] ); ?>
                                <?php endif; ?>
                            </div>
                        <?php endforeach; ?>
                        </td>
                        <td class="mvp-cd-desc-col">
                        <?php foreach ( $group_parts as $i => $part ) :
                            $sku_key_d  = strtoupper( trim( $part['part_number'] ?? '' ) );
                            $entry_d    = $products_by_sku[ $sku_key_d ] ?? null;
                            $prod_d     = $entry_d ? $entry_d['post'] : null;
                            $lr_val_d   = $prod_d ? get_post_meta( $prod_d->ID, 'lr', true ) : '';
                        ?>
                            <div class="mvp-cd-part-line<?php echo $i > 0 ? ' mvp-cd-sep' : ''; ?>">
                                <?php echo esc_html( $part['usage_name'] ); ?>
                                <?php if ( $lr_val_d ) : ?>
                                    <span class="mvp-cd-lr-badge mvp-cd-lr-<?php echo esc_attr( strtolower( $lr_val_d ) ); ?>"><?php echo esc_html( $lr_val_d ); ?></span>
                                <?php endif; ?>
                            </div>
                        <?php endforeach; ?>
                        </td>
                        <td class="mvp-cd-price-col">
                        <?php foreach ( $group_parts as $i => $part ) :
                            $sku_key    = strtoupper( trim( $part['part_number'] ?? '' ) );
                            $entry      = $products_by_sku[ $sku_key ] ?? null;
                            $wc_product = $entry ? $entry['wc_product'] : null;
                        ?>
                            <div class="mvp-cd-part-line<?php echo $i > 0 ? ' mvp-cd-sep' : ''; ?>">
                                <?php if ( $wc_product && $wc_product->get_price() !== '' ) : ?>
                                    <?php echo wp_kses_post( wc_price( $wc_product->get_price() ) ); ?>
                                <?php else : ?>
                                    <span class="mvp-cd-no-price">—</span>
                                <?php endif; ?>
                            </div>
                        <?php endforeach; ?>
                        </td>
                        <td class="mvp-cd-cart-col">
                        <?php foreach ( $group_parts as $i => $part ) :
                            $sku_key    = strtoupper( trim( $part['part_number'] ?? '' ) );
                            $entry      = $products_by_sku[ $sku_key ] ?? null;
                            $prod       = $entry ? $entry['post']       : null;
                            $wc_product = $entry ? $entry['wc_product'] : null;
                        ?>
                            <div class="mvp-cd-part-line<?php echo $i > 0 ? ' mvp-cd-sep' : ''; ?>">
                                <?php if ( $prod && $wc_product && $wc_product->is_purchasable() && $wc_product->is_in_stock() ) : ?>
                                    <a href="<?php echo esc_url( $wc_product->add_to_cart_url() ); ?>"
                                       class="mvp-cd-atc-btn"
                                       aria-label="<?php echo esc_attr( 'Add ' . $part['part_number'] . ' to cart' ); ?>">
                                        Add to cart
                                    </a>
                                <?php elseif ( $prod && $wc_product && ( $wc_product->get_price() === '' || $wc_product->get_price() === null ) ) :
                                    $lr_val = get_post_meta( $prod->ID, 'lr', true );
                                    $remark_val = get_post_meta( $prod->ID, 'remark', true );
                                ?>
                                    <button type="button"
                                       class="mvp-cd-atc-btn mvp-cd-request-price"
                                       data-sku="<?php echo esc_attr( $wc_product->get_sku() ); ?>"
                                       data-name="<?php echo esc_attr( $prod->post_title ); ?>"
                                       data-url="<?php echo esc_url( get_permalink( $prod->ID ) ); ?>"
                                       data-lr="<?php echo esc_attr( $lr_val ); ?>"
                                       data-remark="<?php echo esc_attr( $remark_val ); ?>"
                                       onclick="event.stopPropagation(); mvpOpenPriceModalFromTable(this)">
                                        Request Price
                                    </button>
                                <?php elseif ( $prod ) : ?>
                                    <a href="<?php echo esc_url( get_permalink( $prod->ID ) ); ?>"
                                       class="mvp-cd-atc-btn mvp-cd-atc-view">
                                        View
                                    </a>
                                <?php endif; ?>
                            </div>
                        <?php endforeach; ?>
                        </td>
                    </tr>
                <?php endforeach; ?>
                </tbody>
            </table>
        </div>

    </div>

    <style>
    .mvp-component-diagram {
        display: flex;
        gap: 24px;
        margin: 0 0 32px;
        align-items: flex-start;
        flex-wrap: wrap;
    }
    .mvp-cd-svg-wrap {
        flex: 0 1 45%;
        min-width: 280px;
        border: 1px solid #dde3e9;
        background: #fff;
        border-radius: 6px;
        overflow: hidden;
        max-height: 640px;
        display: flex;
        flex-direction: column;
    }
    .mvp-cd-zoom-controls {
        display: flex;
        gap: 6px;
        padding: 6px 8px;
        background: #f4f6f8;
        border-bottom: 1px solid #dde3e9;
        flex-shrink: 0;
    }
    .mvp-cd-zoom-btn {
        width: 30px;
        height: 30px;
        border: 1px solid #bbc5d0;
        border-radius: 4px;
        background: #fff;
        cursor: pointer;
        font-size: 18px;
        line-height: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #1a2d4a;
        transition: background 0.15s;
    }
    .mvp-cd-zoom-btn:hover { background: #e8edf2; }
    .mvp-cd-svg-inner {
        overflow: auto;
        flex: 1;
        cursor: grab;
    }
    .mvp-cd-svg-inner svg {
        width: 100%;
        height: auto;
        display: block;
        transform-origin: top left;
        transition: transform 0.2s;
    }
    .mvp-cd-table-wrap {
        flex: 1 1 320px;
        overflow-x: auto;
        overflow-y: auto;
    }
    .mvp-cd-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        background: #fff;
        border: 1px solid #dde3e9;
        border-radius: 6px;
        overflow: hidden;
    }
    .mvp-cd-table thead th { 
        background: #D18A0C;
        color: #fff;
        padding: 10px 14px;
        text-align: left;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: .03em;
    }
    .mvp-cd-th-num  { width: 42px; text-align: center; line-height: 48px; }
    .mvp-cd-th-qty  { width: 52px; }
    .mvp-cd-table tbody tr {
        border-bottom: 1px solid #edf0f4;
        cursor: pointer;
        transition: background 0.15s;
    }
    .mvp-cd-table tbody tr:last-child { border-bottom: none; }
    .mvp-cd-table tbody tr:hover   { background: #f5f8ff; }
    .mvp-cd-table tbody tr.mvp-cd-active { background: #fff3cd; }
    .mvp-cd-table td { padding: 9px 14px; vertical-align: top; }
    .mvp-cd-num {
        font-weight: 700;
        font-size: 15px;
        color: #1a2d4a;
        text-align: center; line-height: 48px;
    }
    .mvp-cd-price-col { text-align: right; white-space: nowrap; font-weight: 600; color: #1a2d4a; }
    .mvp-cd-no-price  { color: #aaa; }
    .mvp-cd-cart-col  { text-align: center; line-height: 48px; white-space: nowrap; }
    .mvp-cd-lr-badge {
        display: inline-block;
        font-size: 10px;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 3px;
        margin-left: 6px;
        text-transform: uppercase;
        vertical-align: middle;
    }
    .mvp-cd-lr-left {
        background: #e3f2fd;
        color: #1565c0;
    }
    .mvp-cd-lr-right {
        background: #fce4ec;
        color: #c62828;
    }
    .mvp-cd-request-price {
        background: #BF3617 !important;
        color: #fff !important;
        border: none !important;
        cursor: pointer;
    }
    .mvp-cd-request-price:hover { background: #a82e13 !important; }
    .mvp-cd-atc-btn {
        display: inline-block;
        padding: 4px 10px;
        background: #BF3617;
        color: #fff !important;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        text-decoration: none !important;
        white-space: nowrap;
        transition: background 0.15s;
    }
    .mvp-cd-atc-btn:hover { background: #a02e13; }
    .mvp-cd-atc-view { background: #6c7a8d; }
    .mvp-cd-atc-view:hover { background: #4a5568; }
    .mvp-cd-sep { border-top: 1px dashed #ddd; padding-top: 8px; margin-top: 4px; }
    .mvp-cd-part-col a { color: #1a2d4a; font-weight: 600; text-decoration: underline; }
    .mvp-cd-part-col a:hover { color: #F29F05; }
    @media (max-width: 700px) {
        .mvp-cd-svg-wrap { flex: 0 0 100%; max-height: none; }
    }
    </style>

    <script>
    document.addEventListener("DOMContentLoaded", function () {
        var wrap = document.getElementById('<?php echo esc_js( $uid ); ?>');
        if (!wrap) return;
        var rows   = Array.from(wrap.querySelectorAll('.mvp-cd-row'));
        // Prefer the diagram SVG inside this widget's container (robust for small
        // diagrams with <=5 callouts, where the old text-count heuristic failed).
        var svg = wrap.querySelector('.mvp-cd-svg-inner svg');
        if (!svg) { document.querySelectorAll('svg').forEach(function(s) { if (!svg && s.querySelectorAll('text').length > 5) svg = s; }); }
        // Only EXPAND viewBox if content is clipped outside it (never shrink) — uses svg.getBBox for full coverage
        if (svg) {
            try {
                var vb = (svg.getAttribute('viewBox') || '0 0 100 100').split(/\s+/).map(Number);
                var vbX=vb[0], vbY=vb[1], vbW=vb[2], vbH=vb[3];
                var bb = svg.getBBox();
                var mnX = Math.min(vbX, bb.x);
                var mnY = Math.min(vbY, bb.y);
                var mxX = Math.max(vbX+vbW, bb.x+bb.width);
                var mxY = Math.max(vbY+vbH, bb.y+bb.height);
                var changed = (mnX < vbX || mnY < vbY || mxX > vbX+vbW || mxY > vbY+vbH);
                if(changed){ var p=15; svg.setAttribute('viewBox',(mnX-p)+' '+(mnY-p)+' '+(mxX-mnX+p*2)+' '+(mxY-mnY+p*2)); }
            } catch(e) {}
        }
        // Save original SVG fills/strokes at init
        if (svg) {
            svg.querySelectorAll("text").forEach(function(t) {
                t.setAttribute("data-orig-fill", t.getAttribute("fill") || "");
                t.setAttribute("data-orig-size", t.getAttribute("font-size") || "9");
            });
        }
        var inner  = wrap.querySelector('.mvp-cd-svg-inner');
        var scale  = 1;
        var STEP   = 0.2;
        var MIN    = 0.4;
        var MAX    = 4;

        // ── Zoom controls ────────────────────────────────────────────────
        wrap.querySelectorAll('.mvp-cd-zoom-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var action = btn.dataset.action;
                if (action === 'in')    scale = Math.min(MAX, +(scale + STEP).toFixed(2));
                if (action === 'out')   scale = Math.max(MIN, +(scale - STEP).toFixed(2));
                if (action === 'reset') scale = 1;
                if (svg) svg.style.transform = scale === 1 ? '' : 'scale(' + scale + ')';
                // Expand inner height when zoomed so scrolling works
                if (inner && svg) {
                    inner.style.height = scale > 1
                        ? (svg.getBoundingClientRect().height * scale + 40) + 'px'
                        : '';
                }
            });
        });

        // ── Callout highlighting ─────────────────────────────────────────
        function activate(num) {
            var n = String(num);
            rows.forEach(function (r) {
                r.classList.toggle('mvp-cd-active', r.dataset.callout === n);
            });
            // Re-resolve the diagram SVG if it wasn't captured at load (guards
            // against a DOMContentLoaded timing race on large inline SVGs).
            if (!svg) { svg = wrap.querySelector('.mvp-cd-svg-inner svg'); }
            if (svg) {
                svg.querySelectorAll('text').forEach(function (t) {
                    var orig = t.getAttribute('data-orig-fill') || '';
                    if (t.textContent.trim() === n) {
                        t.style.setProperty('fill', '#F29F05', 'important');
                        t.style.setProperty('font-weight', 'bold', 'important');
                        t.style.setProperty('font-size', '14px', 'important');
                    } else {
                        t.style.removeProperty('fill');
                        t.style.removeProperty('font-weight');
                        var os = t.getAttribute('data-orig-size');
                        t.style.removeProperty('font-size');
                    }
                });
            }
        }

        function deactivate() {
            rows.forEach(function (r) { r.classList.remove('mvp-cd-active'); });
            if (svg) {
                svg.querySelectorAll('text').forEach(function (t) {
                    var orig = t.getAttribute('data-orig-fill') || '';
                    t.style.removeProperty('fill');
                    t.style.removeProperty('font-weight');
                    var os = t.getAttribute('data-orig-size');
                    t.style.removeProperty('font-size');
                });
            }
        }

        // Table row click → highlight SVG callout
        rows.forEach(function (row) {
            row.addEventListener('click', function () {
                activate(row.dataset.callout);
            });
            row.addEventListener('mouseenter', function () {
                activate(row.dataset.callout);
            });
            row.addEventListener('mouseleave', function () {
                deactivate();
            });
        });

        // SVG text click → highlight row + scroll into view
        if (svg) {
            svg.querySelectorAll('text').forEach(function (t) {
                var n = t.textContent.trim();
                if (/^\d+$/.test(n)) {
                    t.style.cursor = 'pointer';
                    t.addEventListener('click', function (e) {
                        e.stopPropagation();
                        activate(n);
                        var tableWrap = wrap.querySelector('.mvp-cd-table-wrap');
                        var match = rows.find(function (r) { return r.dataset.callout === n; });
                        if (match && tableWrap) match.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    });
                }
            });
        }

        // ── Sync table height to SVG diagram height ──────────────────────
        var svgWrap = wrap.querySelector('.mvp-cd-svg-wrap');
        var tableWrap = wrap.querySelector('.mvp-cd-table-wrap');
        if (svgWrap && tableWrap && window.innerWidth > 700) {
            function syncTableHeight() {
                var svgH = svgWrap.offsetHeight;
                if (svgH > 200) {
                    tableWrap.style.maxHeight = svgH + 'px';
                }
            }
            syncTableHeight();
            window.addEventListener('resize', syncTableHeight);
        }
    });
    </script>
    <?php
}


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
            'vehicle_serial' => array(
                'required'          => false,
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

    // --- POST /products-by-skus-bulk: look up many SKUs in one query ---
    register_rest_route( 'custom/v1', '/products-by-skus-bulk', array(
        'methods'             => 'POST',
        'callback'            => 'cvone_bulk_products_by_original_sku',
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
    // Accept the same shared secret used by the component-meta endpoint
    $secret = $request->get_param( 'secret' );
    if ( $secret && defined( 'MVP_COMPONENT_API_SECRET' ) && hash_equals( MVP_COMPONENT_API_SECRET, (string) $secret ) ) {
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
 * Query the postmeta table directly for original_sku (+ optional vehicle_serial) matches.
 * Returns all post IDs (products + variations) that match.
 */
function cvone_query_ids_by_original_sku( $sku, $vehicle_serial = '' ) {
    global $wpdb;
    $sku            = sanitize_text_field( $sku );
    $vehicle_serial = sanitize_text_field( $vehicle_serial );

    if ( $vehicle_serial ) {
        // Narrow to posts that have BOTH original_sku AND vehicle_serial meta
        $ids = $wpdb->get_col( $wpdb->prepare(
            "SELECT pm1.post_id
               FROM {$wpdb->postmeta} pm1
               JOIN {$wpdb->postmeta} pm2 ON pm2.post_id = pm1.post_id
              WHERE pm1.meta_key   = 'original_sku'
                AND pm1.meta_value = %s
                AND pm2.meta_key   = 'vehicle_serial'
                AND pm2.meta_value = %s",
            $sku,
            $vehicle_serial
        ) );
    } else {
        $ids = $wpdb->get_col( $wpdb->prepare(
            "SELECT post_id
               FROM {$wpdb->postmeta}
              WHERE meta_key   = 'original_sku'
                AND meta_value = %s",
            $sku
        ) );
    }

    return array_map( 'intval', $ids );
}

/**
 * POST /wp-json/custom/v1/products-by-skus-bulk
 * Body (JSON): { "skus": ["C00371126", ...], "secret": "..." }
 * Returns: { "C00371126": {id, parent_id, type, wc_sku, status}, ... }
 * SKUs with no match are omitted from the response.
 */
function cvone_bulk_products_by_original_sku( WP_REST_Request $request ) {
    global $wpdb;

    $body = $request->get_json_params();
    $skus = isset( $body['skus'] ) ? (array) $body['skus'] : array();

    if ( empty( $skus ) ) {
        return new WP_Error( 'missing_skus', 'No SKUs provided', array( 'status' => 400 ) );
    }

    // Sanitise and de-duplicate
    $skus = array_values( array_unique( array_map( 'sanitize_text_field', $skus ) ) );

    // Build a single IN (...) query
    $placeholders = implode( ',', array_fill( 0, count( $skus ), '%s' ) );
    // phpcs:ignore WordPress.DB.PreparedSQLPlaceholders.UnfinishedPrepare
    $rows = $wpdb->get_results(
        $wpdb->prepare(
            "SELECT post_id, meta_value AS original_sku
               FROM {$wpdb->postmeta}
              WHERE meta_key   = 'original_sku'
                AND meta_value IN ($placeholders)",
            ...$skus
        )
    );

    $result = array();
    foreach ( $rows as $row ) {
        $post      = get_post( (int) $row->post_id );
        if ( ! $post ) continue;
        $parent_id = (int) $post->post_parent;
        $result[ $row->original_sku ] = array(
            'id'           => (int) $row->post_id,
            'parent_id'    => $parent_id,
            'type'         => ( $parent_id > 0 ) ? 'variation' : 'product',
            'wc_sku'       => get_post_meta( (int) $row->post_id, '_sku', true ),
            'status'       => $post->post_status,
        );
    }

    return new WP_REST_Response( $result, 200 );
}


function cvone_get_products_by_original_sku( WP_REST_Request $request ) {
    $sku            = $request->get_param( 'original_sku' );
    $vehicle_serial = (string) $request->get_param( 'vehicle_serial' );
    $ids            = cvone_query_ids_by_original_sku( $sku, $vehicle_serial );

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

/**
 * Diagnostic: Check if functions.php is loaded and cache status
 */
add_action( 'rest_api_init', function () {
    register_rest_route( 'custom/v1', '/diagnostic', array(
        'methods'             => 'GET',
        'callback'            => 'cvone_diagnostic',
        'permission_callback' => '__return_true',
    ) );
} );

function cvone_diagnostic() {
    $functions_file = get_stylesheet_directory() . '/functions.php';
    $file_mtime = file_exists( $functions_file ) ? filemtime( $functions_file ) : 0;
    
    return new WP_REST_Response( array(
        'functions_php_modified' => $file_mtime > 0 ? date( 'Y-m-d H:i:s', $file_mtime ) : 'not found',
        'functions_php_modified_timestamp' => $file_mtime,
        'wordpress_time' => current_time( 'mysql' ),
        'php_version' => phpversion(),
        'opcache_enabled' => function_exists( 'opcache_get_status' ) && opcache_get_status() !== false,
        'test_cookie_value' => isset( $_COOKIE['mvp_vehicle_slug'] ) ? $_COOKIE['mvp_vehicle_slug'] : 'not set',
        'diagnostic_added' => 'March 19, 2026 - Cookie issue investigation',
    ), 200 );
}

// ============================================================
// 14. COMPONENT DIAGRAM — REST ENDPOINT TO SAVE TERM META
// ============================================================
// POST /wp-json/custom/v1/set-component-meta
// Body (JSON): { "term_id": 4356, "svg_code": "...", "parts_json": "[...]" }
// Auth: WC Consumer Key / Consumer Secret via HTTP Basic Auth.

// Secret shared between this endpoint and the import script.
// Change this value if you need to rotate it.
define( 'MVP_COMPONENT_API_SECRET', 'mvp-comp-2026-xK9pLq' );

add_action( 'rest_api_init', function () {
    register_rest_route( 'custom/v1', '/set-component-meta', array(
        'methods'             => 'POST',
        'callback'            => 'mvp_set_component_meta',
        'permission_callback' => 'mvp_set_component_meta_permission',
        'args'                => array(
            'term_id'    => array( 'required' => true,  'type' => 'integer' ),
            'svg_code'   => array( 'required' => false, 'type' => 'string'  ),
            'parts_json' => array( 'required' => false, 'type' => 'string'  ),
            'secret'     => array( 'required' => false, 'type' => 'string'  ),
        ),
    ) );
} );

function mvp_set_component_meta_permission( WP_REST_Request $request ) {
    // Allow logged-in admins (WP application-password auth) in addition to the shared secret.
    if ( is_user_logged_in() && current_user_can( 'manage_options' ) ) {
        return true;
    }
    $secret = $request->get_param( 'secret' );
    return hash_equals( MVP_COMPONENT_API_SECRET, (string) $secret );
}

function mvp_set_component_meta( WP_REST_Request $request ) {
    $term_id = (int) $request->get_param( 'term_id' );

    // Verify the term exists and is a product_cat
    $term = get_term( $term_id, 'product_cat' );
    if ( ! $term || is_wp_error( $term ) ) {
        return new WP_Error( 'invalid_term', 'Term not found or not a product_cat.', array( 'status' => 404 ) );
    }

    $updated = array();

    $svg_code = $request->get_param( 'svg_code' );
    // No-overwrite guard: only fill categories that currently have no diagram.
    if ( $svg_code !== null && ! get_term_meta( $term_id, 'component_svg_code', true ) ) {
        update_term_meta( $term_id, 'component_svg_code', $svg_code );
        $updated[] = 'component_svg_code';
    }

    $parts_json = $request->get_param( 'parts_json' );
    if ( $parts_json !== null && ! get_term_meta( $term_id, 'component_parts_json', true ) ) {
        // Validate it's parseable JSON
        $decoded = json_decode( $parts_json, true );
        if ( ! is_array( $decoded ) ) {
            return new WP_Error( 'invalid_json', 'parts_json must be a valid JSON array.', array( 'status' => 400 ) );
        }
        update_term_meta( $term_id, 'component_parts_json', $parts_json );
        $updated[] = 'component_parts_json';
    }

    return new WP_REST_Response( array(
        'success' => true,
        'term_id' => $term_id,
        'term_name' => $term->name,
        'updated'   => $updated,
    ), 200 );
}


// ============================================================
// 15. SUBCATEGORY GRID — MID-LEVEL CATEGORY PAGES
// ============================================================

/**
 * On mid-level category pages with exactly 1 leaf child, skip straight to the leaf.
 */
add_action( 'template_redirect', 'mvp_midlevel_single_child_redirect' );
function mvp_midlevel_single_child_redirect() {
    if ( ! is_tax( 'product_cat' ) ) return;

    $term = get_queried_object();
    if ( ! ( $term instanceof WP_Term ) ) return;

    $maxus_id  = mvp_get_maxus_term_id();
    $ancestors = get_ancestors( $term->term_id, 'product_cat', 'taxonomy' );

    // Only act on mid-level: exactly 2 ancestors = [VIN-id, Maxus-id]
    if ( count( $ancestors ) !== 2 || ! in_array( $maxus_id, $ancestors, true ) ) return;

    $children = get_terms( array(
        'taxonomy'   => 'product_cat',
        'parent'     => $term->term_id,
        'hide_empty' => false,
        'number'     => 2, // only need to know if count is 1
    ) );

    if ( ! is_wp_error( $children ) && count( $children ) === 1 ) {
        wp_redirect( get_term_link( $children[0] ), 302 );
        exit;
    }
}

/**
 * On mid-level category pages (Maxus > VIN > mid-category), show the
 * leaf sub-categories as clickable cards instead of a flat product listing.
 * Depth detected by ancestor count: exactly 2 ancestors = [VIN, Maxus].
 */
add_action( 'woocommerce_before_shop_loop', 'mvp_render_midlevel_subcat_grid', 4 );
function mvp_render_midlevel_subcat_grid() {
    if ( ! is_tax( 'product_cat' ) ) return;

    $term = get_queried_object();
    if ( ! ( $term instanceof WP_Term ) ) return;

    $maxus_id  = mvp_get_maxus_term_id();
    $ancestors = get_ancestors( $term->term_id, 'product_cat', 'taxonomy' );

    // Mid-level: exactly 2 ancestors = [VIN-id, Maxus-id]
    if ( count( $ancestors ) !== 2 || ! in_array( $maxus_id, $ancestors, true ) ) return;

    $children = get_terms( array(
        'taxonomy'   => 'product_cat',
        'parent'     => $term->term_id,
        'hide_empty' => false,
        'orderby'    => 'name',
        'order'      => 'ASC',
    ) );

    if ( is_wp_error( $children ) || empty( $children ) ) return;

    // Suppress the product loop, result count, and sort order that follow
    remove_action( 'woocommerce_before_shop_loop', 'woocommerce_result_count',    20 );
    remove_action( 'woocommerce_before_shop_loop', 'woocommerce_catalog_ordering', 30 );
    wc_set_loop_prop( 'total', 0 );
    add_filter( 'woocommerce_product_loop_start', '__return_empty_string' );
    add_filter( 'woocommerce_product_loop_end',   '__return_empty_string' );
    remove_all_actions( 'woocommerce_after_shop_loop' );
    remove_action( 'woocommerce_no_products_found', 'wc_no_products_found' );

    ?>
    <div class="mvp-subcat-grid">
        <?php foreach ( $children as $child ) :
            $link  = get_term_link( $child );
            $count = (int) $child->count;
        ?>
        <?php
            $img_name = mvp_category_icon_file( $child->name );
            $has_img  = ( $img_name !== '' );
        ?>
        <a class="mvp-subcat-card<?php echo $has_img ? ' has-img' : ''; ?>" href="<?php echo esc_url( $link ); ?>">
            <?php if ( $has_img ) : ?>
            <span class="mvp-subcat-img"><img src="<?php echo esc_url( content_url( '/uploads/categories/' . $img_name ) ); ?>" alt="<?php echo esc_attr( $child->name ); ?>" /></span>
            <?php else : ?>
            <span class="mvp-subcat-icon">&#9741;</span>
            <?php endif; ?>
            <span class="mvp-subcat-name"><?php echo esc_html( $child->name ); ?></span>
            <?php if ( $count > 0 ) : ?>
            <span class="mvp-subcat-count"><?php echo esc_html( $count ); ?> part<?php echo $count !== 1 ? 's' : ''; ?></span>
            <?php endif; ?>
        </a>
        <?php endforeach; ?>
    </div>

    <style>
    .mvp-subcat-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        margin: 0 0 40px;
    }
.mvp-subcat-card {        flex: 1 1 200px;        max-width: 260px;        display: flex;        flex-direction: column;        align-items: center;        justify-content: center;        gap: 8px;        background: #fff;        color: #333;        text-decoration: none;        border-radius: 10px;        border: 1px solid #eee;        padding: 32px 20px;        text-align: center;        transition: transform 0.3s, box-shadow 0.3s;        box-shadow: none;    }
.mvp-subcat-card:hover {        transform: translateY(-4px);        box-shadow: 0 8px 25px rgba(0,0,0,0.1);    }
    .mvp-subcat-img {
        background: #f5f5f5;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #f5f5f5;
        border-radius: 10px 10px 0 0;
        padding: 8px;
        margin-bottom: 4px;
    }
    .mvp-subcat-img img {
        max-width: 100%;
        max-height: 120px;
        object-fit: contain;
    }
    .mvp-subcat-card.has-img {
        overflow: hidden;
        padding: 12px 12px 20px;
    }
    .mvp-subcat-icon {
        font-size: 28px;
        line-height: 1;
        opacity: 0.7;
    }
    .mvp-subcat-name {
        color: #1a1a2e;
        font-size: 16px;
        font-weight: 700;
        letter-spacing: .01em;
        line-height: 1.3;
    }
    .mvp-subcat-count {
        color: #999;
        font-size: 12px;
        opacity: 0.75;
        font-weight: 400;
    }
    @media (max-width: 600px) {
.mvp-subcat-card {        flex: 1 1 200px;        max-width: 260px;        display: flex;        flex-direction: column;        align-items: center;        justify-content: center;        gap: 8px;        background: #fff;        color: #333;        text-decoration: none;        border-radius: 10px;        border: 1px solid #eee;        padding: 32px 20px;        text-align: center;        transition: transform 0.3s, box-shadow 0.3s;        box-shadow: none;    }
    </style>
    <?php
}
// ============================================================
// 16. CHECKOUT — Vehicle VIN / Registration Confirmation Field
// ============================================================
add_action( 'wp_footer', 'mvp_checkout_vehicle_field', 99 );
function mvp_checkout_vehicle_field() {
    if ( ! is_checkout() ) return;
    ?>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        function addVehicleField() {
            if (document.getElementById('mvp-checkout-vehicle-field')) return;
            // Find the order notes or the place order section
            var target = document.querySelector('.wc-block-checkout__actions, .wc-block-components-checkout-place-order-button, #order_review, .woocommerce-checkout-review-order');
            if (!target) return;
            var wrap = document.createElement('div');
            wrap.id = 'mvp-checkout-vehicle-field';
            wrap.style.cssText = "border:2px dashed #D18A0C;border-radius:8px;padding:28px 32px;margin:0 0 24px;";
            wrap.innerHTML = '<h3 style="font-family:Inter,sans-serif;font-size:20px;font-weight:600;margin:0 0 12px;color:#333;">Vehicle Verification</h3>' +
                '<p style="font-size:14px;color:#666;line-height:1.6;margin:0 0 20px;">To help ensure you receive the correct parts, please provide the registration number or VIN for each vehicle these parts are intended for. While we make every effort to keep our site accurate and up to date, part numbers can change and descriptions may vary between manufacturers.</p>' +
                '<div id="mvp-vehicle-entries">' +
                '<div class="mvp-vehicle-entry" style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:12px;">' +
                '<div style="flex:1;min-width:200px;"><label style="display:block;font-size:11px;font-weight:700;color:#333;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">Registration Number</label><input type="text" name="vehicle_reg[]" placeholder="E.G. AB12 CDE" style="width:100%;height:44px;padding:0 14px;border:1px solid #ddd;border-radius:4px;font-size:14px;text-transform:uppercase;"></div>' +
                '<div style="flex:1;min-width:200px;"><label style="display:block;font-size:11px;font-weight:700;color:#333;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">VIN Number</label><input type="text" name="vehicle_vin[]" placeholder="E.G. 4T4BE46K79R107189" maxlength="17" style="width:100%;height:44px;padding:0 14px;border:1px solid #ddd;border-radius:4px;font-size:14px;text-transform:uppercase;"></div>' +
                '</div></div>' +
                '<button type="button" id="mvp-add-vehicle" style="background:none;border:1px solid #ddd;border-radius:4px;padding:8px 16px;font-size:13px;color:#333;cursor:pointer;margin:8px 0 16px;">+ Add another vehicle</button>' +
                '<div style="border-top:1px solid #eee;padding-top:14px;margin-top:8px;">' +
                '<label style="display:flex;align-items:center;gap:8px;font-size:14px;color:#555;cursor:pointer;">' +
                '<input type="checkbox" name="skip_vehicle_details" style="width:16px;height:16px;"> Continue without providing vehicle details</label></div>';
            target.parentNode.insertBefore(wrap, target);
            // Add another vehicle button
            document.getElementById("mvp-add-vehicle").addEventListener("click", function() {
                var entries = document.getElementById("mvp-vehicle-entries");
                var newEntry = document.createElement("div");
                newEntry.className = "mvp-vehicle-entry";
                newEntry.style.cssText = "display:flex;gap:16px;flex-wrap:wrap;margin-bottom:12px;";
                newEntry.innerHTML = '<div style="flex:1;min-width:200px;"><label style="display:block;font-size:11px;font-weight:700;color:#333;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">Registration Number</label><input type="text" name="vehicle_reg[]" placeholder="E.G. AB12 CDE" style="width:100%;height:44px;padding:0 14px;border:1px solid #ddd;border-radius:4px;font-size:14px;text-transform:uppercase;"></div>' +
                '<div style="flex:1;min-width:200px;"><label style="display:block;font-size:11px;font-weight:700;color:#333;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">VIN Number</label><input type="text" name="vehicle_vin[]" placeholder="E.G. 4T4BE46K79R107189" maxlength="17" style="width:100%;height:44px;padding:0 14px;border:1px solid #ddd;border-radius:4px;font-size:14px;text-transform:uppercase;"></div>';
                entries.appendChild(newEntry);
            });
        }
        // Try immediately and also observe for Blocks rendering
        addVehicleField();
        var obs = new MutationObserver(function() { addVehicleField(); });
        obs.observe(document.body, {childList: true, subtree: true});
        setTimeout(function() { obs.disconnect(); }, 10000);
    });
    </script>
    <?php
}

// Save the vehicle VIN/Reg field to order meta
add_action( 'woocommerce_checkout_update_order_meta', 'mvp_save_vehicle_field' );
function mvp_save_vehicle_field( $order_id ) {
    if ( ! empty( $_POST['vehicle_reg'] ) || ! empty( $_POST['vehicle_vin'] ) ) {
        $regs = isset( $_POST['vehicle_reg'] ) ? array_map( 'sanitize_text_field', $_POST['vehicle_reg'] ) : array();
        $vins = isset( $_POST['vehicle_vin'] ) ? array_map( 'sanitize_text_field', $_POST['vehicle_vin'] ) : array();
        $vehicles = array();
        for ( $i = 0; $i < max( count( $regs ), count( $vins ) ); $i++ ) {
            $r = isset( $regs[$i] ) ? trim( $regs[$i] ) : '';
            $v = isset( $vins[$i] ) ? trim( $vins[$i] ) : '';
            if ( $r || $v ) $vehicles[] = array( 'reg' => $r, 'vin' => $v );
        }
        if ( $vehicles ) {
        update_post_meta( $order_id, '_vehicle_verification', $vehicles );
        }
    }
}

// Display vehicle VIN/Reg in admin order
add_action( 'woocommerce_admin_order_data_after_billing_address', 'mvp_display_vehicle_field_admin' );
function mvp_display_vehicle_field_admin( $order ) {
    $vehicles = get_post_meta( $order->get_id(), '_vehicle_verification', true );
    if ( $vehicles && is_array( $vehicles ) ) {
        echo '<p><strong>Vehicle Verification:</strong></p>';
        foreach ( $vehicles as $v ) {
            echo '<p>Reg: ' . esc_html( $v['reg'] ) . ' | VIN: ' . esc_html( $v['vin'] ) . '</p>';
        }
    }
}

/* ── Round product weight display to 2 decimal places ── */
add_filter( 'woocommerce_product_get_weight', function( $weight ) {
    return is_numeric( $weight ) ? round( (float) $weight, 2 ) : $weight;
});

/* ── Subcategory thumbnails: fall back to /categories/ folder images ── */
add_action( 'init', function() {
    remove_action( 'woocommerce_before_subcategory_title', 'mobex_enovathemes_subcategory_thumbnail', 10 );
    add_action( 'woocommerce_before_subcategory_title', 'mvp_subcategory_thumbnail_fallback', 10 );
}, 20 );
function mvp_subcategory_thumbnail_fallback( $category ) {
    $thumbnail_id = get_term_meta( $category->term_id, 'thumbnail_id', true );
    if ( $thumbnail_id ) {
        echo wp_get_attachment_image( $thumbnail_id, 'woocommerce_thumbnail' );
    } else {
        $img_name = mvp_category_icon_file( $category->name );
        if ( $img_name !== '' ) {
            $img_url = content_url( '/uploads/categories/' . $img_name );
            echo '<img src="' . esc_url( $img_url ) . '" alt="' . esc_attr( $category->name ) . '" style="background:#fff;object-fit:contain;width:100%;height:auto;padding:10px;" />';
        } else {
            $placeholder = wc_placeholder_img_src();
            if ( $placeholder ) {
                echo '<img src="' . esc_url( $placeholder ) . '" />';
            }
        }
    }
}

// ============================================================
// Mobile: Force vehicle filter form visible (override theme JS slideToggle)
// ============================================================
add_action( 'wp_footer', function() {
    if ( ! is_front_page() && ! is_home() ) return;
    ?>
    <style>
    @media (max-width: 1024px) {
        .mvp-mobile-filter {
            background: #D18A0C;
            border-radius: 8px;
            padding: 16px;
            margin: 0 10px 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .mvp-mobile-filter select,
        .mvp-mobile-filter input[type=text] {
            width: 100%;
            height: 44px;
            padding: 0 12px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            color: #333;
            background: #fff;
            box-sizing: border-box;
            -webkit-appearance: menulist;
        }
        .mvp-mobile-filter input[type=text] {
            -webkit-appearance: none;
            text-align: center;
            text-transform: uppercase;
        }
        .mvp-mobile-filter input[type=text]::placeholder {
            color: #999;
            text-transform: uppercase;
        }
        .mvp-mobile-filter .mvp-mf-or {
            color: #fff;
            font-weight: 700;
            font-size: 12px;
            text-align: center;
        }
        .mvp-mobile-filter button {
            width: 100%;
            height: 48px;
            background: #BF3617;
            color: #fff;
            border: none;
            border-radius: 6px;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
        }
        .mvp-mobile-filter button:hover { background: #a82e13; }
    }
    @media (min-width: 1025px) {
        .mvp-mobile-filter { display: none !important; }
    }
    </style>
    <script>
    (function(){
        if (window.innerWidth > 1024) return;
        if (!document.body.classList.contains('home')) return;
        
        // Wait for DOM
        function injectMobileFilter() {
            if (document.querySelector('.mvp-mobile-filter')) return;
            
            // Find insertion point — after hero area or vehicle carousel
            var hero = document.getElementById('mvp-facelift-hero-area');
            var insertAfter = hero || document.querySelector('[data-id="60c0b2d"]');
            if (!insertAfter) return;
            
            var div = document.createElement('div');
            div.className = 'mvp-mobile-filter';
            div.innerHTML = 
                '<input type="text" class="mvp-mf-vin" placeholder="SEARCH BY VIN NUMBER" maxlength="17">' +
                '<div class="mvp-mf-or">OR</div>' +
                '<input type="text" class="mvp-mf-reg" placeholder="SEARCH BY REGISTRATION" maxlength="10">' +
                '<button type="button" class="mvp-mf-submit">Search</button>';
            
            insertAfter.parentNode.insertBefore(div, insertAfter.nextSibling);
            
            // Handle search
            div.querySelector('.mvp-mf-submit').addEventListener('click', function() {
                var vin = div.querySelector('.mvp-mf-vin').value.trim();
                var reg = div.querySelector('.mvp-mf-reg').value.trim();
                var home = window.location.origin;
                if (vin.length > 0) {
                    window.location.href = home + '/vin-search-test/?vin=' + encodeURIComponent(vin);
                } else if (reg.length > 0) {
                    window.location.href = home + '/registration-lookup/?reg=' + encodeURIComponent(reg);
                }
            });
            
            // Enter key support
            div.querySelectorAll('input[type="text"]').forEach(function(inp) {
                inp.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter') { e.preventDefault(); div.querySelector('.mvp-mf-submit').click(); }
                });
            });
        }
        
        setTimeout(injectMobileFilter, 300);
        setTimeout(injectMobileFilter, 1000);
    })();
    </script>
    <?php
}, 999 );

// ============================================================
// Favicon / Site Icon
// ============================================================
add_action( 'wp_head', function() {
    $site = home_url();
    echo '<link rel="icon" type="image/x-icon" href="' . $site . '/favicon.ico">';
    echo '<link rel="icon" type="image/png" sizes="32x32" href="' . $site . '/favicon-32.png">';
    echo '<link rel="icon" type="image/png" sizes="192x192" href="' . $site . '/favicon-192.png">';
    echo '<link rel="apple-touch-icon" sizes="180x180" href="' . $site . '/apple-touch-icon.png">';
}, 1 );


// ============================================================
// Featured Products section — homepage
// ============================================================
add_action( 'wp_head', function() {
    if ( ! is_front_page() && ! is_home() ) return;
    ?>
    <style>
    .mvp-featured-section { max-width: 1320px; margin: 20px auto 0; padding: 0 20px; }
    .mvp-featured-section h2 { font-size: 22px; font-weight: 700; color: #333; margin: 0 0 16px; }
    .mvp-featured-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
    }
    .mvp-feat-card {
        border: 1px solid #eee;
        border-radius: 8px;
        padding: 16px;
        display: flex;
        gap: 14px;
        align-items: flex-start;
        text-decoration: none;
        color: #333;
        transition: box-shadow 0.2s;
        background: #fff;
    }
    .mvp-feat-card:hover { box-shadow: 0 4px 15px rgba(0,0,0,0.08); }
    .mvp-feat-card-img {
        width: 100px;
        height: 100px;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #f9f9f9;
        border-radius: 6px;
        overflow: hidden;
    }
    .mvp-feat-card-img img { max-width: 90%; max-height: 90%; object-fit: contain; }
    .mvp-feat-card-info { flex: 1; min-width: 0; }
    .mvp-feat-card-title {
        font-size: 13px; font-weight: 700; color: #333;
        margin: 0 0 4px; line-height: 1.3;
        display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
    }
    .mvp-feat-card-sku { font-size: 11px; color: #999; margin: 0 0 8px; }
    .mvp-feat-card-price { font-size: 16px; font-weight: 700; color: #333; margin: 0 0 8px; }
    .mvp-feat-card-btn {
        float: right;
        display: inline-block; font-size: 12px; color: #fff; text-decoration: none; background: #BF3617;
        border: none; border-radius: 4px; padding: 6px 14px; font-weight: 600;
    }
    .mvp-feat-card-btn:hover { background: #a82e13; color: #fff; }
    @media (max-width: 900px) { .mvp-featured-grid { grid-template-columns: repeat(2, 1fr); } }
    @media (max-width: 600px) { .mvp-featured-grid { grid-template-columns: 1fr; } }
    </style>
    <?php
}, 21 );

add_action( 'wp_footer', 'mvp_featured_products_section', 12 );
function mvp_featured_products_section() {
    if ( ! is_front_page() && ! is_home() ) return;

    $args = array(
        'post_type'      => 'product',
        'posts_per_page' => 9,
        'post_status'    => 'publish',
        'orderby'        => 'date',
        'order'          => 'DESC',
        'meta_query'     => array(
            array(
                'key'     => '_price',
                'value'   => '',
                'compare' => '!=',
            ),
            array(
                'key'     => '_thumbnail_id',
                'compare' => 'EXISTS',
            ),
        ),
        'tax_query' => array(
            array(
                'taxonomy' => 'product_visibility',
                'field'    => 'name',
                'terms'    => 'exclude-from-catalog',
                'operator' => 'NOT IN',
            ),
        ),
    );
    $products = new WP_Query( $args );
    if ( ! $products->have_posts() ) { wp_reset_postdata(); return; }
    ?>
    <div class="mvp-featured-section" id="mvp-featured-products" style="display:none;">
        <h2>Featured Products</h2>
        <div class="mvp-featured-grid">
            <?php while ( $products->have_posts() ) : $products->the_post();
                $product = wc_get_product( get_the_ID() );
                if ( ! $product ) continue;
                $img = wp_get_attachment_image_src( get_post_thumbnail_id(), 'thumbnail' );
            ?>
            <a href="<?php the_permalink(); ?>" class="mvp-feat-card">
                <div class="mvp-feat-card-img">
                    <?php if ( $img ) : ?>
                    <img src="<?php echo esc_url( $img[0] ); ?>" alt="<?php echo esc_attr( get_the_title() ); ?>" loading="lazy">
                    <?php endif; ?>
                </div>
                <div class="mvp-feat-card-info">
                    <h3 class="mvp-feat-card-title"><?php the_title(); ?></h3>
                    <?php if ( $product->get_sku() ) : ?>
                    <p class="mvp-feat-card-sku">SKU: <?php echo esc_html( $product->get_sku() ); ?></p>
                    <?php endif; ?>
                    <p class="mvp-feat-card-price"><?php echo $product->get_price_html(); ?></p>
                    <span class="mvp-feat-card-btn">Add to cart</span>
                </div>
            </a>
            <?php endwhile; wp_reset_postdata(); ?>
        </div>
    </div>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        var section = document.getElementById('mvp-featured-products');
        if (!section) return;
        // Position it before the Why Use Us Elementor section (8b07793)
        var whyUs = document.querySelector('[data-id="8b07793"]');
        if (whyUs) {
            whyUs.parentNode.insertBefore(section, whyUs);
        } else {
            // Fallback: before the footer
            var footer = document.querySelector('.mvp-footer, footer');
            if (footer) footer.parentNode.insertBefore(section, footer);
        }
        section.style.display = 'block';
    });
    </script>
    <?php
}


// ============================================================
// Product Diagram — show SVG with highlighted callout on product page
// ============================================================

// Show "Part number X in diagram" in product summary above Estimated Delivery
add_action( 'woocommerce_single_product_summary', function() {
    global $product;
    if ( ! $product ) return;
    $callout = get_post_meta( $product->get_id(), 'callout_number', true );
    if ( ! $callout ) return;
    echo '<div class="mvp-callout-badge">';
    echo '<span class="mvp-callout-label">Part number </span>';
    echo '<span class="mvp-callout-num">' . esc_html( $callout ) . '</span>';
    echo '<span class="mvp-callout-label"> in diagram</span>';
    echo '</div>';
}, 27 );

// Replace the product gallery image with the SAME contained, zoomable diagram
// widget used on category pages (see mvp_render_component_diagram). The old
// approach forced the A4-portrait SVG into the gallery slot at height:auto and
// then EXPANDED the viewBox to include any stray off-page geometry (common in
// the EPC exports), which left many products with a tall empty box and a
// drifting orange callout ring. Containing the SVG in a fixed, scrollable box
// with a fit-to-box viewBox fixes every affected product uniformly.
add_action( 'wp_footer', 'mvp_product_svg_gallery', 30 );
function mvp_product_svg_gallery() {
    if ( ! is_product() ) return;
    global $product;
    if ( ! $product ) return;

    $callout = get_post_meta( $product->get_id(), 'callout_number', true );
    if ( ! $callout ) return;

    // Find the leaf category that carries the diagram SVG
    $cats = wp_get_post_terms( $product->get_id(), 'product_cat', array( 'fields' => 'all' ) );
    if ( is_wp_error( $cats ) || empty( $cats ) ) return;

    $svg_code = '';
    foreach ( $cats as $cat ) {
        $svg = get_term_meta( $cat->term_id, 'component_svg_code', true );
        if ( $svg ) { $svg_code = $svg; break; }
    }
    if ( ! $svg_code ) return;
    ?>
    <div id="mvp-pd-svg-source" style="display:none;"><?php echo $svg_code; ?></div>
    <script>
    (function(){
        var callout = '<?php echo esc_js( $callout ); ?>';
        var source  = document.getElementById('mvp-pd-svg-source');
        if (!source) return;

        // The real diagram is the SVG with the most text callouts (no fixed
        // threshold, so small diagrams with only a few callouts still build).
        var srcSvg = null;
        source.querySelectorAll('svg').forEach(function(s){
            if (!srcSvg || s.querySelectorAll('text').length > srcSvg.querySelectorAll('text').length) srcSvg = s;
        });
        if (!srcSvg) { source.remove(); return; }

        // Keep the SVG's native viewBox and fit-to-box (centre + clip). We do NOT
        // expand the viewBox to chase stray off-page geometry, so no whitespace.
        srcSvg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
        srcSvg.removeAttribute('width');
        srcSvg.removeAttribute('height');
        srcSvg.style.width   = '100%';
        srcSvg.style.height  = '100%';
        srcSvg.style.display = 'block';
        srcSvg.style.transformOrigin = 'top left';
        srcSvg.style.transition = 'transform 0.2s';
        srcSvg.style.background = '#fff';

        var gallery = document.querySelector('.woocommerce-product-gallery__image')
                   || document.querySelector('.woocommerce-product-gallery__image--placeholder');
        if (!gallery) { source.remove(); return; }

        // Build the same widget shell as the category page (zoom controls + inner)
        var box = document.createElement('div');
        box.className = 'mvp-cd-svg-wrap mvp-pd-widget';

        var controls = document.createElement('div');
        controls.className = 'mvp-cd-zoom-controls';
        controls.innerHTML =
            '<button type="button" class="mvp-cd-zoom-btn" data-action="out" aria-label="Zoom out">&#8722;</button>' +
            '<button type="button" class="mvp-cd-zoom-btn" data-action="reset" aria-label="Reset zoom">&#8635;</button>' +
            '<button type="button" class="mvp-cd-zoom-btn" data-action="in" aria-label="Zoom in">&#43;</button>';

        var inner = document.createElement('div');
        inner.className = 'mvp-cd-svg-inner';
        inner.appendChild(srcSvg);

        box.appendChild(controls);
        box.appendChild(inner);
        gallery.innerHTML = '';
        gallery.appendChild(box);
        gallery.style.cursor = 'default';

        // Highlight this product's callout number in orange and ring it
        srcSvg.querySelectorAll('text').forEach(function(t){
            if (t.textContent.trim() === callout) {
                t.style.setProperty('fill', '#F29F05', 'important');
                t.style.setProperty('font-weight', 'bold', 'important');
                try {
                    var bb = t.getBBox();
                    var c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                    c.setAttribute('cx', bb.x + bb.width / 2);
                    c.setAttribute('cy', bb.y + bb.height / 2);
                    c.setAttribute('r', Math.max(bb.width, bb.height) * 0.9 + 5);
                    c.setAttribute('fill', 'none');
                    c.setAttribute('stroke', '#F29F05');
                    c.setAttribute('stroke-width', '2');
                    // The callout text is positioned by its own transform, which getBBox
                    // ignores — copy it so the ring lands on the label, not at the origin.
                    var tf = t.getAttribute('transform');
                    if ( tf ) { c.setAttribute('transform', tf); }
                    t.parentNode.insertBefore(c, t);
                } catch(e) {}
            }
        });

        // Zoom: stepped +/-/reset buttons, PLUS hover-to-magnify (loupe) at
        // default scale — restores the original single-product hover behaviour.
        var scale = 1, STEP = 0.2, MIN = 0.4, MAX = 4, baseH = 0;
        var HOVER = 2.5, hovering = false;

        function applyBase(){
            srcSvg.style.transformOrigin = 'top left';
            srcSvg.style.transform = scale === 1 ? '' : 'scale(' + scale + ')';
            inner.style.overflow = scale > 1 ? 'auto' : 'hidden';
            inner.style.cursor   = scale > 1 ? 'grab' : 'zoom-in';
            inner.style.height   = scale > 1 ? (baseH * scale) + 'px' : '';
        }
        controls.querySelectorAll('.mvp-cd-zoom-btn').forEach(function(btn){
            btn.addEventListener('click', function(){
                if (!baseH) baseH = inner.clientHeight;
                var a = btn.dataset.action;
                if (a === 'in')    scale = Math.min(MAX, +(scale + STEP).toFixed(2));
                if (a === 'out')   scale = Math.max(MIN, +(scale - STEP).toFixed(2));
                if (a === 'reset') scale = 1;
                hovering = false;
                applyBase();
            });
        });
        applyBase();

        // Hover magnify — only when not stepped-zoomed via the buttons
        inner.addEventListener('mouseenter', function(){
            if (scale !== 1) return;
            hovering = true;
            inner.style.overflow = 'hidden';
        });
        inner.addEventListener('mousemove', function(e){
            if (scale !== 1 || !hovering) return;
            var r = inner.getBoundingClientRect();
            var x = (e.clientX - r.left) / r.width  * 100;
            var y = (e.clientY - r.top)  / r.height * 100;
            srcSvg.style.transformOrigin = x + '% ' + y + '%';
            srcSvg.style.transform = 'scale(' + HOVER + ')';
        });
        inner.addEventListener('mouseleave', function(){
            if (scale !== 1) return;
            hovering = false;
            srcSvg.style.transform = '';
            srcSvg.style.transformOrigin = 'top left';
        });

        // Kill the native WooCommerce zoom trigger left over from the gallery
        var trigger = document.querySelector('.woocommerce-product-gallery__trigger');
        if (trigger) trigger.style.display = 'none';

        source.remove();
    })();
    </script>
    <?php
}

add_action( 'wp_head', function() {
    if ( ! is_product() ) return;
    ?>
    <style>
    .mvp-product-diagram {
        max-width: 1300px;
        margin: 0 auto 40px;
        padding: 30px;
        background: #f9f9f9;
        border-radius: 12px;
        border: 1px solid #eee;
    }
    .mvp-product-diagram h3 {
        font-size: 18px;
        font-weight: 700;
        color: #1a1a2e;
        margin: 0 0 8px;
    }
    .mvp-callout-badge {
        background: #f5f5f5;
        border-left: 4px solid #BF3617;
        padding: 10px 16px;
        margin: 0 0 12px;
        border-radius: 0 6px 6px 0;
        font-size: 14px;
        color: #333;
    }
    .mvp-callout-num {
        font-weight: 700;
        color: #F29F05;
        font-size: 18px;
    }
    .woocommerce-product-gallery__trigger { display: none !important; }
    .woocommerce-product-gallery .zoomImg { display: none !important; }
    /* Single-product exploded-diagram widget — contained + zoomable, mirrors
       the category-page component diagram box (mvp_render_component_diagram) */
    .woocommerce-product-gallery__image .mvp-cd-svg-wrap.mvp-pd-widget {
        width: 100%;
        height: 520px;
        border: 1px solid #dde3e9;
        background: #fff;
        border-radius: 6px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }
    .mvp-pd-widget .mvp-cd-zoom-controls {
        display: flex;
        gap: 6px;
        padding: 6px 8px;
        background: #f4f6f8;
        border-bottom: 1px solid #dde3e9;
        flex-shrink: 0;
    }
    /* !important + min/max-width override the theme's single-product button
       min-width, which was stretching these to ~81px */
    .woocommerce-product-gallery__image .mvp-pd-widget .mvp-cd-zoom-btn {
        width: 34px !important;
        min-width: 34px !important;
        max-width: 34px !important;
        height: 30px !important;
        padding: 0 !important;
        margin: 0 !important;
        flex: 0 0 auto !important;
        box-sizing: border-box !important;
        border: 1px solid #F29F05 !important;
        border-radius: 4px !important;
        background: #F29F05 !important;
        cursor: pointer !important;
        font-size: 18px !important;
        line-height: 1 !important;
        display: flex !important;
        align-items: center;
        justify-content: center;
        color: #fff !important;
        transition: background 0.15s, border-color 0.15s;
    }
    .woocommerce-product-gallery__image .mvp-pd-widget .mvp-cd-zoom-btn:hover { background: #D18A0C !important; border-color: #D18A0C !important; }
    .mvp-pd-widget .mvp-cd-svg-inner {
        overflow: auto;
        flex: 1;
        cursor: grab;
        padding: 10px;
    }
    .mvp-pd-widget .mvp-cd-svg-inner svg {
        width: 100% !important;
        height: 100% !important;
        display: block;
        transform-origin: top left;
    }

    </style>
    <?php
}, 22 );

// Featured products section removed — was breaking homepage layout

// Homepage products CSS removed

// ============================================================
// Performance: Hide PHP version header
// ============================================================
add_filter( 'wp_headers', function( $headers ) {
    unset( $headers['X-Powered-By'] );
    return $headers;
} );
header_remove( 'X-Powered-By' );

// ============================================================
// Performance: Only load CF7 JS/CSS on pages with forms
// ============================================================
add_action( 'wp_enqueue_scripts', function() {
    if ( ! is_page( array( 'contact', 'contact-us', 'trade-account' ) ) ) {
        wp_dequeue_script( 'contact-form-7' );
        wp_dequeue_style( 'contact-form-7' );
    }
}, 100 );

// ============================================================
// Performance: Only load Worldpay JS on checkout
// ============================================================
add_action( 'wp_enqueue_scripts', function() {
    if ( ! is_checkout() && ! is_cart() ) {
        wp_dequeue_script( 'worldpay-checkout' );
        wp_dequeue_script( 'worldpay-sdk' );
        wp_dequeue_style( 'worldpay-checkout' );
    }
}, 100 );

// Fix department sidebar icon black boxes on homepage
add_action( 'wp_head', function() {
    if ( ! is_front_page() && ! is_home() ) return;
    ?>
    <style>
    /* Fix department sidebar icon dark backgrounds */
    .elementor-element-ea2c0ec .icon::before {
        display: none !important;
    }
    .menu-icon.img, .menu-icon.img.lazyloaded {
        background-color: transparent !important;
    }
    /* Hide the "Features products" heading and empty product widget */
    body.home .elementor-widget-et_products {
        display: none !important;
    }
    body.home .elementor-element-320ce91,
    body.home .elementor-element-8555cc5 {
        display: none !important;
    }
    </style>
    <?php
}, 20 );


if ( ! function_exists( 'mvp_category_icon_file' ) ) {
/**
 * Resolve a product_cat name to an icon file basename in /uploads/categories/.
 * Returns '' if none found. Exact current-convention match is tried FIRST, so any
 * card that already resolves keeps identical behaviour; the rest are fallbacks only.
 * Added 2026-07-06 (blank category-card fix). Safe to revert: delete this function
 * and this session's git commit restores the prior inline resolvers.
 */
function mvp_category_icon_file( $name ) {
    static $norm_index = null;
    $dir = WP_CONTENT_DIR . '/uploads/categories/';
    $d   = html_entity_decode( $name, ENT_QUOTES, 'UTF-8' );
    // 1) exact current convention (entity-decoded name, spaces -> underscore)
    $try = str_replace( ' ', '_', $d ) . '.png';
    if ( is_file( $dir . $try ) ) return $try;
    // 2) & -> and
    $try_and = str_replace( '&', 'and', $try );
    if ( is_file( $dir . $try_and ) ) return $try_and;
    // 3) filesystem-sanitised (slash/backslash -> underscore) - fixes names with "/"
    $san = str_replace( array( ' ', '/', '\\' ), '_', $d ) . '.png';
    if ( $san !== $try && is_file( $dir . $san ) ) return $san;
    // 4) normalised alnum index (largest real file wins), built once per request
    if ( $norm_index === null ) {
        $norm_index = array();
        foreach ( (array) glob( $dir . '*.png' ) as $gf ) {
            $sz = @filesize( $gf );
            if ( $sz === false || $sz <= 1000 ) continue;
            if ( ! mb_check_encoding( $gf, 'UTF-8' ) ) continue; // skip corrupt-byte filenames that break URLs
            $b = preg_replace( '/_[A-Za-z0-9]{7}$/', '', basename( $gf, '.png' ) );
            $k = preg_replace( '/[^a-z0-9]/', '', strtolower( html_entity_decode( $b, ENT_QUOTES, 'UTF-8' ) ) );
            if ( $k === '' ) continue;
            if ( ! isset( $norm_index[ $k ] ) || $sz > (int) $norm_index[ $k ]['s'] ) {
                $norm_index[ $k ] = array( 'f' => basename( $gf ), 's' => $sz );
            }
        }
    }
    $key = preg_replace( '/[^a-z0-9]/', '', strtolower( $d ) );
    if ( $key !== '' && isset( $norm_index[ $key ] ) ) return $norm_index[ $key ]['f'];
    return '';
}

// ============================================================
// Custom Product Meta Fields
// ============================================================

/**
 * Add custom tab for Maxus product data in WooCommerce product editor
 */
add_filter( 'woocommerce_product_data_tabs', 'mvp_add_custom_product_data_tab' );
function mvp_add_custom_product_data_tab( $tabs ) {
    $tabs['mvp_custom_data'] = array(
        'label'    => __( 'Maxus Data', 'woocommerce' ),
        'target'   => 'mvp_custom_product_data',
        'class'    => array(),
        'priority' => 60,
    );
    return $tabs;
}

/**
 * Add custom fields to the Maxus Data tab
 */
add_action( 'woocommerce_product_data_panels', 'mvp_add_custom_product_data_fields' );
function mvp_add_custom_product_data_fields() {
    global $post;
    ?>
    <div id="mvp_custom_product_data" class="panel woocommerce_options_panel">
        <?php
        // Callout Number field
        woocommerce_wp_text_input( array(
            'id'          => 'callout_number',
            'label'       => __( 'Callout Number', 'woocommerce' ),
            'placeholder' => '',
            'desc_tip'    => true,
            'description' => __( 'Product callout number for identification.', 'woocommerce' ),
        ) );
        
        // Original SKU field
        woocommerce_wp_text_input( array(
            'id'          => 'original_sku',
            'label'       => __( 'Original SKU', 'woocommerce' ),
            'placeholder' => '',
            'desc_tip'    => true,
            'description' => __( 'Original SKU/part number (Oscar part number).', 'woocommerce' ),
        ) );
        
        // Replacement Available checkbox
        woocommerce_wp_checkbox( array(
            'id'          => 'replacement_avail',
            'label'       => __( 'Replacement Available', 'woocommerce' ),
            'description' => __( 'Check if a replacement product is available.', 'woocommerce' ),
        ) );
        
        // Replacement SKU field
        woocommerce_wp_text_input( array(
            'id'          => 'replacement_sku',
            'label'       => __( 'Replacement SKU', 'woocommerce' ),
            'placeholder' => '',
            'desc_tip'    => true,
            'description' => __( 'Replacement product SKU/part number.', 'woocommerce' ),
        ) );
        
        // Date Updated field
        woocommerce_wp_text_input( array(
            'id'          => 'date_updated',
            'label'       => __( 'Date Updated', 'woocommerce' ),
            'placeholder' => 'YYYY-MM-DD',
            'desc_tip'    => true,
            'description' => __( 'Date when product data was last updated (YYYY-MM-DD format).', 'woocommerce' ),
            'type'        => 'date',
        ) );
        ?>
    </div>
    <?php
}

/**
 * Save custom product meta fields
 */
add_action( 'woocommerce_process_product_meta', 'mvp_save_custom_product_data_fields' );
function mvp_save_custom_product_data_fields( $post_id ) {
    // Callout Number
    $callout_number = isset( $_POST['callout_number'] ) ? sanitize_text_field( $_POST['callout_number'] ) : '';
    update_post_meta( $post_id, 'callout_number', $callout_number );
    
    // Original SKU
    $original_sku = isset( $_POST['original_sku'] ) ? sanitize_text_field( $_POST['original_sku'] ) : '';
    update_post_meta( $post_id, 'original_sku', $original_sku );
    
    // Replacement Available (checkbox)
    $replacement_avail = isset( $_POST['replacement_avail'] ) ? 'yes' : 'no';
    update_post_meta( $post_id, 'replacement_avail', $replacement_avail );
    
    // Replacement SKU
    $replacement_sku = isset( $_POST['replacement_sku'] ) ? sanitize_text_field( $_POST['replacement_sku'] ) : '';
    update_post_meta( $post_id, 'replacement_sku', $replacement_sku );
    
    // Date Updated
    $date_updated = isset( $_POST['date_updated'] ) ? sanitize_text_field( $_POST['date_updated'] ) : '';
    update_post_meta( $post_id, 'date_updated', $date_updated );
}
}
