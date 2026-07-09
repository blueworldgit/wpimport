<?php

/* Constantas
---------------*/

    define('MOBEX_ENOVATHEMES_TEMPPATH', get_template_directory_uri());
    define('MOBEX_ENOVATHEMES_IMAGES', MOBEX_ENOVATHEMES_TEMPPATH. "/images");
    define('MOBEX_SVG', MOBEX_ENOVATHEMES_IMAGES."/icons/");
    define('ICL_DONT_LOAD_NAVIGATION_CSS', true);
    define('ICL_DONT_LOAD_LANGUAGE_SELECTOR_CSS', true);

/* Includes
---------------*/

    require_once(get_template_directory() . '/includes/menu/custom-menu.php' );
    require_once(get_template_directory() . '/includes/enovathemes-functions.php');

/* TGM
---------------*/

    if (!class_exists('TGM_Plugin_Activation') && file_exists( get_template_directory() . '/includes/class-tgm-plugin-activation.php' ) ) {
        require_once(get_template_directory() . '/includes/class-tgm-plugin-activation.php');
    }

    if (class_exists('OCDI_Plugin')) {

        add_filter( 'pt-ocdi/disable_pt_branding', '__return_true' );
        add_filter( 'pt-ocdi/regenerate_thumbnails_in_content_import', '__return_false' );

        function mobex_enovathemes_intro_text( $default_text ) {
            $default_text = '<div class="ocdi__intro-text custom-intro-text">
            <h2 class="about-description">
            '.esc_html__( "Importing demo data (post, pages, images, theme settings, ...) is the easiest way to setup your theme.", "mobex" ).'
            '.esc_html__( "It will allow you to quickly edit everything instead of creating content from scratch.", "mobex" ).'
            </h2>
            <hr>
            <h3>'.esc_html__( "Important things to know before starting demo import", "mobex" ).'</h3>
            <ul>
            <li>'.esc_html__( "No existing posts, pages, categories, images, custom post types or any other data will be deleted or modified.", "mobex" ).'</li>
            <li>'.esc_html__( "Posts, pages, images, widgets, menus and other theme settings will get imported.", "mobex" ).'</li>
            <li>'.esc_html__( "Please click on the Import button only once and wait, it can take a couple of minutes.", "mobex" ).'</li>
            <li>'.esc_html__( "If you want to change the homepage version after import, do not import another demo, go to WordPress settings >> Reading and choose different homepage version as your front-page.", "mobex" ).'</li>
            <li>'.esc_html__( "If you want to import pages/posts/custom post type/menu etc. separately use regular WordPress importer", "mobex" ).'</li>
            <li>'.esc_html__( "Sometimes not all widgets are displayed after the import, this is known issue, you will need to replace these plugins or re-save one more time", "mobex" ).'</li>
            </ul>
            <hr>
            <h3>'.esc_html__( "What to do after import", "mobex" ).'</h3>
            <ul>
            <li>'.esc_html__( "All the images will be imported with original sizes without cropping. This way your import process will be quicker and your server will have less work to do. After the import completed go to the WordPress >> Tools and use the Regenerate thumbnails plugin to crop images to theme supported sizes. !!! Important, regenerate only Featured images", "mobex" ).'</li>
            <li>'.esc_html__( "Also re-save permalinks from default to whatever you want. (WordPress settings >> permalinks)", "mobex" ).'</li>
            </ul>
            <hr>
            <h3>'.esc_html__( "Troubleshooting", "mobex" ).'</h3><br>
            <p>'.esc_html__( "If you will have any issues with the import process, please update these option on your server (edit your php.ini file)", "mobex" ).' </p>
            <ul class="code">
            <li>'.esc_html__( "upload_max_filesize (256M)", "mobex" ).'</li>
            <li>'.esc_html__( "max_input_time (300)", "mobex" ).'</li>
            <li>'.esc_html__( "memory_limit (256M)", "mobex" ).'</li>
            <li>'.esc_html__( "max_execution_time (300)", "mobex" ).'</li>
            <li>'.esc_html__( "post_max_size (512M)", "mobex" ).'</li>
            </ul>
            <p>'.esc_html__( "These defaults are not perfect and it depends on how large of an import you are making. So the bigger the import, the higher the numbers should be.", "mobex" ).' </p>
            </div>';
            return $default_text;
        }
        add_filter( 'pt-ocdi/plugin_intro_text', 'mobex_enovathemes_intro_text' );

        function mobex_enovathemes_import_files() {

            return array(

                array(
                    'import_file_name'             => esc_html__('Full demo', 'mobex'),
                    'categories'                   => array( 'General' ),
                    'local_import_file'            => trailingslashit( get_template_directory() ) . 'demo/all.xml',
                    'local_import_widget_file'     => trailingslashit( get_template_directory() ) . 'demo/widgets.wie',
                    'local_import_customizer_file' => trailingslashit( get_template_directory() ) . 'demo/customizer.dat',
                    'import_notice' => esc_html__( 'Import process can take up to 10 minutes, so please be patient and do not interrupt the import process', 'mobex' ),
                ),

            );
        }
        add_filter( 'pt-ocdi/import_files', 'mobex_enovathemes_import_files' );

    }

    add_action( 'tgmpa_register', 'mobex_enovathemes_register_required_plugins' );
    function mobex_enovathemes_register_required_plugins() {

        $plugins = array(

            array(
                'name'      => esc_html__('Elementor Website Builder', 'mobex'),
                'slug'      => 'elementor',
            ),
            array(
                'name'      => esc_html__('Contact Form 7', 'mobex'),
                'slug'      => 'contact-form-7',
            ),
            array(
                'name'      => esc_html__('Safe SVG', 'mobex'),
                'slug'      => 'safe-svg',
            ),
            array(
                'name'      => esc_html__('One Click Demo Import', 'mobex'),
                'slug'      => 'one-click-demo-import',
            ),
            array(
                'name'      => esc_html__('Envato market master', 'mobex'),
                'slug'      => 'envato-market',
                'source'    => get_template_directory() . '/plugins/envato-market.zip',
            ),
            array(
                'name'      => esc_html__('Revolution slider', 'mobex'),
                'slug'      => 'revslider',
                'source'    => get_template_directory() . '/plugins/revslider.zip',
                'version'   => '6.7.37'
            ),
            array(
                'name'      => esc_html__('Enovathemes add-ons', 'mobex'),
                'slug'      => 'enovathemes-addons',
                'source'    => get_template_directory() . '/plugins/enovathemes-addons.zip',
                'required'  => true,
                'version'   => '3.3'
            ),
            array(
                'name'      => esc_html__('Regenerate Thumbnails', 'mobex'),
                'slug'      => 'regenerate-thumbnails',
                'required'  => true,
                'dismissable' => true
            ),
            array(
                'name'      => esc_html__('WooCommerce', 'mobex'),
                'slug'      => 'woocommerce',
                'required'  => true,
                'dismissable' => true
            ),

        );

        if (class_exists('Woocommerce')) {
            $plugins[] = array(
                'name'      => esc_html__('YayCurrency – WooCommerce Multi-Currency Switcher', 'mobex'),
                'slug'      => 'yaycurrency',
            );
        }

        $config = array(
            'id'                => 'mobex',
            'default_path'      => '',                          // Default absolute path to pre-packaged plugins
            'parent_slug'       => 'themes.php',                // Default parent menu slug
            'capability'        => 'edit_theme_options',
            'menu'              => 'install-required-plugins',  // Menu slug
            'has_notices'       => true,                        // Show admin notices or not
            'dismissable'       => true,
            'is_automatic'      => false,                       // Automatically activate plugins after installation or not
            'message'           => '',                          // Message to output right before the plugins table
            'strings'           => array(
                'page_title'                                => esc_html__( 'Install Required Plugins', 'mobex' ),
                'menu_title'                                => esc_html__( 'Install Plugins', 'mobex' ),
                'installing'                                => esc_html__( 'Installing Plugin: %s', 'mobex' ), // %1$s = plugin name
                'oops'                                      => esc_html__( 'Something went wrong with the plugin API.', 'mobex' ),
                'notice_can_install_required'               => _n_noop( 'This theme requires the following plugin: %1$s.', 'This theme requires the following plugins: %1$s.', 'mobex' ), // %1$s = plugin name(s)
                'notice_can_install_recommended'            => _n_noop( 'This theme recommends the following plugin: %1$s.', 'This theme recommends the following plugins: %1$s.', 'mobex' ), // %1$s = plugin name(s)
                'notice_cannot_install'                     => _n_noop( 'Sorry, but you do not have the correct permissions to install the %s plugin. Contact the administrator of this site for help on getting the plugin installed.', 'Sorry, but you do not have the correct permissions to install the %s plugins. Contact the administrator of this site for help on getting the plugins installed.', 'mobex' ), // %1$s = plugin name(s)
                'notice_can_activate_required'              => _n_noop( 'The following required plugin is currently inactive: %1$s.', 'The following required plugins are currently inactive: %1$s.', 'mobex' ), // %1$s = plugin name(s)
                'notice_can_activate_recommended'           => _n_noop( 'The following recommended plugin is currently inactive: %1$s.', 'The following recommended plugins are currently inactive: %1$s.', 'mobex' ), // %1$s = plugin name(s)
                'notice_cannot_activate'                    => _n_noop( 'Sorry, but you do not have the correct permissions to activate the %s plugin. Contact the administrator of this site for help on getting the plugin activated.', 'Sorry, but you do not have the correct permissions to activate the %s plugins. Contact the administrator of this site for help on getting the plugins activated.', 'mobex' ), // %1$s = plugin name(s)
                'notice_ask_to_update'                      => _n_noop( 'The following plugin needs to be updated to its latest version to ensure maximum compatibility with this theme: %1$s.', 'The following plugins need to be updated to their latest version to ensure maximum compatibility with this theme: %1$s.', 'mobex' ), // %1$s = plugin name(s)
                'notice_cannot_update'                      => _n_noop( 'Sorry, but you do not have the correct permissions to update the %s plugin. Contact the administrator of this site for help on getting the plugin updated.', 'Sorry, but you do not have the correct permissions to update the %s plugins. Contact the administrator of this site for help on getting the plugins updated.', 'mobex' ), // %1$s = plugin name(s)
                'install_link'                              => _n_noop( 'Begin installing plugin', 'Begin installing plugins', 'mobex' ),
                'activate_link'                             => _n_noop( 'Activate installed plugin', 'Activate installed plugins', 'mobex' ),
                'return'                                    => esc_html__( 'Return to Required Plugins Installer', 'mobex' ),
                'plugin_activated'                          => esc_html__( 'Plugin activated successfully.', 'mobex' ),
                'complete'                                  => esc_html__( 'All plugins installed and activated successfully. %s', 'mobex' ), // %1$s = dashboard link
                'nag_type'                                  => 'updated' // Determines admin notice type - can only be 'updated' or 'error'
            )
        );

        tgmpa( $plugins, $config );

    }

/* Theme Config
---------------*/

    add_action('after_setup_theme', 'mobex_enovathemes_after_setup_theme');
    function mobex_enovathemes_after_setup_theme() {

        function mobex_enovathemes_pingback_header() {
            if ( is_singular() && pings_open() ) {
                echo '<link rel="pingback" href="', esc_url( get_bloginfo( 'pingback_url' ) ), '">';
            }
        }
        add_action( 'wp_head', 'mobex_enovathemes_pingback_header' );

        if ( function_exists( 'add_theme_support' ) ) {
            add_image_size( 'lazy_img', 16, 16, false );
            add_image_size( 'post_img', 1320, 560, true );
        }

        if ( ! function_exists( 'mobex_enovathemes_thumbnail_sizes' ) ) {
            function mobex_enovathemes_thumbnail_sizes() {
                update_option( 'thumbnail_size_w', 150 );
                update_option( 'thumbnail_size_h', 150 );

                update_option( 'medium_size_w', 660 );
                update_option( 'medium_size_h', 440 );

                update_option( 'large_size_w', 1320 );
                update_option( 'large_size_h', 800 );
            }
            add_action( 'after_switch_theme', 'mobex_enovathemes_thumbnail_sizes' );
        }

        add_theme_support('rtl');
        add_theme_support( 'post-thumbnails');
        add_theme_support( 'html5', array( 'gallery', 'caption' ) );
        add_theme_support( 'post-formats', array('video','gallery') );
        add_theme_support( 'automatic-feed-links' );
        add_post_type_support( 'post', 'post-formats' );
        add_post_type_support( 'page', 'excerpt' );
        add_theme_support( 'align-wide' );
        add_theme_support( 'responsive-embeds' );

        load_theme_textdomain('mobex', get_template_directory() . '/languages');
        add_theme_support( 'woocommerce' );
        add_theme_support( 'title-tag' );

        if ( ! isset( $content_width ) ) {$content_width = 1320;}

    }

    function mobex_enovathemes_customize_save_after( $array ) { 
        delete_transient( 'dynamic-styles-cached' );
    }; 
    add_action( 'customize_save_after', 'mobex_enovathemes_customize_save_after', 10, 1 ); 

    add_filter('body_class', 'mobex_enovathemes_general_body_classes');
    function mobex_enovathemes_general_body_classes($classes) {

            $modes               = et_get_theme_mods();
            $footer              = get_theme_mod('footer');
            $instagram           = (!empty(get_theme_mod('instagram'))) ? 'light' : '';
            $shop_sidebar_toggle = (get_theme_mod('shop_sidebar_toggle') != null && !empty(get_theme_mod('shop_sidebar_toggle'))) ? true : false;
        
            $data_shop  = (isset($_GET["data_shop"]) && !empty($_GET["data_shop"])) ? $_GET["data_shop"] : "default";
            if($data_shop == 'toggle'){
                $shop_sidebar_toggle = true;
            }

            $custom_class = array();
            $custom_class[] = "enovathemes";

            $layout = isset($modes['layout']) ? $modes['layout'] : 'wide';

            if ($layout == "boxed") {
                $custom_class[] = "layout-boxed";
            }

            if (!empty($instagram)) {
                $custom_class[] = "light";
            }

            if ($shop_sidebar_toggle) {
                $custom_class[] = "product-sidebar-toggle-true";
            }

            if ($footer == "default" || empty($footer)) {
                $custom_class[] = "default-footer";
            }

            if (class_exists('Woocommerce')){
                
                if (is_cart() || is_checkout()) {$custom_class[] = "cart-checkout";}
                if (is_account_page()) {$custom_class[] = "my-account";}

                if (is_shop() || is_tax('product_cat') || is_tax('product_tag')) {
                    $custom_class[] = "shop";
                }

                $woocommerce_shop_page_display = get_option( 'woocommerce_shop_page_display' );

                if ($woocommerce_shop_page_display === '') {
                    $custom_class[] = "woocommerce-layout-product";
                } elseif ($woocommerce_shop_page_display === 'subcategories') {
                    $custom_class[] = "woocommerce-layout-category";
                } elseif($woocommerce_shop_page_display === 'both') {
                    $custom_class[] = "woocommerce-layout-both";
                }

            }

            $custom_class[] = (!defined('ENOVATHEMES_ADDONS')) ? 'addon-off' : 'addon-on';

            $shop_sidebar = get_theme_mod('shop_sidebar');
            if (is_active_sidebar('shop-widgets') && empty($shop_sidebar) && !defined('ENOVATHEMES_ADDONS')) {
                $shop_sidebar = 'true';
            }

            if (class_exists('Woocommerce') && (is_shop() || is_tax('product_cat') || is_tax('product_tag')) && !empty($shop_sidebar)){
                $custom_class[] = "filter-active";
            }
            

            $classes[] = implode(" ", $custom_class);

            return $classes;
    }

/* Theme actions
/*-------------*/

    /* Fetch user info
    ---------------*/

    // Get current user data
    function mobex_enovathemes_fetch_user_info() {
        if (is_user_logged_in()){

            $current_user = wp_get_current_user();
            $user         = ($current_user->user_firstname) ? $current_user->user_firstname : $current_user->display_name;
            $email        = $current_user->user_email;

            echo json_encode(array('user' => $user,'email' => $email));
        }
        die();
    }
    add_action( 'wp_ajax_fetch_user_info', 'mobex_enovathemes_fetch_user_info' );

    /* Header
    ---------------*/

        function mobex_enovathemes_header(){ ?>

            <?php

                $desktop_header = get_theme_mod('desktop_header');
                $mobile_header  = get_theme_mod('mobile_header');

                if (empty($desktop_header)) {
                    $desktop_header = 'default';
                }

                if (empty($mobile_header)) {
                    $mobile_header = 'default';
                }


                if (class_exists('SitePress') || function_exists('pll_the_languages')){

                    $current_lang = (function_exists('pll_the_languages')) ? pll_current_language() : ICL_LANGUAGE_CODE;

                    if ($desktop_header != 'default') {
                        $lang_desktop_header = (function_exists('pll_the_languages')) ? pll_get_post($desktop_header) : icl_object_id($desktop_header, 'header', false, $current_lang);
                        if ($lang_desktop_header) {
                            $desktop_header = $lang_desktop_header;
                        }
                    }

                    if ($mobile_header != 'default') {
                        $lang_mobile_header  = (function_exists('pll_the_languages')) ? pll_get_post($mobile_header ) : icl_object_id($mobile_header , 'header', false, $current_lang);
                        if ($lang_mobile_header) {
                            $mobile_header = $lang_mobile_header;
                        }
                    }

                }


                if (is_page()) {

                    $page_desktop_header = get_post_meta( get_the_ID(), 'enovathemes_addons_desktop_header', true );
                    $page_mobile_header  = get_post_meta( get_the_ID(), 'enovathemes_addons_mobile_header', true );

                    if ($page_desktop_header != "inherit" && !empty($page_desktop_header)) {
                        $desktop_header = $page_desktop_header;
                    }

                    if ($page_mobile_header != "inherit" && !empty($page_mobile_header)) {
                        $mobile_header = $page_mobile_header;
                    }

                }

                if ($desktop_header == $mobile_header && $desktop_header != "default") {
                    $mobile_header = "none";
                }

                if (class_exists('\Detection\MobileDetect')) {


                    $detect = new \Detection\MobileDetect;

                    if ($detect->isMobile() || $detect->isTablet()) {
                        if ($mobile_header != "none" && $mobile_header != "default" && function_exists('enovathemes_addons_header_html')) {
                            enovathemes_addons_header_html($mobile_header, 'mobile');
                        } elseif ($mobile_header == "default") {
                            mobex_enovathemes_default_header('mobile');
                        }
                    } else {
                        if ($mobile_header != "none" && $mobile_header != "default" && function_exists('enovathemes_addons_header_html')) {
                            enovathemes_addons_header_html($mobile_header, 'mobile');
                        } elseif ($mobile_header == "default") {
                            mobex_enovathemes_default_header('mobile');
                        }

                        if ($desktop_header != "none" && $desktop_header != "default" && function_exists('enovathemes_addons_header_html')) {
                            enovathemes_addons_header_html($desktop_header, 'desktop');
                        } elseif ($desktop_header == "default") {
                            mobex_enovathemes_default_header('desktop');
                        }
                    }
                } else {

                    if ($mobile_header != "none" && $mobile_header != "default" && function_exists('enovathemes_addons_header_html')) {
                        enovathemes_addons_header_html($mobile_header, 'mobile');
                    } elseif ($mobile_header == "default") {
                        mobex_enovathemes_default_header('mobile');
                    }

                    if ($desktop_header != "none" && $desktop_header != "default" && function_exists('enovathemes_addons_header_html')) {
                        enovathemes_addons_header_html($desktop_header, 'desktop');
                    } elseif ($desktop_header == "default") {
                        mobex_enovathemes_default_header('desktop');
                    }
                }

            ?>

        <?php }
        add_action('mobex_enovathemes_header', 'mobex_enovathemes_header');

    /* Footer
    ---------------*/

        function mobex_enovathemes_footer(){ ?>

            <?php

                $footer = get_theme_mod('footer');

                if (empty($footer)) {
                    $footer = 'default';
                }

                if (class_exists('SitePress') || function_exists('pll_the_languages')){

                    $current_lang = (function_exists('pll_the_languages')) ? pll_current_language() : (defined('ICL_SITEPRESS_VERSION') ? ICL_LANGUAGE_CODE : false);

                    if ($footer != 'default' && $current_lang) {
                        $lang_footer  = (function_exists('pll_the_languages')) ? pll_get_post($footer ) : icl_object_id($footer , 'header', false, $current_lang);
                        if ($lang_footer) {
                            $footer = $lang_footer;
                        }
                    }

                }

                if (is_page()) {
                    $page_footer = get_post_meta( get_the_ID(), 'enovathemes_addons_footer', true );

                    if ($page_footer != "inherit" && !empty($page_footer)) {
                        $footer = $page_footer;
                    }
                }

                if ($footer != "none" && $footer != "default" && function_exists('enovathemes_addons_footer_html')) {
                    enovathemes_addons_footer_html($footer);
                } elseif ($footer == "default") {
                    mobex_enovathemes_default_footer();
                }

            ?>

        <?php }
        add_action('mobex_enovathemes_footer', 'mobex_enovathemes_footer');

    /* Page comments
    ---------------*/

        function mobex_enovathemes_page_comments(){
            if (class_exists('Woocommerce')){

                $add_comment_template = "true";

                if (is_cart() || is_checkout() || is_account_page() || is_wc_endpoint_url()) {
                    $add_comment_template = "false";
                }

                if ($add_comment_template == "true" &&  comments_open( get_the_ID() ) && !defined('ENOVATHEMES_ADDONS')) {
                    comments_template();
                }

            } else {

                $add_comment_template = "true";

                if ($add_comment_template == "true" &&  comments_open( get_the_ID() ) && !defined('ENOVATHEMES_ADDONS')) {
                    comments_template();
                }

            }
        }
        add_action('mobex_enovathemes_after_page_body', 'mobex_enovathemes_page_comments');

    /* Page container after/before
    ---------------*/

        function mobex_enovathemes_woocommerce_page_container_before(){
            if (class_exists('Woocommerce')){
                if (is_cart() || is_checkout() || is_account_page() || is_wc_endpoint_url()) {
                    echo '<div class="product-layout product-container-boxed">';
                }

            }
        }
        add_action('mobex_enovathemes_before_page_container', 'mobex_enovathemes_woocommerce_page_container_before');


        function mobex_enovathemes_woocommerce_page_container_after(){
            if (class_exists('Woocommerce')){
                if (is_cart() || is_checkout() || is_account_page() || is_wc_endpoint_url()) {
                    echo '</div>';
                }
            }
        }
        add_action('mobex_enovathemes_after_page_container', 'mobex_enovathemes_woocommerce_page_container_after');

/* Menu
---------------*/

    function mobex_enovathemes_register_menu() {

        register_nav_menus(
            array(
              'header-menu' => esc_html__( 'Header menu', 'mobex' ),
            )
        );

    }
    add_action( 'after_setup_theme', 'mobex_enovathemes_register_menu' );

/* Widget areas
---------------*/

    add_action( 'widgets_init', 'mobex_enovathemes_register_sidebars' );
    function mobex_enovathemes_register_sidebars() {

        if ( function_exists( 'register_sidebar' ) ){

            register_sidebar(
                array (
                'name'          => esc_html__( 'Blog widgets', 'mobex'),
                'id'            => 'blog-widgets',
                'description'   => esc_html__('Add your blog widgets here. This is the main blog widget area. It is visible only in blog archive pages.', 'mobex'),
                'class'         => 'blog-widgets',
                'before_widget' => '<div id="%1$s" class="widget %2$s">',
                'after_widget'  => '</div>',
                'before_title'  => '<h5 class="widget_title">',
                'after_title'   => '</h5>' )
            );

            register_sidebar(
                array (
                'name'          => esc_html__( 'Blog single post page widgets', 'mobex'),
                'id'            => 'blog-single-widgets',
                'description'   => esc_html__('Add your blog single post widgets here. This widget area is only visible in the single post page.', 'mobex'),
                'class'         => 'blog-single-widgets',
                'before_widget' => '<div id="%1$s" class="widget %2$s">',
                'after_widget'  => '</div>',
                'before_title'  => '<h5 class="widget_title">',
                'after_title'   => '</h5>' )
            );

            register_sidebar(
                array (
                'name'          => esc_html__( 'Blog after single post widgets', 'mobex'),
                'id'            => 'blog-after-single-widgets',
                'description'   => esc_html__('This widget area is only visible after the single post, before comments.', 'mobex'),
                'class'         => 'blog-after-single-widgets',
                'before_widget' => '<div id="%1$s" class="widget %2$s">',
                'after_widget'  => '</div>',
                'before_title'  => '<h5 class="widget_title">',
                'after_title'   => '</h5>' )
            );

            if (class_exists("Woocommerce")) {

                register_sidebar(
                    array (
                    'name'          => esc_html__( 'Shop widgets', 'mobex'),
                    'id'            => 'shop-widgets',
                    'description'   => esc_html__('Add your shop widgets here. This widget area is visible in shop arhive pages only.', 'mobex'),
                    'class'         => 'shop-widgets',
                    'before_widget' => '<div id="%1$s" class="widget %2$s">',
                    'after_widget'  => '</div>',
                    'before_title'  => '<h5 class="widget_title">',
                    'after_title'   => '</h5>' )
                );

                register_sidebar(
                    array (
                    'name'          => esc_html__( 'Shop single product summary widget area', 'mobex'),
                    'id'            => 'shop-single-summary-widgets',
                    'description'   => esc_html__('Add your shop single product summary widgets here. This widget area is only visible in single product page summary area.', 'mobex'),
                    'class'         => 'shop-single-summary-widgets',
                    'before_widget' => '<div id="%1$s" class="widget %2$s">',
                    'after_widget'  => '</div>',
                    'before_title'  => '<h5 class="widget_title">',
                    'after_title'   => '</h5>' )
                );

                register_sidebar(
                    array (
                    'name'          => esc_html__( 'Shop single product description next widget area', 'mobex'),
                    'id'            => 'shop-single-widgets',
                    'description'   => esc_html__('Add your shop single product widgets here. This widget area is only visible in single product page.', 'mobex'),
                    'class'         => 'shop-single-widgets',
                    'before_widget' => '<div id="%1$s" class="widget %2$s">',
                    'after_widget'  => '</div>',
                    'before_title'  => '<h5 class="widget_title">',
                    'after_title'   => '</h5>' )
                );

                register_sidebar(
                    array (
                    'name'          => esc_html__( 'Shop before products widget area', 'mobex'),
                    'id'            => 'shop-top-widgets',
                    'description'   => esc_html__('Add your shop widgets here. This widget area is visible in shop arhive pages only. And appears before products list', 'mobex'),
                    'class'         => 'shop-single-widgets',
                    'before_widget' => '<div id="%1$s" class="widget %2$s">',
                    'after_widget'  => '</div>',
                    'before_title'  => '<h5 class="widget_title">',
                    'after_title'   => '</h5>' )
                );

                register_sidebar(
                    array (
                    'name'          => esc_html__( 'Shop after products widget area', 'mobex'),
                    'id'            => 'shop-bottom-widgets',
                    'description'   => esc_html__('Add your shop widgets here. This widget area is visible in shop arhive pages only. And appears after products list', 'mobex'),
                    'class'         => 'shop-single-widgets',
                    'before_widget' => '<div id="%1$s" class="widget %2$s">',
                    'after_widget'  => '</div>',
                    'before_title'  => '<h5 class="widget_title">',
                    'after_title'   => '</h5>' )
                );

            }
        }
    }

/* Woo Commerce
---------------*/

    if (class_exists('Woocommerce')){

        add_action('woocommerce_before_shop_loop','mobex_enovathemes_woocommerce_banner_area_top',10);
        function mobex_enovathemes_woocommerce_banner_area_top(){ ?>
            <?php get_sidebar('shop-top'); ?>
        <?php }

        remove_action( 'woocommerce_archive_description', 'woocommerce_taxonomy_archive_description', 10 );
        add_action( 'woocommerce_after_shop_loop', 'woocommerce_taxonomy_archive_description', 45 );

        add_action('woocommerce_after_shop_loop','mobex_enovathemes_woocommerce_banner_area_bottom',45);
        function mobex_enovathemes_woocommerce_banner_area_bottom(){ ?>
            <?php get_sidebar('shop-bottom'); ?>
        <?php }

        /* Show mini cart on cart and checkout
        ---------------*/

            add_filter( 'woocommerce_widget_cart_is_hidden', 'mobex_enovathemes_always_show_cart', 40, 0 );
            function mobex_enovathemes_always_show_cart() {
                return false;
            }

        /* Remove default styling
        ---------------*/

            add_filter( 'woocommerce_enqueue_styles', '__return_empty_array' );

        /* Woocommerce gallery support
        ---------------*/

            add_action( 'after_setup_theme', 'mobex_enovathemes_setup' );
            function mobex_enovathemes_setup() {
                add_theme_support( 'wc-product-gallery-zoom' );
                add_theme_support( 'wc-product-gallery-lightbox' );
                add_theme_support( 'wc-product-gallery-slider' );
            }

        /* Add to cart
        ---------------*/

            add_filter('woocommerce_add_to_cart_fragments', 'mobex_enovathemes_add_to_cart');
            function mobex_enovathemes_add_to_cart( $fragments ) {

                global $woocommerce;

                ob_start(); ?>

                <?php if ($GLOBALS['woocommerce']->cart->cart_contents_count): ?>
                    <span class="cart-contents"><?php echo mobex_enovathemes_output_html($GLOBALS['woocommerce']->cart->cart_contents_count); ?></span>
                <?php else: ?>
                    <span class="cart-contents">0</span>
                <?php endif; ?>

                <?php

                $fragments['span.cart-contents'] = ob_get_clean();
                return $fragments;

            }

        /* Shop loop
        ---------------*/

            remove_action( 'woocommerce_before_main_content', 'woocommerce_output_content_wrapper', 10 );
            remove_action( 'woocommerce_before_main_content', 'woocommerce_breadcrumb', 20 );
            remove_action( 'woocommerce_after_main_content', 'woocommerce_output_content_wrapper_end', 10 );
            remove_action( 'woocommerce_before_shop_loop', 'woocommerce_result_count', 20 );
            remove_action( 'woocommerce_before_shop_loop', 'woocommerce_catalog_ordering', 30 );

            /* Shop title
            ---------------*/

                add_filter( 'woocommerce_show_page_title' , 'mobex_enovathemes_woo_hide_page_title' );
                function mobex_enovathemes_woo_hide_page_title() {
                    return false;
                }

            /* Shop filter
            ---------------*/

                add_action( 'woocommerce_before_shop_loop', 'mobex_enovathemes_before_shop_loop_open', 15 );
                function mobex_enovathemes_before_shop_loop_open() {?><div class="woocommerce-before-shop-loop et-clearfix">

                    <?php

                        $shop_layout         = get_theme_mod('shop_layout');
                        $shop_sidebar        = get_theme_mod('shop_sidebar');
                        $shop_sidebar_toggle = (get_theme_mod('shop_sidebar_toggle') != null && !empty(get_theme_mod('shop_sidebar_toggle'))) ? true : false;

                        if (is_active_sidebar('shop-widgets') && empty($shop_sidebar) && !defined('ENOVATHEMES_ADDONS')) {
                            $shop_sidebar = 'true';
                        }

                        if (empty($shop_layout)) {
                            $shop_layout = 'grid';
                        }
                    
                        $data_shop  = (isset($_GET["data_shop"]) && !empty($_GET["data_shop"])) ? $_GET["data_shop"] : "default";
                        if($data_shop == 'toggle'){
                            $shop_sidebar_toggle = true;
                        }

                    ?>

                    <?php if (!empty($shop_sidebar)): ?>

                        <div class="layout-control" data-layout="<?php echo  esc_attr($shop_layout); ?>" data-size="medium">
                            <div <?php echo (($shop_layout == "grid") ? 'class="chosen"' : ''); ?> data-layout="grid" data-size="medium"></div>
                            <div <?php echo (($shop_layout == "list") ? 'class="chosen"' : ''); ?> data-layout="list" data-size="medium"></div>
                            <div <?php echo (($shop_layout == "comp") ? 'class="chosen"' : ''); ?> data-layout="comp" data-size="medium"></div>
                        </div>

                        <?php if ($shop_sidebar_toggle): ?>
                            <a href="#" title="<?php echo esc_attr__("Toggle sidebar","mobex"); ?>" class="content-sidebar-toggle visible"></a>
                        <?php endif ?>

                    <?php endif ?>

                    <?php

                    add_action( 'woocommerce_before_shop_loop', 'woocommerce_catalog_ordering', 20 );}

                    add_action( 'woocommerce_before_shop_loop', 'mobex_enovathemes_only_sale', 25 );
                    function mobex_enovathemes_only_sale(){ ?>
                        <div class="sale-products"><?php echo esc_html__("Only products on sale","mobex"); ?></div>
                    <?php }

                    add_action( 'woocommerce_before_shop_loop', 'woocommerce_result_count', 30 );

                add_action( 'woocommerce_before_shop_loop', 'mobex_enovathemes_before_shop_loop_close', 40 );
                function mobex_enovathemes_before_shop_loop_close() {?>
                    </div>
                <?php }

                add_action( 'woocommerce_before_shop_loop', 'mobex_enovathemes_before_shop_loop_filter_breadcrumbs', 45 );
                function mobex_enovathemes_before_shop_loop_filter_breadcrumbs() {?>
                    <?php if (isset($_GET["sel"]) && !empty($_GET["sel"]) && $_GET["sel"] == 'true' && function_exists('filter_breadcrumbs_output')) {

                        $filter_breadcrumbs = array();

                        foreach ($_GET as $key => $value) {
                            if ($key != 'sel') {
                                $taxonomy = ($key == 'product_cat') ? $key : 'pa_'.substr($key, 7);
                                $label    = ($key == 'product_cat') ? esc_html__('Category','mobex') : ucfirst(substr($key, 7));
                                $label    = str_replace('-', ' ', $label);
                                $term     = get_term_by('slug',$value,$taxonomy);
                                if ($term) {
                                    $filter_breadcrumbs[] = '<span class="breadcrumbs-item">'.$label.': '.$term->name.'</span>';
                                }
                            }
                        }

                        if (!empty($filter_breadcrumbs)) {
                            echo filter_breadcrumbs_output($filter_breadcrumbs);
                        }  

                    } ?>
                <?php }

            /* Shop loop item
            ---------------*/

                remove_action( 'woocommerce_before_shop_loop_item', 'woocommerce_template_loop_product_link_open', 10 );
                remove_action( 'woocommerce_after_shop_loop_item', 'woocommerce_template_loop_product_link_close', 5 );

                add_action( 'woocommerce_before_shop_loop_item', 'mobex_enovathemes_loop_product_inner_open', 10 );
                function mobex_enovathemes_loop_product_inner_open() { ?>

                    <div class="post-inner et-item-inner">

                        <?php if(get_option( 'woocommerce_enable_ajax_add_to_cart' ) === "yes"){ ?>
                            <div class="ajax-add-to-cart-loading">
                                <svg viewBox="0 0 56 56"><circle class="loader-path" cx="28" cy="28" r="20" /></svg>
                                <svg viewBox="0 0 511.999 511.999" class="tick"><path d="M506.231 75.508c-7.689-7.69-20.158-7.69-27.849 0l-319.21 319.211L33.617 269.163c-7.689-7.691-20.158-7.691-27.849 0-7.69 7.69-7.69 20.158 0 27.849l139.481 139.481c7.687 7.687 20.16 7.689 27.849 0l333.133-333.136c7.69-7.691 7.69-20.159 0-27.849z"/></svg>
                            </div>
                        <?php } ?>

                <?php }

                    remove_action( 'woocommerce_before_shop_loop_item_title', 'woocommerce_show_product_loop_sale_flash', 10 );
                    remove_action( 'woocommerce_before_shop_loop_item_title', 'woocommerce_template_loop_product_thumbnail', 10 );

                    add_action( 'woocommerce_before_shop_loop_item_title', 'mobex_enovathemes_loop_product_thumbnail_action', 10 );
                    function mobex_enovathemes_loop_product_thumbnail_action() { ?>

                        <?php
                            $shop_layout = get_theme_mod('shop_layout');
                            if (empty($shop_layout)) {
                                $shop_layout = 'grid';
                            }
                            echo mobex_enovathemes_loop_product_thumbnail($shop_layout);
                        ?>

                    <?php }

                    remove_action( 'woocommerce_shop_loop_item_title', 'woocommerce_template_loop_product_title', 10 );
                    remove_action( 'woocommerce_after_shop_loop_item_title', 'woocommerce_template_loop_rating', 5 );
                    remove_action( 'woocommerce_after_shop_loop_item', 'woocommerce_template_loop_add_to_cart', 10 );
                    remove_action( 'woocommerce_after_shop_loop_item_title', 'woocommerce_template_loop_price', 10 );

                    add_action( 'woocommerce_shop_loop_item_title', 'mobex_enovathemes_loop_product_title_action', 10 );
                    function mobex_enovathemes_loop_product_title_action() { ?>

                        <?php
                            $shop_layout = get_theme_mod('shop_layout');
                            if (empty($shop_layout)) {
                                $shop_layout = 'grid';
                            }
                            echo mobex_enovathemes_loop_product_title($shop_layout);
                        ?>

                    <?php }

                add_action( 'woocommerce_after_shop_loop_item', 'mobex_enovathemes_loop_product_inner_close_action', 20 );
                function mobex_enovathemes_loop_product_inner_close_action() { ?>
                    <?php 
                        $shop_layout = get_theme_mod('shop_layout');
                        if (empty($shop_layout)) {
                            $shop_layout = 'grid';
                        }
                        echo mobex_enovathemes_loop_product_inner_close($shop_layout);
                    ?>

                    </div>
                <?php }

            /* Shop navigation
            ---------------*/

                add_action('init','mobex_enovathemes_woocommerce_nav');
                function mobex_enovathemes_woocommerce_nav(){

                    $woocommerce_get_loop_display_mode = get_option('woocommerce_shop_page_display');

                    if ('products' == $woocommerce_get_loop_display_mode) {

                        $shop_navigation = get_theme_mod('shop_navigation');
                        if (empty($shop_navigation)) {
                            $shop_navigation = 'pagination';
                        }
                        
                        $data_shop  = (isset($_GET["data_shop"]) && !empty($_GET["data_shop"])) ? $_GET["data_shop"] : "default";
                        if($data_shop == 'infinite'){
                            $shop_navigation = 'infinite';
                        } elseif($data_shop == 'loadmore'){
                            $shop_navigation = 'loadmore';
                        }

                        remove_action( 'woocommerce_after_shop_loop', 'woocommerce_pagination', 10 );
                        add_action( 'woocommerce_after_shop_loop', 'mobex_enovathemes_woocommerce_pagination', 10 );
                        function mobex_enovathemes_woocommerce_pagination() {

                            $shop_navigation = get_theme_mod('shop_navigation');
                            if (empty($shop_navigation)) {
                                $shop_navigation = 'pagination';
                            }
                            
                            $data_shop  = (isset($_GET["data_shop"]) && !empty($_GET["data_shop"])) ? $_GET["data_shop"] : "default";
                            if($data_shop == 'infinite'){
                                $shop_navigation = 'infinite';
                            } elseif($data_shop == 'loadmore'){
                                $shop_navigation = 'loadmore';
                            }

                            $nav = (function_exists('mobex_enovathemes_navigation')) ? mobex_enovathemes_navigation('product',$shop_navigation) : mobex_enovathemes_post_nav_num('product');
                            
                                echo mobex_enovathemes_output_html($nav);

                            if ($shop_navigation == 'pagination' && strpos($_SERVER['REQUEST_URI'], '?') === false && strpos($_SERVER['REQUEST_URI'], 'page') === false) {
                                set_transient( 'enovathemes-products-navigation-pagination', $nav, apply_filters( 'null_product_filter_cache_time', 0 ) );
                            }

                        }

                    }

                }

                add_action( 'woocommerce_after_shop_loop', 'mobex_enovathemes_no_products_found', 9 );
                function mobex_enovathemes_no_products_found() {?>
                    <?php

                        $product_notfound_form = get_theme_mod('product_notfound_form');

                        if (
                            shortcode_exists('contact-form-7') && 
                            isset($product_notfound_form) && !empty($product_notfound_form)
                        ) {
                            echo '<div class="no-vehicles-form">';
                                echo '<h4>'.esc_html__("Can't find your part or vehicle?","mobex").'</h4>';
                                echo '<p>'.esc_html__("No worries. Our team is here to help you find the perfect part for your car. Just provide us with some details and we will get to work!","mobex").'</p>';
                                echo do_shortcode('[contact-form-7 id="'.$product_notfound_form.'"]');
                            echo '</div>';
                        }

                    ?>
                <?php }

        /* Category
        ---------------*/

            function mobex_enovathemes_category_class( $classes, $class, $category= null ){
                $classes[] = 'et-item post';
                return $classes;
            }
            add_filter( 'product_cat_class', 'mobex_enovathemes_category_class', 10, 3 );

            remove_action( 'woocommerce_before_subcategory', 'woocommerce_template_loop_category_link_open', 10);
            remove_action( 'woocommerce_after_subcategory', 'woocommerce_template_loop_category_link_close', 10);

            remove_action( 'woocommerce_shop_loop_subcategory_title', 'woocommerce_template_loop_category_title', 10);
            add_action( 'woocommerce_shop_loop_subcategory_title', 'woocommerce_template_loop_category_title', 10);
            if ( ! function_exists( 'woocommerce_template_loop_category_title' ) ) {
                function woocommerce_template_loop_category_title( $category ) { ?>
                    <h4 class="woocommerce-loop-category__title post-title post-title">
                        <a href="<?php echo esc_url(get_term_link( $category->slug, 'product_cat' )); ?>" title="<?php echo esc_attr__("View ", 'mobex').' '.esc_attr( $category->name ); ?>">
                        <?php echo esc_attr($category->name);?>
                        </a>
                    </h4>

                <?php }
            }

            function mobex_enovathemes_before_subcategory($category){ ?>
                <div class="post-inner et-item-inner">

                    <?php

                        $image_class = array();
                        $image_class[] = 'post-image';
                        $image_class[] = 'post-media';
                        $image_class[] = 'overlay-hover';

                    ?>

                    <div class="<?php echo implode(' ', $image_class); ?>">
                        <a href="<?php echo esc_url(get_term_link( $category->slug, 'product_cat' )); ?>" title="<?php echo esc_attr__("View ", 'mobex').' '.esc_attr( $category->name ); ?>">
                            <div class="image-container">
            <?php }
            add_filter( 'woocommerce_before_subcategory', 'mobex_enovathemes_before_subcategory', 10, 2);

            remove_action( 'woocommerce_before_subcategory_title', 'woocommerce_subcategory_thumbnail', 10);
            add_action( 'woocommerce_before_subcategory_title', 'mobex_enovathemes_subcategory_thumbnail', 10);
            function mobex_enovathemes_subcategory_thumbnail($category){

                $thumb_size = 'woocommerce_thumbnail';

                $thumbnail_id = get_term_meta( $category->term_id, 'thumbnail_id', true  );

                if ($thumbnail_id) {
                    echo mobex_enovathemes_build_post_media($thumb_size,$thumbnail_id,'product');
                } else {
                    $image = wc_placeholder_img_src();
                    if ( $image ) {
                        $image = str_replace( ' ', '%20', $image );
                        echo '<img src="' . esc_url( $image ) . '" />';
                    }
                }
                
            }

            add_filter( 'woocommerce_before_subcategory_title', 'mobex_enovathemes_before_subcategory_title', 10, 2 );
            function mobex_enovathemes_before_subcategory_title(){ ?>
                            </div>
                        </a>
                    </div>
                    <div class="post-body et-clearfix">
                        <div class="post-body-inner">
            <?php }

            add_filter( 'woocommerce_after_subcategory_title', 'mobex_enovathemes_after_subcategory_title', 10, 2 );
            function mobex_enovathemes_after_subcategory_title(){ ?>
                        </div>
                    </div>
            <?php }

            function mobex_enovathemes_after_subcategory(){ ?>
                </div>
            <?php }
            add_filter( 'woocommerce_after_subcategory', 'mobex_enovathemes_after_subcategory', 10, 2 );

            remove_action( 'woocommerce_cart_collaterals', 'woocommerce_cross_sell_display' );
            add_action( 'woocommerce_after_cart', 'woocommerce_cross_sell_display' );

        /* Single product
        ---------------*/

            add_filter( 'wc_product_sku_enabled', 'mobex_enovathemes_remove_product_sku' );
            function mobex_enovathemes_remove_product_sku( $sku ) {
                if ( ! is_admin() && is_product() ) {
                    return false;
                }
                return $sku;
             }

            add_action('woocommerce_single_product_summary','mobex_enovathemes_wishlist_toggle_single',35);
            function mobex_enovathemes_wishlist_toggle_single(){

                global $product;

                $wishlist = (!empty(get_theme_mod('product_wishlist'))) ? "true" : "false";
                $compare  = (!empty(get_theme_mod('product_compare'))) ? "true" : "false";
                $title    = esc_html__("Add to wishlist","mobex");
                $class    = '';


                if($wishlist == "true"){
                    
                    $wishlist_count = get_post_meta($product->get_id(), 'enovathemes_addons_wishlist', true );

                    if (is_user_logged_in()) {
                        $current_user = wp_get_current_user();
                        $current_user_wishlist = get_user_meta( $current_user->ID, 'wishlist',true);

                        if (isset($current_user_wishlist) && !empty($current_user_wishlist) && in_array($product->get_id(), explode(',', $current_user_wishlist))) {
                           $title = esc_html__("In wishlist","mobex");
                           $class = 'active';
                           $wishlist_count = '';
                        }

                    }

                    echo '<a class="wishlist-toggle '.esc_attr($class).'" data-product="'.esc_attr($product->get_id()).'" href="'.esc_url(get_permalink(get_option('woocommerce_myaccount_page_id'))).'wishlist'.'" title="'.$title.'"></a><span class="wishlist-title">'.$title.'</span>';
                }
                if($compare == "true"){
                    echo '<a class="compare-toggle" data-product="'.esc_attr($product->get_id()).'" href="#" title="'.esc_attr__("Compare","mobex").'"></a><span class="compare-title">'.esc_attr__("Add to compare","mobex").'</span>';
                }
                
            }

            add_action( 'woocommerce_before_single_product_summary', 'mobex_enovathemes_single_product_wrapper_open', 5 );
            function mobex_enovathemes_single_product_wrapper_open() {?>

                <?php

                    global $product;

                    $gallery = $product->get_gallery_image_ids() ? 'true' : 'false';
                    $fbt_ids = get_post_meta( get_the_ID(), 'fbt_ids', true ) ? 'true' : 'false';
                    $universal = get_post_meta(get_the_ID(),'enovathemes_addons_universal',true) ? 'true' : 'false';

                ?>

                <div class="single-product-wrapper et-clearfix gallery-<?php echo esc_attr($gallery); ?> fbt-<?php echo esc_attr($fbt_ids); ?> uni-<?php echo esc_attr($universal); ?>">
            <?php }

                add_action( 'woocommerce_single_product_summary', 'mobex_enovathemes_summary_details_open', 2 );
                function mobex_enovathemes_summary_details_open(){ ?>
                    <div class="summary-details">
                <?php }

                    add_action( 'woocommerce_single_product_summary', 'mobex_enovathemes_single_product_before_title', 2 );
                    function mobex_enovathemes_single_product_before_title(){ ?>
                        <div class="single-title-wrapper et-clearfix">
                            <?php

                                global $product;

                                if (taxonomy_exists('pa_brand')) {

                                    $attr = get_the_terms($product->get_id(),'pa_brand');

                                    if ($attr && !is_wp_error($attr)) {

                                        foreach ($attr as $key => $term) {
                                            $image = get_term_meta($term->term_id,'image',true);
                                            if (isset($image) && !empty($image)) {
                                                echo '<div class="product-brand"><img alt="'.esc_attr($term->name).'" src="'.wp_get_attachment_url($image).'"></div>';
                                            }
                                            
                                        }
                                        
                                    }
                                }


                            ?>
                    <?php }

                    remove_action( 'woocommerce_single_product_summary', 'woocommerce_template_single_rating', 10 );

                    add_action( 'woocommerce_single_product_summary', 'mobex_enovathemes_single_product_after_title', 6 );
                    function mobex_enovathemes_single_product_after_title(){ ?>

                        <?php 

                            global $product;

                            if ( $product->get_sku() ) {
                                echo '<p class="sku"><span>'.esc_html__("SKU","mobex").':</span> '.$product->get_sku().'</p>';
                            }

                        ?>

                    <?php }

                    add_action( 'woocommerce_single_product_summary', 'woocommerce_template_single_rating', 6 );
                    

                    add_action( 'woocommerce_single_product_summary', 'mobex_enovathemes_single_product_after_title_close', 6 );
                    function mobex_enovathemes_single_product_after_title_close(){ ?>
                        </div>
                    <?php }

                    remove_action( 'woocommerce_single_product_summary', 'woocommerce_template_single_price', 10 );
                    remove_action( 'woocommerce_single_product_summary', 'woocommerce_template_single_excerpt', 20 );
                    add_action( 'woocommerce_single_product_summary', 'woocommerce_template_single_price', 15 );

                    add_action( 'woocommerce_single_product_summary', 'mobex_enovathemes_product_stock', 15 );
                    function mobex_enovathemes_product_stock(){
                        global $product;

                        if ($product->get_manage_stock()) {

                            $stock = $product->get_stock_status();

                            $stock_status = '';

                            switch ($stock) {
                                case 'outofstock':
                                    $stock_status = esc_html__('Out of stock','mobex');
                                    break;
                                case 'onbackorder':
                                    $stock_status = esc_html__('On backorder','mobex');
                                    break;
                                default:
                                    $stock_status = esc_html__('In stock','mobex');
                                    break;
                            }

                            echo '<p class="stock-status '.$stock.'">'.$stock_status.'</p>'; 
                        }
                    }

                add_action( 'woocommerce_before_single_product_summary', 'mobex_enovathemes_nav_tabs', 1 );
                function mobex_enovathemes_nav_tabs() { global $product;

                    $modes          = et_get_theme_mods();
                    $product_layout = isset($modes['product_layout']) ? $modes['product_layout'] : 'simple';

                    $nav_tabs = array(
                        'photo' => esc_html__("Image","mobex"),
                    );

                    if ($product_layout == "advanced") {
                        $nav_tabs['info'] = esc_html__("Info","mobex");
                    }

                    $fbt_ids       = get_post_meta( $product->get_id(), 'fbt_ids', true );
                    $product_terms = get_the_terms( $product->get_id(), 'vehicles');
                    $compare_ids   = get_post_meta( $product->get_id(), 'compare_ids', true );
                    $faq           = get_post_meta($product->get_id(),'faq',true);

                    if (!empty($fbt_ids)) {
                        $nav_tabs['fbt'] = esc_html__("Linked products","mobex");
                    }

                    if ($product->get_description()) {
                        $nav_tabs['description'] = esc_html__("Description","mobex");
                    }

                    if (! is_wp_error( $product_terms ) && $product_terms) {
                        $nav_tabs['vehicles'] = esc_html__("Vehicles","mobex");
                    }


                    if (!empty($compare_ids)) {
                        $nav_tabs['compare'] = esc_html__("Compare","mobex");
                    }

                    if ($product->get_reviews_allowed()) {
                        $nav_tabs['reviews'] = esc_html__("Reviews","mobex");
                    }

                    if ($faq) {
                        $nav_tabs['faq'] = esc_html__("FAQ","mobex");
                    }

                ?>
                    <ul class="product-nav-tabs">
                        <?php foreach ($nav_tabs as $key => $value) { ?>
                            <li><a href="<?php echo (($key == 'photo') ? '#wrap' : '#product-nav-target-'.esc_attr($key)); ?>" data-target="<?php echo esc_attr($key); ?>"><?php echo esc_html($value); ?></a></li>
                        <?php } ?>
                    </ul>
                <?php }



                add_action( 'woocommerce_after_add_to_cart_form', 'mobex_enovathemes_summary_banner', 1 );
                function mobex_enovathemes_summary_banner(){ ?>
                    <?php

                            global $product;

                            $modes          = et_get_theme_mods();
                            $product_layout = isset($modes['product_layout']) ? $modes['product_layout'] : 'simple';
                           
                            if ($product_layout == "simple" && $product->get_short_description()) {
                                echo '<div class="short-description">';
                                    echo mobex_enovathemes_output_html($product->get_short_description());
                                echo '</div>';
                            }

                            $summary_banner = get_post_meta($product->get_id(),'enovathemes_addons_summary_banner',true);


                            if (!empty($summary_banner) && $summary_banner != "none" && function_exists('enovathemes_addons_get_the_widget')) {

                                $args = array(
                                    'before_widget' => '<div class="shop-summary-widgets widget widget_banner">',
                                    'after_widget'  => '</div>',
                                    'before_title'  => '',
                                    'after_title'   => '',
                                );

                                $instance = array(
                                    'banner' => $summary_banner,
                                    'category' => '',
                                    'children' => '',
                                    'shop'     => '',
                                );

                                echo enovathemes_addons_get_the_widget( 'Enovathemes_Addons_WP_Widget_Banner', $instance,$args);
                            } else {
                                get_sidebar('shop-single-summary');
                            }

                    ?>

                <?php }


                add_action( 'woocommerce_single_product_summary', 'mobex_enovathemes_social_share', 45 );
                function mobex_enovathemes_social_share() {

                    $product_social_share = (!empty(get_theme_mod('product_social_share'))) ? "true" : "false";

                    if ($product_social_share == "true" && function_exists('enovathemes_addons_post_social_share')) {
                        echo enovathemes_addons_post_social_share('post-social-share');
                    }

                }


                add_action( 'woocommerce_single_product_summary', 'mobex_enovathemes_summary_details_close', 45 );
                function mobex_enovathemes_summary_details_close() {?>
                    </div>
                <?php }

                add_filter( 'woocommerce_product_tabs', 'mobex_enovathemes_remove_product_tabs_reviews', 98 );
                function mobex_enovathemes_remove_product_tabs_reviews( $tabs ) {
                  unset( $tabs['reviews'] ); // To remove the additional information tab
                  return $tabs;
                }

                add_action('init',function(){
                    
                    $modes          = et_get_theme_mods();
                    $product_layout = isset($modes['product_layout']) ? $modes['product_layout'] : 'simple';

                    if ($product_layout == "advanced") {

                        add_filter( 'woocommerce_product_tabs', 'mobex_enovathemes_remove_product_tabs_info', 98 );
                        function mobex_enovathemes_remove_product_tabs_info( $tabs ) {
                          unset( $tabs['additional_information'] ); // To remove the additional information tab
                          return $tabs;
                        }

                        add_action( 'woocommerce_single_product_summary', 'mobex_enovathemes_summary_details_open_2', 45 );
                        function mobex_enovathemes_summary_details_open_2(){ global $product; ?>
                            <div class="summary-details">

                                <div class="et-accordion collapsible-false">

                                    <?php if ($product && ( $product->has_attributes() || apply_filters( 'wc_product_enable_dimensions_display', $product->has_weight() || 
                                        $product->has_dimensions() ) )): ?>
                                        <div class="accordion-title active"><?php echo esc_html__('Product information','mobex'); ?></div>
                                        <div class="accordion-content active info"><?php wc_display_product_attributes( $product ) ?></div>
                                    <?php endif ?>

                                    <?php if ($product->get_short_description()): ?>
                                        <div class="accordion-title active"><?php echo esc_html__('Description','mobex'); ?></div>
                                        <div class="accordion-content active">
                                            <?php echo mobex_enovathemes_output_html($product->get_short_description()); ?>
                                        </div>
                                    <?php endif ?>

                                    <?php $features = get_post_meta($product->get_id(),'enovathemes_addons_features',true) ?>

                                    <?php if (!empty($features)): ?>
                                        <div class="accordion-title active"><?php echo esc_html__('Features','mobex'); ?></div>
                                        <div class="accordion-content active">
                                            <?php

                                                $split = preg_split("/(\r?\n)+|(<br\s*\/?>\s*)+/", $features);
                                                $output = '<ul class="features">';  
                                                    foreach($split as $haystack) {
                                                        $output .= '<li>'.$haystack.'</li>';
                                                    }
                                                $output .= '</ul>';

                                                echo mobex_enovathemes_output_html($output);

                                            ?>
                                        </div>
                                    <?php endif ?>

                                </div>

                        <?php }

                        add_action( 'woocommerce_single_product_summary', 'mobex_enovathemes_summary_details_close_2', 47 );
                        function mobex_enovathemes_summary_details_close_2(){ ?>
                            </div>
                        <?php }

                    }

                    add_action( 'woocommerce_after_single_product_summary', 'mobex_enovathemes_single_product_fbt', 5 );
                    function mobex_enovathemes_single_product_fbt() {mobex_enovathemes_fbt_output();}

                    add_action( 'woocommerce_after_single_product_summary', 'mobex_enovathemes_single_product_ss', 5 );
                    function mobex_enovathemes_single_product_ss() {
                        $ss_ids = get_post_meta( get_the_ID(), 'ss_ids', true );

                        if (!empty($ss_ids)) {
                            echo '<div class="ss-products">';
                                echo '<h4>'.esc_html__('Supersession','mobex').'</h4>';
                                echo do_shortcode('[et_products ids="'.implode(',', $ss_ids).'" carousel="true" navigation_position="top-right" type="custom" columns="6" columns_tab_land="3" columns_tab_port="2" ajax="false"]');
                            echo '</div>';
                        }
                    }

                });    

            add_action( 'woocommerce_after_single_product_summary', 'mobex_enovathemes_single_product_wrapper_close', 0 );
            function mobex_enovathemes_single_product_wrapper_close() {?>
                </div>
            <?php }
        
            add_action( 'woocommerce_after_single_product_summary', 'mobex_enovathemes_single_product_after_summary_banner', 6 );
            function mobex_enovathemes_single_product_after_summary_banner(){

                        global $product;

                        $after_summary_banner = get_post_meta($product->get_id(),'enovathemes_addons_after_summary_banner',true);

                        if (!empty($after_summary_banner) && $after_summary_banner != "none" && function_exists('enovathemes_addons_get_the_widget')) {

                            $args = array(
                                'before_widget' => '<div class="shop-after-summary-widgets widget widget_banner">',
                                'after_widget'  => '</div>',
                                'before_title'  => '',
                                'after_title'   => '',
                            );

                            $instance = array(
                                'banner' => $after_summary_banner,
                                'category' => '',
                                'children' => '',
                                'shop'     => '',
                            );

                            echo enovathemes_addons_get_the_widget( 'Enovathemes_Addons_WP_Widget_Banner', $instance,$args);
                        }

            }

            add_action( 'woocommerce_after_add_to_cart_quantity', 'mobex_enovathemes_quantity_plus_sign' );
            function mobex_enovathemes_quantity_plus_sign() {
                global $product;
                if (!$product->is_type( 'grouped' )) {
                    echo '<button type="button" class="plus" >+</button></div>';
                }
            }
             
            add_action( 'woocommerce_before_add_to_cart_quantity', 'mobex_enovathemes_quantity_minus_sign' );
            function mobex_enovathemes_quantity_minus_sign() {
                global $product;
                if (!$product->is_type( 'grouped' )) {
                    echo '<div class="variation-calc"><button type="button" class="minus" disabled>-</button>';
                }
            }

            add_action( 'woocommerce_after_add_to_cart_button', 'mobex_enovathemes_buy_now_button');
            function mobex_enovathemes_buy_now_button() { 

                $product_quick_buy  = (!empty(get_theme_mod('product_quick_buy'))) ? "true" : "false";


                if ($product_quick_buy == "true") {
                    global $product;

                    if ('instock' == $product->get_stock_status()) {
                        echo '<a href="' . esc_url(wc_get_checkout_url()) . '?add-to-cart=' . esc_attr($product->get_id()) . '" class="button single_add_to_cart_button buy-now-button">'.esc_html__("Buy now","mobex").'</a>';
                    }
                }
            }

            add_action( 'woocommerce_after_single_product_summary', 'mobex_enovathemes_single_product_before_description_wrap', 9 );
            function mobex_enovathemes_single_product_before_description_wrap(){ global $product;
                echo '<div class="before-description-wrap">';
                    if ($product->get_description()) {
                        echo '<div>';
                    }
            }

            add_action( 'woocommerce_after_single_product_summary', 'mobex_enovathemes_single_product_after_description_wrap', 10 );
            function mobex_enovathemes_single_product_after_description_wrap(){ global $product;

                        $after_description_banner = get_post_meta($product->get_id(),'enovathemes_addons_after_description_banner',true);

                        if (!empty($after_description_banner) && $after_description_banner != "none"  && function_exists('enovathemes_addons_get_the_widget')) {

                            $args = array(
                                'before_widget' => '<div class="shop-after-description-widgets widget widget_banner">',
                                'after_widget'  => '</div>',
                                'before_title'  => '',
                                'after_title'   => '',
                            );

                            $instance = array(
                                'banner' => $after_description_banner,
                                'category' => '',
                                'children' => '',
                                'shop'     => '',
                            );

                            echo enovathemes_addons_get_the_widget( 'Enovathemes_Addons_WP_Widget_Banner', $instance,$args);
                        }

                    if ($product->get_description()) {
                        echo '</div>';
                    }

                    $next_description_banner = get_post_meta($product->get_id(),'enovathemes_addons_next_description_banner',true);

                    if (!empty($next_description_banner) && $next_description_banner != "none"  && function_exists('enovathemes_addons_get_the_widget')) {

                        $args = array(
                            'before_widget' => '<div class="shop-next-description-widgets widget widget_banner">',
                            'after_widget'  => '</div>',
                            'before_title'  => '',
                            'after_title'   => '',
                        );

                        $instance = array(
                            'banner' => $next_description_banner,
                            'category' => '',
                            'children' => '',
                            'shop'     => '',
                        );

                        echo enovathemes_addons_get_the_widget( 'Enovathemes_Addons_WP_Widget_Banner', $instance,$args);
                    }

                echo '</div>';
            }

            add_action( 'woocommerce_after_single_product_summary', 'mobex_enovathemes_single_product_compatible_vehicles', 10 );
            function mobex_enovathemes_single_product_compatible_vehicles(){ global $product;

                $product_terms = get_the_terms( $product->get_id(), 'vehicles');

                if (! is_wp_error( $product_terms ) && $product_terms) {
                        
                    if (function_exists('et_render_vehicles_table')) {
                        echo '<div class="single-product-vehicles">';
                            echo '<div class="compatible-vehicles-title">';
                                echo '<h2>'.esc_html__("Compatible vehicles","mobex").'</h2>';
                                echo '<input type="text" / placeholder="'.esc_attr__("Search for vehicle","mobex").'">';
                            echo '</div>';
                            echo '<div class="table-wrapper"><table class="table-sort">';
                                echo et_render_vehicles_table($product->get_id(),true,false);
                            echo '</table></div>';
                        echo '</div>';
                    }

                }
                    
            }

            add_action( 'woocommerce_after_single_product_summary', 'mobex_enovathemes_single_product_compare', 10 );
            function mobex_enovathemes_single_product_compare() {?>

                <?php
                    $compare_ids = get_post_meta( get_the_ID(), 'compare_ids', true );
                ?>

                <?php if ($compare_ids && function_exists('compare_products_fetch')): ?>
                    <?php
                        array_unshift($compare_ids, get_the_ID());
                        $compare_ids = implode(',', $compare_ids);
                    ?>
                    <div class="compare-products">
                        <h4><?php echo esc_html__('Compare products','mobex'); ?></h4>
                        <div class="single-product-cbt" data-sidebar="false"><?php compare_products_fetch($compare_ids); ?></div>
                    </div>
                <?php endif ?>

            <?php }
        
            

            add_action( 'woocommerce_after_single_product_summary', 'mobex_enovathemes_rating_count', 50 );
            function mobex_enovathemes_rating_count() {?>

                <div class="single-product-reviews-wrap">


                    <?php

                        if ( post_type_supports( 'product', 'comments' ) && get_option( 'woocommerce_enable_reviews' ) === "yes") {

                            global $product;

                            $rating       = array();
                            $rating_total = $product->get_review_count();

                            if ($rating_total && wc_review_ratings_enabled()) {

                            for ($i=1; $i <= 5; $i++) { 
                                $rating[$i] = $product->get_rating_count($i);
                            }

                            $rating_1 = ($rating[1]) ? $rating[1] : 0;
                            $rating_2 = ($rating[2]) ? $rating[2] : 0;
                            $rating_3 = ($rating[3]) ? $rating[3] : 0;
                            $rating_4 = ($rating[4]) ? $rating[4] : 0;
                            $rating_5 = ($rating[5]) ? $rating[5] : 0;

                            $rating_1_percent = absint(100*$rating_1/$rating_total);
                            $rating_2_percent = absint(100*$rating_2/$rating_total);
                            $rating_3_percent = absint(100*$rating_3/$rating_total);
                            $rating_4_percent = absint(100*$rating_4/$rating_total);
                            $rating_5_percent = absint(100*$rating_5/$rating_total);


                    ?>

                        <div class="rating-bars">

                            <div class="rating-info-wrap">

                                <h4><?php echo esc_html__('Customer reviews','mobex') ?></h4>
                                <div class="rating-count">
                                    <?php wc_get_template( 'single-product/rating.php' ); echo '<span>'.round($product->get_average_rating(),2).' '.esc_html__('out of 5 Stars','mobex').'</span>'; ?> 
                                </div>

                            </div>

                            <div class="rating-bars-wrap">

                                <div class="et-progress" data-delay="0" data-percentage="<?php echo esc_attr($rating_5_percent); ?>">
                                    <div class="text"><?php echo esc_html__('5 Stars','mobex') ?></div>
                                    <div class="track-bar">
                                        <div class="bar" style="width: <?php echo esc_attr($rating_5_percent); ?>%" data-percent="<?php echo esc_attr($rating_5_percent); ?>"></div>
                                        <div class="track"></div>
                                    </div>
                                    <span class="count"><?php echo esc_html($rating_5); ?></span>
                                </div>

                                <div class="et-progress" data-delay="0" data-percentage="<?php echo esc_attr($rating_4_percent); ?>">
                                    <div class="text"><?php echo esc_html__('4 Stars','mobex') ?></div>
                                    <div class="track-bar">
                                        <div class="bar" style="width: <?php echo esc_attr($rating_4_percent); ?>%" data-percent="<?php echo esc_attr($rating_4_percent); ?>"></div>
                                        <div class="track"></div>
                                    </div>
                                    <span class="count"><?php echo esc_html($rating_4); ?></span>
                                </div>

                                <div class="et-progress" data-delay="0" data-percentage="<?php echo esc_attr($rating_3_percent); ?>">
                                    <div class="text"><?php echo esc_html__('3 Stars','mobex') ?></div>
                                    <div class="track-bar">
                                        <div class="bar" style="width: <?php echo esc_attr($rating_3_percent); ?>%" data-percent="<?php echo esc_attr($rating_3_percent); ?>"></div>
                                        <div class="track"></div>
                                    </div>
                                    <span class="count"><?php echo esc_html($rating_3); ?></span>
                                </div>

                                <div class="et-progress" data-delay="0" data-percentage="<?php echo esc_attr($rating_2_percent); ?>">
                                    <div class="text"><?php echo esc_html__('2 Stars','mobex') ?></div>
                                    <div class="track-bar">
                                        <div class="bar" style="width: <?php echo esc_attr($rating_2_percent); ?>%" data-percent="<?php echo esc_attr($rating_2_percent); ?>"></div>
                                        <div class="track"></div>
                                    </div>
                                    <span class="count"><?php echo esc_html($rating_2); ?></span>
                                </div>

                                <div class="et-progress" data-delay="0" data-percentage="<?php echo esc_attr($rating_1_percent); ?>">
                                    <div class="text"><?php echo esc_html__('1 Star','mobex') ?></div>
                                    <div class="track-bar">
                                        <div class="bar" style="width: <?php echo esc_attr($rating_1_percent); ?>%" data-percent="<?php echo esc_attr($rating_1_percent); ?>"></div>
                                        <div class="track"></div>
                                    </div>
                                    <span class="count"><?php echo esc_html($rating_1); ?></span>
                                </div>

                                <a class="et-button small write-review" href="#review_form_wrapper"><?php echo esc_html__("Write a review","mobex"); ?></a>

                            </div>

                        </div>

                    <?php } }

            }

                add_action( 'woocommerce_after_single_product_summary', 'comments_template', 50 );

            add_action( 'woocommerce_after_single_product_summary', 'mobex_enovathemes_rating_end', 50 );
            function mobex_enovathemes_rating_end(){ ?>
                </div>
            <?php }

            remove_action( 'woocommerce_review_before', 'woocommerce_review_display_gravatar', 10 );
            add_action( 'woocommerce_review_before', 'mobex_enovathemes_woocommerce_review_display_gravatar', 10 );
            function mobex_enovathemes_woocommerce_review_display_gravatar( $comment ) {
                echo get_avatar( $comment, apply_filters( 'woocommerce_review_gravatar_size', '72' ), '' );
            }


            add_action('woocommerce_after_single_product_summary','mobex_enovathemes_woocommerce_faq',50);
            function mobex_enovathemes_woocommerce_faq(){
                global $product;

                $faq = get_post_meta($product->get_id(),'faq',true);

                if ($faq) { ?>

                    <div class="product-faq">

                        <h4><?php echo esc_html__("Questions and Answers","mobex"); ?></h4>

                        <div class="et-accordion collapsible-true">

                            <?php foreach ($faq as $key => $opt) { ?>
                                <div class="accordion-title"><?php echo esc_html($opt['title']); ?></div>
                                <div class="accordion-content"><?php echo wp_kses_post($opt['value']) ?></div>
                            <?php } ?>

                        </div>
                        <br>
                        <p><?php echo esc_html__("Still have questions?","mobex"); ?></p>
                        <a class="product-ask-toggle et-button small ask-toggle" href="#"><?php echo esc_html__("Ask a question","mobex"); ?></a>
                    </div>

                <?php }

            }

            add_action( 'woocommerce_after_single_product', 'mobex_enovathemes_woocommerce_after_single_product');
            function mobex_enovathemes_woocommerce_after_single_product() {?>
                <div class="et-clearfix">
                    <?php mobex_enovathemes_post_nav('product',get_the_ID()); ?>
                </div>
            <?php }

            remove_action( 'woocommerce_after_single_product_summary', 'woocommerce_upsell_display', 15 );
            add_action( 'woocommerce_after_single_product_summary', 'woocommerce_upsell_display', 50 );

            add_action( 'woocommerce_after_single_product_summary', 'mobex_enovathemes_woocommerce_after_single_product_history',50);
            function mobex_enovathemes_woocommerce_after_single_product_history(){ global $product;


                if (isset($_COOKIE["woocommerce_recently_viewed"]) && !empty($_COOKIE["woocommerce_recently_viewed"])) {

                    $output = '';

                    $ids       = explode('|', $_COOKIE["woocommerce_recently_viewed"]);
                    $result    = array_diff($ids, [$product->get_id()]);
                    $reindexed = array_values($result);

                    $query_options = array(
                        'post_type'      => 'product',
                        'posts_per_page' => 10,
                        'post__in'       => $reindexed,
                        'tax_query'      => array(
                            array(
                                'taxonomy'  => 'product_visibility',
                                'terms'     => array( 'exclude-from-catalog' ),
                                'field'     => 'name',
                                'operator'  => 'NOT IN'
                            )
                        )
                    );

                    $history_query = new WP_Query($query_options);

                    if($history_query->have_posts()){

                        $class      = array();
                        $list_class = array();
                        $attributes = array();

                        $list_class[] = 'loop-posts';
                        $list_class[] = 'loop-products';
                        $list_class[] = 'products';
                        $list_class[] = 'history-products';

                        $class[] = 'et-woo-products';
                        $class[] = 'only';
                        $class[] = 'post-layout';
                        $class[] = 'grid';
                        $class[] = 'history-products';

                        $attributes[] = 'class="'.esc_attr(implode(' ', $class)).'"';

                        $output .= '<div class="history-products-wrapper">';

                            $output .= '<h4>'.esc_html__("Recently viewed products","mobex").'</h4>';

                            $output .= '<div '.implode(' ', $attributes).'>';
                                $output .= '<ul class="'.esc_attr(implode(' ', $list_class)).'">';

                                    while ($history_query->have_posts() ) {
                                        $history_query->the_post();

                                        global $product;

                                        $output .= '<li data-product="'.esc_attr($product->get_id()).'" class="post product" id="product-'.esc_attr($product->get_id()).'">';

                                            $output .='<div class="post-inner et-item-inner">';
                                                if(get_option( 'woocommerce_enable_ajax_add_to_cart' ) === "yes"){
                                                    $output .='<div class="ajax-add-to-cart-loading">';
                                                        $output .='<svg viewBox="0 0 56 56"><circle class="loader-path" cx="28" cy="28" r="20" /></svg>';
                                                        $output .= '<svg viewBox="0 0 511.999 511.999" class="tick"><path d="M506.231 75.508c-7.689-7.69-20.158-7.69-27.849 0l-319.21 319.211L33.617 269.163c-7.689-7.691-20.158-7.691-27.849 0-7.69 7.69-7.69 20.158 0 27.849l139.481 139.481c7.687 7.687 20.16 7.689 27.849 0l333.133-333.136c7.69-7.691 7.69-20.159 0-27.849z"/></svg>';
                                                    $output .='</div>';
                                                }
                                                $output .= mobex_enovathemes_loop_product_thumbnail('grid',false);
                                                $output .= mobex_enovathemes_loop_product_title('grid');
                                                $output .= mobex_enovathemes_loop_product_inner_close('grid');
                                            $output .='</div>';
                                            
                                        $output .= '</li>';

                                    }

                                    wp_reset_postdata();

                                $output .= '</ul>';
                            $output .= '</div>';

                        $output .= '</div>';

                        wp_reset_postdata();

                    }

                    if (!empty($output)) {
                        echo mobex_enovathemes_output_html($output);
                    }

                }
            }

            add_filter( 'woocommerce_output_related_products_args', 'mobex_enovathemes_related_products_args', 20 );
            function mobex_enovathemes_related_products_args( $args ) {
                $args['posts_per_page'] = 6;
                return $args;
            }

            function mobex_enovathemes_single_product_sale_flash() {
                global $product;
                if($product->is_on_sale()) {
                    echo '<span class="onsale">' .esc_html__("Sale","mobex").'</span>';
                }

                $output ='';

                $mobex_enovathemes_label1 = get_post_meta($product->get_id(),'mobex_enovathemes_label1',true);
                $mobex_enovathemes_label2 = get_post_meta($product->get_id(),'mobex_enovathemes_label2',true);

                if (isset($mobex_enovathemes_label1) && !empty($mobex_enovathemes_label1)) {
                    $mobex_enovathemes_label1_color = get_post_meta($product->get_id(),'mobex_enovathemes_label1_color',true);

                    $style = '';

                    if (isset($mobex_enovathemes_label1_color) && !empty($mobex_enovathemes_label1_color)) {
                        $style = 'style="background:'.$mobex_enovathemes_label1_color.';';
                        $style .='"';
                    }

                     $output.='<span class="label" '.$style.'>' . esc_html($mobex_enovathemes_label1) . '</span>';

                }

                if (isset($mobex_enovathemes_label2) && !empty($mobex_enovathemes_label2)) {
                    $mobex_enovathemes_label2_color = get_post_meta($product->get_id(),'mobex_enovathemes_label2_color',true);

                    $style = '';

                    if (isset($mobex_enovathemes_label2_color) && !empty($mobex_enovathemes_label2_color)) {
                        $style = 'style="background:'.$mobex_enovathemes_label2_color.';';
                        $style .='"';
                    }

                    $output.='<span class="label" '.$style.'>' . esc_html($mobex_enovathemes_label2) . '</span>';

                }


                if (!empty($output)) {
                    echo mobex_enovathemes_output_html($output);
                }

            }
            remove_action( 'woocommerce_before_single_product_summary', 'woocommerce_show_product_sale_flash', 10 );
            add_filter( 'woocommerce_before_single_product_summary', 'mobex_enovathemes_single_product_sale_flash', 15);

            add_action('wp_footer','mobex_enovathemes_product_quick_ask');
            function mobex_enovathemes_product_quick_ask(){
                if (is_singular('product')) {

                    $product_ask_form = get_theme_mod('product_ask_form');

                    if (
                        shortcode_exists('contact-form-7') && 
                        isset($product_ask_form) && !empty($product_ask_form)
                    ) {
                        echo '<div class="ask-form"><span class="ask-close"></span>'.do_shortcode('[contact-form-7 id="'.$product_ask_form.'"]').'</div><div class="ask-after"></div>';
                    }
                }
            }

        /* Cart
        ---------------*/ 

            remove_action( 'woocommerce_cart_collaterals', 'woocommerce_cross_sell_display' );
            add_action( 'woocommerce_after_cart', 'woocommerce_cross_sell_display' );

        /* Single product admin tabs
        ---------------*/

            add_filter( 'woocommerce_product_data_tabs', 'mobex_enovathemes_labels_tab', 10, 1 );

            function mobex_enovathemes_labels_tab( $default_tabs ) {
                $default_tabs['labels_tab'] = array(
                    'label'   =>  esc_html__( 'Labels', 'mobex' ),
                    'target'  =>  'mobex_enovathemes_labels_tab_data',
                    'priority' => 60,
                    'class'   => array()
                );
                return $default_tabs;
            }

            add_action( 'woocommerce_product_data_panels', 'mobex_enovathemes_labels_tab_data' );
            function mobex_enovathemes_labels_tab_data() { ?>
               <div id="mobex_enovathemes_labels_tab_data" class="panel woocommerce_options_panel">
                   <?php

                    woocommerce_wp_text_input([
                        'id' => 'mobex_enovathemes_label1',
                        'label' => esc_html__('Label 1', 'mobex'),
                    ]);

                    woocommerce_wp_text_input([
                        'id' => 'mobex_enovathemes_label1_color',
                        'label' => esc_html__('Label 1 color code in hex', 'mobex'),
                    ]);

                    woocommerce_wp_text_input([
                        'id' => 'mobex_enovathemes_label2',
                        'label' => esc_html__('Label 2', 'mobex'),
                    ]);

                    woocommerce_wp_text_input([
                        'id' => 'mobex_enovathemes_label2_color',
                        'label' => esc_html__('Label 2 color code in hex', 'mobex'),
                    ]);

                   ?>
               </div>
            <?php }

            function mobex_enovathemes_fbt() { global $post; ?>
                <div class="options_group">
                    <p class="form-field selection-choice-custom">
                        <label for="fbt_ids"><?php esc_html_e( 'Frequently bought', 'mobex' ); ?></label>
                        <select class="wc-product-search" multiple="multiple" style="width: 50%;" id="fbt_ids" name="fbt_ids[]" data-placeholder="<?php esc_attr_e( 'Search for a product&hellip;', 'mobex' ); ?>" data-action="woocommerce_json_search_products_and_variations" data-exclude="<?php echo intval( $post->ID ); ?>">
                            <?php

                                $fbt_ids = get_post_meta( $post->ID, 'fbt_ids', true );
                                $product_ids = isset( $fbt_ids ) ? array_map( 'intval', (array) wp_unslash( $fbt_ids ) ) : array();
                                if (!empty($product_ids)) {
                                    foreach ( $product_ids as $product_id ) {
                                        $product = wc_get_product( $product_id );
                                        if ( is_object( $product ) ) {
                                            echo '<option value="' . esc_attr( $product_id ) . '"' . selected( true, true, false ) . '>' . esc_html( wp_kses_post( $product->get_formatted_name() ) ) . '</option>';
                                        }
                                    }
                                }
                                
                            ?>
                        </select> <?php echo wc_help_tip( __( 'Frequently bought are products which you recommend with the currently viewed product.', 'mobex' ) ); // WPCS: XSS ok. ?>
                    </p>
            <?php }
            add_action( 'woocommerce_product_options_related', 'mobex_enovathemes_fbt' );

            function mobex_enovathemes_ss() { global $post; ?>
                    <p class="form-field selection-choice-custom">
                        <label for="ss_ids"><?php esc_html_e( 'Supersession', 'mobex' ); ?></label>
                        <select class="wc-product-search" multiple="multiple" style="width: 50%;" id="ss_ids" name="ss_ids[]" data-placeholder="<?php esc_attr_e( 'Search for a product&hellip;', 'mobex' ); ?>" data-action="woocommerce_json_search_products_and_variations" data-exclude="<?php echo intval( $post->ID ); ?>">
                            <?php

                                $ss_ids = get_post_meta( $post->ID, 'ss_ids', true );
                                $product_ids = isset( $ss_ids ) ? array_map( 'intval', (array) wp_unslash( $ss_ids ) ) : array();
                                if (!empty($product_ids)) {
                                    foreach ( $product_ids as $product_id ) {
                                        $product = wc_get_product( $product_id );
                                        if ( is_object( $product ) ) {
                                            echo '<option value="' . esc_attr( $product_id ) . '"' . selected( true, true, false ) . '>' . esc_html( wp_kses_post( $product->get_formatted_name() ) ) . '</option>';
                                        }
                                    }
                                }
                                
                            ?>
                        </select> <?php echo wc_help_tip( __( 'Frequently bought are products which you recommend with the currently viewed product.', 'mobex' ) ); // WPCS: XSS ok. ?>
                    </p>
            <?php }
            add_action( 'woocommerce_product_options_related', 'mobex_enovathemes_ss' );

            function mobex_enovathemes_compare() { global $post; ?>
                    <p class="form-field selection-choice-custom">
                        <label for="compare_ids"><?php esc_html_e( 'Compare', 'mobex' ); ?></label>
                        <select class="wc-product-search" multiple="multiple" style="width: 50%;" id="compare_ids" name="compare_ids[]" data-placeholder="<?php esc_attr_e( 'Search for a product&hellip;', 'mobex' ); ?>" data-action="woocommerce_json_search_products_and_variations" data-exclude="<?php echo intval( $post->ID ); ?>">
                            <?php

                                $compare_ids = get_post_meta( $post->ID, 'compare_ids', true );
                                $product_ids = isset( $compare_ids ) ? array_map( 'intval', (array) wp_unslash( $compare_ids ) ) : array();
                                if (!empty($product_ids)) {
                                    foreach ( $product_ids as $product_id ) {
                                        $product = wc_get_product( $product_id );
                                        if ( is_object( $product ) ) {
                                            echo '<option value="' . esc_attr( $product_id ) . '"' . selected( true, true, false ) . '>' . esc_html( wp_kses_post( $product->get_formatted_name() ) ) . '</option>';
                                        }
                                    }
                                }
                                
                            ?>
                        </select> <?php echo wc_help_tip( __( 'Compare are products which you recommend comapred to the currently viewed product.', 'mobex' ) ); // WPCS: XSS ok. ?>
                    </p>
                </div>
            <?php }
            add_action( 'woocommerce_product_options_related', 'mobex_enovathemes_compare' );
        
        /* Recently veiwed produts
        ---------------*/

            function mobex_enovathemes_custom_track_product_view() {
                if ( ! is_singular( 'product' ) ) {
                    return;
                }

                global $post;

                if ( empty( $_COOKIE['woocommerce_recently_viewed'] ) ){
                    $viewed_products = array();
                }
                else{
                    $viewed_products = (array) explode( '|', $_COOKIE['woocommerce_recently_viewed'] );
                }

                if ( ! in_array( $post->ID, $viewed_products ) ) {
                    $viewed_products[] = $post->ID;
                }

                if ( sizeof( $viewed_products ) > 18 ) {
                    array_shift( $viewed_products );
                }

                // Store for session only
                wc_setcookie( 'woocommerce_recently_viewed', implode( '|', $viewed_products ) );
            }

            add_action( 'template_redirect', 'mobex_enovathemes_custom_track_product_view', 20 );
    
        /* Quick view
        ---------------*/

            function mobex_enovathemes_quick_view($id) {

                $currency = isset($_POST['currency']) ? sanitize_text_field($_POST['currency']) : '';
                $rate     = $currency ? (float) et__get_currency_rate($currency) : 1.0;
                ?>
                <?php if (isset($_POST["id"]) && !empty($_POST["id"])): ?>
                    <?php setup_postdata( $_POST["id"] ); ?>
                    <div class="qwc layout1">
                        <div class="quick-view-wrapper loaded woocommerce">
                            <div class="quick-view-wrapper-close"></div>
                            <?php
                            $args  = array(
                                'post_type' => 'product',
                                'p'         => absint($_POST["id"]),
                            );
                            $query = new WP_Query( $args );

                            // === TEMP FILTERS (apply only during this render) ===
                            $convert_cb = function($price) use ($rate) {
                                return ( $rate && $rate !== 1.0 && is_numeric($price) ) ? (float)$price * $rate : $price;
                            };
                            $currency_cb = function() use ($currency) {
                                return $currency ?: get_woocommerce_currency();
                            };
                            $hash_cb = function($hash, $product, $for_display) use ($currency, $rate) {
                                // ensure variation min/max caches are unique per currency/rate
                                $hash['mobex_currency'] = $currency ?: 'BASE';
                                $hash['mobex_rate']     = $rate ?: 1.0;
                                return $hash;
                            };

                            if ( $rate && $rate !== 1.0 ) {
                                add_filter('woocommerce_product_get_price',         $convert_cb, 9999, 1);
                                add_filter('woocommerce_product_get_regular_price', $convert_cb, 9999, 1);
                                add_filter('woocommerce_product_get_sale_price',    $convert_cb, 9999, 1);
                                add_filter('woocommerce_get_variation_prices_hash', $hash_cb,    9999, 3);
                            }
                            if ( $currency ) {
                                add_filter('woocommerce_currency', $currency_cb, 9999);
                            }

                            if ($query->have_posts()){
                                while ($query->have_posts()) : $query->the_post(); ?>

                                    <!-- DO NOT override woocommerce_get_price_html here -->
                                    <div id="product-<?php the_ID(); ?>" <?php wc_product_class( '', get_the_ID() ); ?>>
                                        <?php do_action( 'woocommerce_before_single_product_summary' ); ?>
                                        <div class="summary entry-summary">
                                            <?php
                                            // Ensure title shows in modal (some themes remove it when ! is_product())
                                            add_action('woocommerce_single_product_summary', 'woocommerce_template_single_title', 5);
                                            do_action( 'woocommerce_single_product_summary' );
                                            remove_action('woocommerce_single_product_summary', 'woocommerce_template_single_title', 5);
                                            ?>
                                        </div>
                                    </div>

                                <?php endwhile;
                            } else {
                                echo esc_html__("No product found","mobex");
                            }

                            // === CLEAN UP TEMP FILTERS so nothing leaks ===
                            if ( $rate && $rate !== 1.0 ) {
                                remove_filter('woocommerce_product_get_price',         $convert_cb, 9999);
                                remove_filter('woocommerce_product_get_regular_price', $convert_cb, 9999);
                                remove_filter('woocommerce_product_get_sale_price',    $convert_cb, 9999);
                                remove_filter('woocommerce_get_variation_prices_hash', $hash_cb,    9999);
                            }
                            if ( $currency ) {
                                remove_filter('woocommerce_currency', $currency_cb, 9999);
                            }

                            wp_reset_postdata();
                            ?>
                        </div>
                    </div>
                    <div class="quick-view-wrapper-after"></div>

                    <script type="text/javascript">
                    jQuery(function($){
                        // Re-initialize variation logic only inside the modal
                        if (typeof wc_add_to_cart_variation_params !== 'undefined') {
                            var $forms = $('.quick-view-wrapper').find('form.variations_form');
                            $forms.each(function(){
                                var $f = $(this);
                                $f.wc_variation_form();
                                $f.find('.variations select').trigger('change'); // evaluate immediately
                            });
                        }
                    });
                    </script>
                <?php endif; ?>

                <?php die();
            }
            add_action( 'wp_ajax_quick_view', 'mobex_enovathemes_quick_view' );
            add_action( 'wp_ajax_nopriv_quick_view', 'mobex_enovathemes_quick_view' );

    }

/* Scripts/Styles
---------------*/

    function mobex_enovathemes_scripts_styles_general() {

        $main_typography = get_theme_mod('main_typography');
        $headings_typography = get_theme_mod('headings_typography');

        if (!defined('ENOVATHEMES_ADDONS') ) {
            wp_enqueue_style( 'mobex-default-font', MOBEX_ENOVATHEMES_TEMPPATH . '/css/default-font.css' );
            wp_enqueue_style('mobex-default-styles', get_template_directory_uri() . '/css/default-styles.css');
        } else{

            $main_typography     = get_theme_mod('main_typography');
            $headings_typography = get_theme_mod('headings_typography');

            if(
                (!isset($main_typography['font-family']) || empty($main_typography['font-family'])) ||
                (!isset($headings_typography['font-family']) || empty($headings_typography['font-family']))
            ){
                wp_enqueue_style( 'mobex-default-font', MOBEX_ENOVATHEMES_TEMPPATH . '/css/default-font.css' );
            }

        }
        wp_enqueue_style('mobex-swiper-no-js', get_template_directory_uri() . '/css/swiper-no-js.css' ,'',wp_get_theme()->get('Version'));
        wp_enqueue_style('mobex-style', get_stylesheet_uri(), '', wp_get_theme()->get('Version'));

        if (isset($_GET['d']) && $_GET['d'] == "rtl") {
            wp_enqueue_style('mobex-rtl', get_template_directory_uri() . '/rtl.css', '', wp_get_theme()->get('Version'));
        }


        if ( is_singular() && get_option( 'thread_comments' ) ) {
            wp_enqueue_script( 'comment-reply' );
        }

        

        // dequeue
        wp_dequeue_style( 'woocommerce_prettyPhoto_css' );
        wp_deregister_style( 'woocommerce_prettyPhoto_css' );

    }

    function mobex_enovathemes_scripts() {

        global $wp_query;

        $modes        = et_get_theme_mods();
        $blog_layout  = isset($modes['blog_layout']) ? $modes['blog_layout'] : 'masonry';

        if (empty($blog_layout)) {
            $blog_layout = 'masonry';
        }

        if ($blog_layout == 'masonry') {
            wp_enqueue_script( 'imagesloaded');
            wp_enqueue_script( 'jquery-masonry');
        }


        if (defined('ENOVATHEMES_ADDONS')) {
            wp_enqueue_script( 'plugins-combined', MOBEX_ENOVATHEMES_TEMPPATH . '/js/plugins-combined.js', array('jquery'), '', true);
        } else {
            wp_enqueue_script( 'mobex-gsap', MOBEX_ENOVATHEMES_TEMPPATH . '/js/gsap.min.js', array('jquery'), '', true);
            wp_enqueue_script( 'mobex-morph-sv-gplugin', MOBEX_ENOVATHEMES_TEMPPATH . '/js/MorphSVGPlugin.min.js', array('jquery'), '', true);
            wp_enqueue_script( 'mobex-split-text', MOBEX_ENOVATHEMES_TEMPPATH . '/js/SplitText.min.js', array('jquery'), '', true);
            wp_enqueue_script( 'mobex-scroll-to', MOBEX_ENOVATHEMES_TEMPPATH . '/js/ScrollToPlugin.min.js', array('jquery'), '', true);
            wp_enqueue_script( 'mobex-swiper', MOBEX_ENOVATHEMES_TEMPPATH . '/js/swiper.min.js', array('jquery'), '', true);
            wp_enqueue_script( 'mobex-waypoints', MOBEX_ENOVATHEMES_TEMPPATH . '/js/waypoints.min.js', array('jquery'), '', true);
            wp_enqueue_script( 'mobex-cookie', MOBEX_ENOVATHEMES_TEMPPATH . '/js/cookie.js', array('jquery'), '', true);
            wp_enqueue_script( 'mobex-select2', MOBEX_ENOVATHEMES_TEMPPATH . '/js/select2.js', array('jquery'), '', true);
            wp_enqueue_script( 'mobex-countdown', MOBEX_ENOVATHEMES_TEMPPATH . '/js/countdown.js', array('jquery'), '', true);
        }

        if (defined('ELEMENTOR_VERSION') && (\Elementor\Plugin::$instance->editor->is_edit_mode() || \Elementor\Plugin::$instance->preview->is_preview_mode())) {
            wp_enqueue_script( 'elementor-extended', MOBEX_ENOVATHEMES_TEMPPATH . '/js/elementor-extended.js', array('jquery'), '', true);
        }

        if (!is_admin()) {

            wp_enqueue_script( 'controller', MOBEX_ENOVATHEMES_TEMPPATH . '/js/controller.js', array('jquery','mobex-fuse'), wp_get_theme()->get('Version'), true);

            $product_per_page = get_theme_mod('product_number');

            if (empty($product_per_page)) {
                $product_per_page = get_option( 'posts_per_page' );
            }

            $post_paged                    = (get_query_var('page')) ? get_query_var('page') : 1;
            $post_max                      = $wp_query->max_num_pages;
            $product_max                   = (empty($product_per_page)) ? $wp_query->max_num_pages : ceil($wp_query->found_posts/$product_per_page);
            $product_ajax_search_threshold = $modes && isset($modes['product_ajax_search_threshold']) && !empty($mods['product_ajax_search_threshold']) ? $modes['product_ajax_search_threshold'] : 0.1;

            $wishlist  = (!empty(get_theme_mod('product_wishlist'))) ? "true" : "false";
            $compare   = (!empty(get_theme_mod('product_compare'))) ? "true" : "false";
            $quickview = (!empty(get_theme_mod('product_quick_view'))) ? "true" : "false";

            $vehicle_params = apply_filters( 'vehicle_params','');

            wp_localize_script(
                'controller',
                'controller_opt',
                array(
                    'lang'           => (is_rtl() ? 'rtl' : 'ltr'),
                    'currency'       => (defined('YAY_CURRENCY_FILE') && class_exists('Yay_Currency\Helpers\YayCurrencyHelper')) || (function_exists('wcml_get_currency') && function_exists('wcml_get_exchange_rate')) ? get_woocommerce_currency() : "",
                    'adminAJAXError' => esc_html__("Something went wrong, please contact the developer", 'mobex'),
                    'noVehicles'     => esc_html__("No results, try a different search", 'mobex'),
                    'vehiclesAssign' => esc_html__("Updated product vehicles", 'mobex'),
                    'vehicleReset'   => esc_html__("Reset", 'mobex'),
                    'mismatched'     => esc_html__("Does not fit your","mobex"),
                    'inWishlist'     => esc_html__("Added to wishlist","mobex"),
                    'inCompare'      => esc_html__("Added to compare","mobex"),
                    'postMax'        => $post_max,
                    'productMax'     => $product_max,
                    'start'          => $post_paged,
                    'postNextLink'   => next_posts($post_max, false),
                    'productNextLink'=> next_posts($product_max, false),
                    'wooError'       => esc_html__("No products found, something was wrong", 'mobex'),
                    'postError'      => esc_html__("No posts found, something was wrong", 'mobex'),
                    'noMore'         => esc_html__("No more", 'mobex'),
                    'noProduct'      => esc_html__( 'No products found', 'mobex' ),
                    'allAdded'       => esc_html__("All items added", 'mobex'),
                    'filterText'     => esc_html__("Choose category", 'mobex'),
                    'already'        => esc_html__("Product already added", 'mobex'),
                    'noLanguage'     => esc_html__("You can configure languages on you site using WPML or Polyland plugins. Theme supports both!", 'mobex'),
                    'ajaxUrl'        => admin_url('admin-ajax.php'),
                    'vehicleParams'  => json_encode($vehicle_params),
                    'threshold'      => $product_ajax_search_threshold,
                    'error'          => esc_html__("Something was wrong, please try later or contact site administrator","mobex"),
                    'SKU'            => esc_html__("SKU", 'mobex'),
                )
            );

            if (class_exists('Woocommerce')) {

                wp_enqueue_script( 'wc-cart-fragments');
                wp_enqueue_script( 'wc-add-to-cart-variation' );
                wp_enqueue_script( 'wc-single-product' );

                wp_dequeue_style('wc-blocks-style-cart');
                wp_deregister_style('wc-blocks-style-cart');
                wp_dequeue_style('wc-blocks-style-checkout');
                wp_deregister_style('wc-blocks-style-checkout');
                wp_dequeue_style('wc-blocks-style-all-products');
                wp_deregister_style('wc-blocks-style-all-products');
                wp_dequeue_style('wc-blocks-packages-style');
                wp_deregister_style('wc-blocks-packages-style');

                wp_enqueue_script( 'mobex-fuse', MOBEX_ENOVATHEMES_TEMPPATH . '/js/fuse.min.js', [], '', true);

                if ($wishlist == "true") {

                    wp_localize_script(
                        'controller',
                        'wish_opt',
                        array(
                            'ajaxPost'       => admin_url('admin-post.php'),
                            'shopName'       => sanitize_title_with_dashes(sanitize_title_with_dashes(get_bloginfo('name'))),
                            'inWishlist'     => esc_html__("Added to wishlist","mobex"),
                            'addedWishlist'  => esc_html__("In wishlist","mobex"),
                            'error'          => esc_html__("Something went wrong, could not add to wishlist","mobex"),
                            'noWishlist'     => esc_html__("No products found","mobex"),
                            'confirm'        => esc_html__("Remove the item from wishlist?","mobex"),
                        )
                    );
                }

                if ($compare == "true") {

                    wp_localize_script(
                        'controller',
                        'comp_opt',
                        array(
                            'shopName'  => sanitize_title_with_dashes(sanitize_title_with_dashes(get_bloginfo('name'))),
                            'inCompare' => esc_html__("Added to compare","mobex"),
                            'addedCompare' => esc_html__("In compare","mobex"),
                            'error'     => esc_html__("Something went wrong, could not add to compare","mobex"),
                            'noCompare' => esc_html__("No products found","mobex"),
                            'confirm'   => esc_html__("Remove the item","mobex"),
                        )
                    );
                }

                if ($quickview == "true") {

                    wp_localize_script(
                        'controller',
                        'quickview_opt',
                        array(
                            'flexslider'                => apply_filters(
                                'woocommerce_single_product_carousel_options',
                                array(
                                    'rtl'            => is_rtl(),
                                    'animation'      => 'slide',
                                    'smoothHeight'   => true,
                                    'directionNav'   => false,
                                    'controlNav'     => 'thumbnails',
                                    'slideshow'      => false,
                                    'animationSpeed' => 500,
                                    'animationLoop'  => false, // Breaks photoswipe pagination if true.
                                    'allowOneSlide'  => false,
                                )
                            ),
                            'zoom_enabled'              => apply_filters( 'woocommerce_single_product_zoom_enabled', get_theme_support( 'wc-product-gallery-zoom' ) ),
                            'zoom_options'              => apply_filters( 'woocommerce_single_product_zoom_options', array() ),
                            'flexslider_enabled'        => apply_filters( 'woocommerce_single_product_flexslider_enabled', get_theme_support( 'wc-product-gallery-slider' ) ),
                            )
                    );
                }

            }

        }

    }


    function mobex_enovathemes_admin_scripts_styles() {

        global $pagenow, $post;

        wp_enqueue_style( 'wp-color-picker' );
        wp_enqueue_script( 'wp-color-picker' );
        wp_enqueue_script( 'jquery-ui-draggable' );
        wp_enqueue_script( 'jquery-ui-droppable' );

        if (( $pagenow == 'post.php' ) && ($post->post_type == 'product')) {
            wp_enqueue_style( 'select2', MOBEX_ENOVATHEMES_TEMPPATH . '/css/select2.css', false, '');
        }

        if (is_rtl()) {
            wp_enqueue_style( 'mobex-admin', MOBEX_ENOVATHEMES_TEMPPATH . '/css/rtl-admin.css', false, '');
        } else {
            wp_enqueue_style( 'mobex-admin', MOBEX_ENOVATHEMES_TEMPPATH . '/css/admin.css', false, '');
        }

        wp_enqueue_script( 'mobex-admin', MOBEX_ENOVATHEMES_TEMPPATH . '/js/admin.js', array('jquery'), '', true);

        $post_paged       = (get_query_var('page')) ? get_query_var('page') : 1;

        $categories = (function_exists('get_product_categories_hierarchy')) ? get_product_categories_hierarchy(true) : '';

        $category_output = '';

        if (!empty($categories) && !is_wp_error($categories)){
            $category_output .= list_taxonomy_hierarchy_no_instance($categories,'','default');
        }

        $filter_text = array(
            'limit'         => esc_html__( 'Limit to category', 'mobex' ),
            'hide'          => esc_html__( 'Hide on category', 'mobex' ),
            'include'       => esc_html__( 'Include child categories?', 'mobex' ),
            'all'           => esc_html__( 'All', 'mobex' ),
            'category'      => esc_html__( 'Include child categories?', 'mobex' ),
            'remove'        => esc_html__( 'Remove', 'mobex' ),
            'display'       => esc_html__( 'Display type', 'mobex' ),
            'select'        => esc_html__( 'Select', 'mobex' ),
            'list'          => esc_html__( 'List', 'mobex' ),
            'image'         => esc_html__( 'Image', 'mobex' ),
            'image-list'    => esc_html__( 'Image list', 'mobex' ),
            'label'         => esc_html__( 'Label', 'mobex' ),
            'color'         => esc_html__( 'Color', 'mobex' ),
            'lock'          => esc_html__( 'Lock this attribute?', 'mobex' ),
            'lock-desk'     => esc_html__( 'If active, filter results will not affect attribute data', 'mobex' ),
            'slider'        => esc_html__( 'Slider', 'mobex' ),
            'columns'       => esc_html__( 'Columns', 'mobex' ),
            'desc1'         => esc_html__( "For color, image display types make sure you set the correct type from this attribute settings, found under products / attributes. For slider display types, make sure your attribute is numeric", "mobex" ),
            'desc2'         => esc_html__( "For image display type make sure you set the product category image from the Products / Categories", "mobex" ),
        );

        wp_localize_script(
            'mobex-admin',
            'admin_opt',
            array(
                'start'          => $post_paged,
                'noMore'         => esc_html__("No more", 'mobex'),
                'csvError'       => esc_html__("Please select CSV file", 'mobex'),
                'vehicleMapNonce' => wp_create_nonce('vehicle-map'),
                'mapError'       => esc_html__("Please map atleast one column", 'mobex'),
                'inactiveProductVehicle' => esc_html__("To assign vehicles to a product, you must first save the product.", 'mobex'),
                'adminAJAXError' => esc_html__("Something went wrong, please contact the developer", 'mobex'),
                'noVehicles'     => esc_html__("No results, try a different search", 'mobex'),
                'vehicleSearch'  => esc_html__("Vehicle search", 'mobex'),
                'vehiclesAssign' => esc_html__("Updated product vehicles", 'mobex'),
                'importTitle'    => esc_html__("Importing vehicle data...", 'mobex'),
                'vehicleReset'   => esc_html__("Reset", 'mobex'),
                'BulkVehicleAssign' => esc_html__("Assign vehicles", 'mobex'),
                'BulkVehicleAssigned' => esc_html__("Vehicles assigned successfully!", 'mobex'),
                'importComplete' => esc_html__("Importing complete!", 'mobex'),
                'importDescription' => esc_html__("Process can take a couple of minutes, don't close the tab, wait for message", 'mobex'),
                'filterText'     => json_encode($filter_text),
                'ajaxUrl'        => admin_url('admin-ajax.php'),
                'categories'     => $category_output,
                'adminAjaxError' => esc_html__("Something went wrong, please contact the developer", 'mobex'),
                'adminAjax'      => admin_url('admin-ajax.php'),
                'indexLabel'     => esc_html__("Indexing...", 'mobex'),
                'productIndexNonce' => wp_create_nonce('et-woo-product-index'),
                'reindexLabel'   => esc_html__("Re-index products", 'mobex'),
                'saving'   => esc_html__("Saving...", 'mobex')
            )
        );

    }

    add_action( 'wp_enqueue_scripts', 'mobex_enovathemes_scripts_styles_general');
    add_action( 'wp_enqueue_scripts', 'mobex_enovathemes_scripts');

    add_action('admin_enqueue_scripts','mobex_enovathemes_admin_scripts_styles');

    function mobex_enovathemes_elementor_scripts() {
        wp_enqueue_style( 'mobex-admin', MOBEX_ENOVATHEMES_TEMPPATH . '/css/admin.css', false, '');
        wp_enqueue_script( 'plugins-combined', MOBEX_ENOVATHEMES_TEMPPATH . '/js/plugins-combined.js', array('jquery'), '', true);
    }
    add_action('elementor/editor/after_enqueue_scripts', 'mobex_enovathemes_elementor_scripts');


    function mobex_enovathemes_editor_styles() {
        wp_enqueue_style( 'mobex-default-font', MOBEX_ENOVATHEMES_TEMPPATH . '/css/default-font.css' );
        wp_enqueue_style( 'mobex-editor-style', MOBEX_ENOVATHEMES_TEMPPATH . '/css/editor-style.css');
    }
    add_action( 'enqueue_block_editor_assets', 'mobex_enovathemes_editor_styles' );

?>