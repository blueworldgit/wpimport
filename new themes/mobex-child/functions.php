<?php

function mobex_enovathemes_child_scripts() {
    wp_enqueue_style( 'mobex_enovathemes-parent-style', get_template_directory_uri(). '/style.css' );
}
add_action( 'wp_enqueue_scripts', 'mobex_enovathemes_child_scripts' );

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
 * Maxus Van Parts — Homepage Facelift
 *
 * Transforms shane.maxusvanparts.co.uk homepage to match
 * the maxusvanparts.acstestweb.co.uk design.
 *
 * Approach: CSS hides unwanted Elementor sections, JS injects
 * hero banner + vehicle carousel into correct DOM position.
 */

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
        display: none !important;
    }

    /* ── Hero Banner ── */
    .mvp-hero {
        position: relative;
        width: 100%;
        height: 348px;
        background-image: url('https://maxusvanparts.acstestweb.co.uk/wp-content/uploads/resized.jpg');
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
        max-width: 700px;
        padding: 40px 120px;
        text-align: left;
    }
    .mvp-hero-content h1 {
        font-family: 'Oswald', sans-serif;
        font-size: 72px;
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
        font-size: 40px;
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
        .mvp-hero-content h1 { font-size: 42px; }
        .mvp-hero-content h1 .hero-sub { font-size: 26px; }
        .mvp-hero-content p { font-size: 15px; margin: 12px 0 18px; }
        .mvp-hero-btn { padding: 10px 24px; font-size: 13px; }
    }
    @media (max-width: 480px) {
        .mvp-hero { height: 220px; }
        .mvp-hero-content { padding: 20px 20px; }
        .mvp-hero-content h1 { font-size: 28px; }
        .mvp-hero-content h1 .hero-sub { font-size: 18px; }
        .mvp-hero-content p { font-size: 13px; margin: 8px 0 12px; }
    }

    /* ── Vehicle Carousel ── */
    .mvp-vehicles {
        background: #fff;
        padding: 25px 0 20px;
        text-align: center;
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
        flex: 0 0 110px;
        text-align: center;
        text-decoration: none;
        color: #333;
        padding: 5px;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .mvp-vehicle-card:hover { transform: translateY(-3px); }
    .mvp-vehicle-circle {
        width: 90px;
        height: 90px;
        border-radius: 50%;
        border: 3px solid #ddd;
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
        border-color: #e74c3c;
        box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3);
    }
    .mvp-vehicle-card:hover .mvp-vehicle-name { color: #e74c3c; }
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
        .mvp-vehicle-card { flex: 0 0 85px; }
        .mvp-vehicle-circle { width: 65px; height: 65px; }
        .mvp-vehicle-name { font-size: 10px; }
        .mvp-carousel-nav { width: 24px; height: 30px; font-size: 20px; }
        .mvp-carousel-nav.prev { left: 10px; }
        .mvp-carousel-nav.next { right: 10px; }
    }

    /* ── Why Use Us ── */
    .mvp-why-us {
        background: #fff;
        padding: 20px 20px 25px;
        text-align: center;
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
        text-align: center;
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
        .mvp-footer-bottom-inner { flex-direction: column; text-align: center; padding: 14px 20px; }
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
    </style>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@700&display=swap" rel="stylesheet">
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
    $maxus_term_id = 3590; // Maxus parent category
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
        . '<a href="/shop/" class="mvp-hero-btn">Shop All Parts</a>'
        . '</div></div>';

    $carousel_html = '<section class="mvp-vehicles">'
        . '<div class="mvp-carousel-wrapper">'
        . '<button class="mvp-carousel-nav prev" onclick="document.querySelector(\'.mvp-carousel-track\').scrollBy({left:-220,behavior:\'smooth\'})">&#8249;</button>'
        . '<div class="mvp-carousel-track">' . $cards . '</div>'
        . '<button class="mvp-carousel-nav next" onclick="document.querySelector(\'.mvp-carousel-track\').scrollBy({left:220,behavior:\'smooth\'})">&#8250;</button>'
        . '</div></section>';

    $combined = json_encode( $hero_html . $carousel_html );
    ?>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        var target = document.querySelector('.elementor-11641');
        if (!target) return;
        var container = document.createElement('div');
        container.id = 'mvp-facelift-hero-area';
        container.innerHTML = <?php echo $combined; ?>;
        target.parentNode.insertBefore(container, target);
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
                <p>Every order checked and confirmed before shipping.</p>
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
    if ( ! is_front_page() && ! is_home() ) return;
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
                    <li><a href="/wishlist/">Wishlist</a></li>
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
                    <li><a href="/refund_returns/">Returns &amp; Exchanges</a></li>
                </ul>
            </div>
            <div class="mvp-footer-col">
                <h4>Vehicles</h4>
                <ul>
                    <li><a href="/shop/">E Deliver 3</a></li>
                    <li><a href="/shop/">E Deliver 7</a></li>
                    <li><a href="/shop/">E Deliver 9</a></li>
                    <li><a href="/shop/">T90 EV</a></li>
                </ul>
            </div>
            <div class="mvp-footer-col">
                <h4>Customer Service</h4>
                <ul>
                    <li><a href="/my-account/">Login</a></li>
                    <li><a href="/my-account/">Register</a></li>
                    <li><a href="/my-account/orders/">Order History</a></li>
                    <li><a href="/shipping-info/">Shipping Info</a></li>
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
    $maxus_term_id = 3590;
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
        'model'        => get_term_meta( $vin_term->term_id, 'vehicle_model', true ),
        'year'         => get_term_meta( $vin_term->term_id, 'vehicle_year', true ),
        'img'          => get_term_meta( $vin_term->term_id, 'vehicle_image', true ),
        'categories'   => get_terms( array(
            'taxonomy'   => 'product_cat',
            'parent'     => $vin_term->term_id,
            'hide_empty' => true,
            'orderby'    => 'name',
        ) ),
        'cat_img_base' => 'https://maxusvanparts.acstestweb.co.uk/wp-content/uploads/categories/',
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
        border: 3px solid #ddd;
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
        text-align: center;
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
        .mvp-vehicle-header { flex-direction: column; text-align: center; gap: 16px; }
        .mvp-vehicle-header-img { width: 90px; height: 90px; }
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
                $cat_img_name = str_replace( ' ', '_', $cat->name ) . '.png';
                $cat_img_url  = $cat_img_base . $cat_img_name;
                // Link to department page (shows all vehicles with this category)
                $cat_url = home_url( '/department/' . sanitize_title( $cat->name ) . '/' );
                // Count products (including subcategories)
                $product_count = $cat->count;
                // Also count products in child categories
                $subcats = get_terms( array(
                    'taxonomy'   => 'product_cat',
                    'parent'     => $cat->term_id,
                    'hide_empty' => true,
                ) );
                if ( ! is_wp_error( $subcats ) ) {
                    foreach ( $subcats as $subcat ) {
                        $product_count += $subcat->count;
                    }
                }
            ?>
            <a href="<?php echo esc_url( $cat_url ); ?>" class="mvp-category-card">
                <div class="mvp-category-card-img">
                    <img src="<?php echo esc_url( $cat_img_url ); ?>" alt="<?php echo esc_attr( $cat->name ); ?>" loading="lazy"
                         onerror="this.style.display='none'">
                </div>
                <div class="mvp-category-card-body">
                    <h3><?php echo esc_html( $cat->name ); ?></h3>
                    <span class="mvp-cat-count"><?php echo $product_count; ?> part<?php echo $product_count !== 1 ? 's' : ''; ?></span>
                </div>
            </a>
            <?php endforeach; ?>
        </div>
        <?php else : ?>
        <p style="text-align:center;color:#888;padding:40px 0;">No parts categories found for this vehicle yet.</p>
        <?php endif; ?>
    </div>
    <?php
    get_footer();
}

// ============================================================
// 5b. DEPARTMENT PAGES — /department/{slug}/ and /department/{slug}/{vehicle-slug}/
// ============================================================

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

    $vehicle_slug = get_query_var( 'mvp_dept_vehicle' );

    // If vehicle slug present, redirect to the WooCommerce category for that vehicle's department
    if ( $vehicle_slug ) {
        mvp_department_vehicle_redirect( $dept_slug, $vehicle_slug );
        return;
    }

    // Show department page with all vehicles that have this category
    global $wp_query;
    $wp_query->is_404 = false;
    status_header( 200 );

    mvp_department_render_page( $dept_slug );
    exit;
}

// Redirect /department/{cat}/{vehicle}/ to the WooCommerce category page
function mvp_department_vehicle_redirect( $dept_slug, $vehicle_slug ) {
    $maxus_term_id = 3590;

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

    // Find the child category matching department name
    $child_cats = get_terms( array(
        'taxonomy' => 'product_cat',
        'parent'   => $vin_term->term_id,
        'hide_empty' => true,
    ) );

    $dept_name_clean = str_replace( '-', ' ', $dept_slug );
    $target_cat = null;

    if ( ! is_wp_error( $child_cats ) ) {
        foreach ( $child_cats as $cat ) {
            $cat_name_clean = strtolower( str_replace( array( ' ', '_' ), '-', $cat->name ) );
            if ( sanitize_title( $cat->name ) === sanitize_title( $dept_name_clean ) ||
                 $cat_name_clean === $dept_slug ||
                 sanitize_title( $cat->name ) === $dept_slug ) {
                $target_cat = $cat;
                break;
            }
        }
    }

    if ( $target_cat ) {
        $url = get_term_link( $target_cat );
        if ( ! is_wp_error( $url ) ) {
            wp_redirect( $url, 301 );
            exit;
        }
    }

    // Fallback: redirect to vehicle page
    wp_redirect( home_url( '/vehicle/' . $vehicle_slug . '/' ), 302 );
    exit;
}

// Render the department page showing all vehicles with this category
function mvp_department_render_page( $dept_slug ) {
    $maxus_term_id = 3590;
    $dept_name_clean = str_replace( '-', ' ', $dept_slug );

    // Get all VIN terms
    $vin_terms = get_terms( array(
        'taxonomy'   => 'product_cat',
        'parent'     => $maxus_term_id,
        'hide_empty' => false,
        'orderby'    => 'name',
    ) );

    // Find which VINs have this category as a child
    $vehicles_with_dept = array();
    $dept_display_name = '';
    $cat_img_base = 'https://maxusvanparts.acstestweb.co.uk/wp-content/uploads/categories/';

    if ( ! is_wp_error( $vin_terms ) ) {
        foreach ( $vin_terms as $vin_term ) {
            $model = get_term_meta( $vin_term->term_id, 'vehicle_model', true );
            $slug  = get_term_meta( $vin_term->term_id, 'vehicle_slug', true );
            if ( ! $model || ! $slug ) continue;

            // Check child categories for matching department
            $child_cats = get_terms( array(
                'taxonomy' => 'product_cat',
                'parent'   => $vin_term->term_id,
                'hide_empty' => true,
            ) );

            if ( is_wp_error( $child_cats ) ) continue;

            foreach ( $child_cats as $cat ) {
                if ( sanitize_title( $cat->name ) === sanitize_title( $dept_name_clean ) ||
                     sanitize_title( $cat->name ) === $dept_slug ) {
                    if ( ! $dept_display_name ) $dept_display_name = $cat->name;

                    // Count products including subcategories
                    $product_count = $cat->count;
                    $subcats = get_terms( array(
                        'taxonomy' => 'product_cat',
                        'parent'   => $cat->term_id,
                        'hide_empty' => true,
                    ) );
                    if ( ! is_wp_error( $subcats ) ) {
                        foreach ( $subcats as $sc ) $product_count += $sc->count;
                    }

                    $year  = get_term_meta( $vin_term->term_id, 'vehicle_year', true );
                    $img   = get_term_meta( $vin_term->term_id, 'vehicle_image', true );

                    $vehicles_with_dept[] = array(
                        'model'         => $model,
                        'year'          => $year,
                        'img'           => $img,
                        'vehicle_slug'  => $slug,
                        'cat_term'      => $cat,
                        'product_count' => $product_count,
                    );
                    break;
                }
            }
        }
    }

    if ( empty( $dept_display_name ) ) {
        $dept_display_name = ucwords( $dept_name_clean );
    }

    // Category image
    $cat_img_name = str_replace( ' ', '_', $dept_display_name ) . '.png';
    $cat_img_url  = $cat_img_base . $cat_img_name;

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
        .mvp-dept-header { flex-direction: column; text-align: center; gap: 16px; }
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
            <div class="mvp-dept-header-img">
                <img src="<?php echo esc_url( $cat_img_url ); ?>" alt="<?php echo esc_attr( $dept_display_name ); ?>"
                     onerror="this.style.display='none'">
            </div>
            <div class="mvp-dept-header-info">
                <p class="mvp-dept-breadcrumb"><a href="<?php echo home_url('/'); ?>">Home</a> &rsaquo; <?php echo esc_html( $dept_display_name ); ?></p>
                <h1><?php echo esc_html( $dept_display_name ); ?></h1>
                <p class="mvp-dept-subtitle">Select your vehicle to view <?php echo esc_html( strtolower( $dept_display_name ) ); ?> parts</p>
            </div>
        </div>

        <?php if ( ! empty( $vehicles_with_dept ) ) : ?>
        <div class="mvp-dept-vehicle-grid">
            <?php foreach ( $vehicles_with_dept as $v ) :
                $cat_url = get_term_link( $v['cat_term'] );
                if ( is_wp_error( $cat_url ) ) $cat_url = home_url( '/vehicle/' . $v['vehicle_slug'] . '/' );
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
    $maxus_term_id = 3590;
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
    $best_slug = '';
    $best_name = '';
    $model_upper = strtoupper( $model_name );

    foreach ( $vehicles as $slug => $v ) {
        $v_name = strtoupper( $v['name'] );

        // Direct match
        if ( stripos( $model_upper, $v_name ) !== false || stripos( $v_name, $model_upper ) !== false ) {
            $best_slug = $slug;
            $best_name = $v['name'];
            break;
        }

        // Keyword matching
        $keywords = array( 'DELIVER 9', 'DELIVER 7', 'E DELIVER 9', 'E DELIVER 7', 'E DELIVER 3', 'E-DELIVER', 'T60', 'T90', 'V80', 'A80' );
        foreach ( $keywords as $kw ) {
            if ( stripos( $model_upper, $kw ) !== false && stripos( $v_name, $kw ) !== false ) {
                $is_electric = ( stripos( $fuel, 'ELECTRIC' ) !== false );
                $v_is_electric = ( stripos( $v_name, 'E DELIVER' ) !== false || stripos( $v_name, 'EV' ) !== false );
                if ( $is_electric === $v_is_electric ) {
                    $best_slug = $slug;
                    $best_name = $v['name'];
                    break 2;
                }
                if ( empty( $best_slug ) ) {
                    $best_slug = $slug;
                    $best_name = $v['name'];
                }
            }
        }
    }

    $display_name = ucwords( strtolower( $make . ' ' . $model_name ) );

    if ( ! empty( $best_slug ) ) {
        wp_send_json_success( array(
            'vehicle_name'  => $display_name,
            'customer_year' => $year,
            'shop_url'      => $home_url . 'vehicle/' . $best_slug . '/',
        ) );
    } else {
        wp_send_json_success( array(
            'vehicle_name'  => $display_name,
            'customer_year' => $year,
            'shop_url'      => $home_url . 'shop/',
            'note'          => 'Could not match exact model. Showing all parts.',
        ) );
    }
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
                    if (data.success && data.data.shop_url) {
                        vinResult.className = 'mvp-lp-result show success';
                        vinResult.innerHTML = '<strong>' + data.data.vehicle_name + ' (' + data.data.customer_year + ')</strong> — Redirecting...';
                        window.location.href = data.data.shop_url;
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
                    if (data.success && data.data.shop_url) {
                        regResult.className = 'mvp-lp-result show success';
                        regResult.innerHTML = '<strong>' + data.data.vehicle_name + ' (' + data.data.customer_year + ')</strong> — Redirecting...';
                        window.location.href = data.data.shop_url;
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
    $maxus_term_id = 3590;
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
        display: flex; flex-wrap: nowrap; align-items: center; gap: 10px;
        padding: 12px 20px;
        background: var(--e-global-color-secondary, #F29F05);
        border-radius: 6px; position: relative;
    }
    .mvp-search-bar .mvp-sb-select {
        height: 36px; padding: 0 28px 0 10px; font-size: 13px; font-family: inherit;
        border: none; border-radius: 4px; outline: none; color: #333; background: #fff;
        cursor: pointer; min-width: 0;
        -webkit-appearance: none; -moz-appearance: none; appearance: none;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%23999'/%3E%3C/svg%3E");
        background-repeat: no-repeat; background-position: right 10px center;
    }
    .mvp-search-bar .mvp-sb-model { min-width: 208px; flex-shrink: 1; }
    .mvp-search-bar .mvp-sb-year { min-width: 120px; flex-shrink: 1; }
    .mvp-search-bar .mvp-sb-or {
        white-space: nowrap; font-weight: 700; font-size: 12px;
        text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.85;
        color: #fff; padding: 0 2px; flex-shrink: 0;
    }
    .mvp-search-bar .mvp-sb-input {
        height: 36px; padding: 0 10px; font-size: 13px; font-family: inherit;
        border: none; border-radius: 4px; outline: none; color: #333; background: #fff;
        box-sizing: border-box; width: 180px; min-width: 120px; flex-shrink: 1;
    }
    .mvp-search-bar .mvp-sb-input::placeholder { color: #999; font-size: 13px; }
    .mvp-search-bar .mvp-sb-submit {
        height: 36px; padding: 0 20px; font-size: 13px; font-weight: 600;
        font-family: inherit; line-height: 36px; white-space: nowrap; flex-shrink: 0;
        border: none; border-radius: 4px; background: #BF3617; color: #fff;
        cursor: pointer; text-transform: uppercase; letter-spacing: 0.5px; transition: background 0.2s;
    }
    .mvp-search-bar .mvp-sb-submit:hover { background: #a02e13; }
    .mvp-search-bar .mvp-sb-reset {
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
        color: #fff; font-weight: 600; font-size: 14px; text-align: center;
        padding: 12px 20px; border-radius: 6px; cursor: pointer;
    }
    @media (max-width: 960px) {
        .mvp-search-bar { flex-wrap: wrap; gap: 8px; padding: 12px 16px; }
        .mvp-search-bar .mvp-sb-model, .mvp-search-bar .mvp-sb-year { min-width: 0; flex: 1 1 45%; }
        .mvp-search-bar .mvp-sb-input { width: auto; flex: 1 1 40%; }
    }
    @media (max-width: 600px) {
        .mvp-sb-mobile-toggle { display: block; }
        .mvp-search-bar { display: none; flex-direction: column; }
        .mvp-search-bar.mvp-sb-open { display: flex; margin-top: 4px; border-radius: 0 0 6px 6px; }
        .mvp-sb-mobile-toggle.mvp-sb-open { border-radius: 6px 6px 0 0; margin-bottom: 0; }
        .mvp-search-bar .mvp-sb-model, .mvp-search-bar .mvp-sb-year,
        .mvp-search-bar .mvp-sb-input { width: 100% !important; min-width: 0; flex: 1 1 100%; }
        .mvp-search-bar .mvp-sb-submit { width: 100%; }
        .mvp-search-bar .mvp-sb-or { display: none; }
    }
    </style>
    <script>
    (function(){
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
                '<select class="mvp-sb-select mvp-sb-model">' + modelOpts + '</select>' +
                '<select class="mvp-sb-select mvp-sb-year" disabled><option value="">Year</option></select>' +
                '<span class="mvp-sb-or">OR</span>' +
                '<input type="text" class="mvp-sb-input mvp-sb-vin" placeholder="Search by VIN" maxlength="17" autocomplete="off">' +
                '<span class="mvp-sb-or">OR</span>' +
                '<input type="text" class="mvp-sb-input mvp-sb-reg" placeholder="Search by Registration" maxlength="10" autocomplete="off">' +
                '<button type="button" class="mvp-sb-submit">Search</button>' +
                '<span class="mvp-sb-reset">Reset</span>' +
                '<div class="mvp-sb-result"></div>' +
            '</div></div>';

        // Inject into the filter container (631db85) or fallback after carousel
        var target = document.querySelector('.elementor-element-631db85');
        if (target) {
            target.insertAdjacentHTML('beforeend', barHtml);
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
                    if (data.success && data.data.shop_url) {
                        resultEl.className = 'mvp-sb-result show success';
                        resultEl.innerHTML = '<strong>' + (data.data.vehicle_name || 'Vehicle found') + '</strong> &mdash; Redirecting...';
                        window.location.href = data.data.shop_url;
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
                    if (data.success && data.data.shop_url) {
                        resultEl.className = 'mvp-sb-result show success';
                        resultEl.innerHTML = '<strong>' + data.data.vehicle_name + ' (' + data.data.customer_year + ')</strong> &mdash; Redirecting...';
                        window.location.href = data.data.shop_url;
                    } else { resultEl.className = 'mvp-sb-result show error'; resultEl.textContent = (data.data && data.data.error) || 'No match found'; }
                }).catch(function() { resultEl.className = 'mvp-sb-result show error'; resultEl.textContent = 'An error occurred. Please try again.'; });
        }
    })();
    </script>
    <?php
}
