<?php 

    $shop_layout  = get_theme_mod('shop_layout');
    $shop_sidebar = get_theme_mod('shop_sidebar');

    if (is_active_sidebar('shop-widgets') && empty($shop_sidebar) && !defined('ENOVATHEMES_ADDONS')) {
        $shop_sidebar = 'true';
    }

    if (empty($shop_layout)) {
        $shop_layout = 'grid';
    }

	$data_shop  = (isset($_GET["data_shop"]) && !empty($_GET["data_shop"])) ? $_GET["data_shop"] : "default";
	if($data_shop == 'nosidebar'){
		$shop_sidebar = '';
	} elseif($data_shop == 'list'){
		$shop_layout = 'comp';
	}

    $class = array();

    if (!empty($shop_sidebar)) {
        $class[] = 'sidebar-active';
    }

    $class[] = 'product-layout';
    $class[] = $shop_layout;

?>
<?php get_header(); ?>
<?php get_template_part('/includes/title-section'); ?>
<?php if (is_singular('product')): ?>
    <?php get_template_part('/woocommerce/content-product-single'); ?>
<?php else: ?>

    <div class="<?php echo implode(' ', $class); ?>">
        <?php get_template_part('/woocommerce/content-product-loop'); ?>
    </div>
<?php endif ?>
<?php get_footer(); ?>