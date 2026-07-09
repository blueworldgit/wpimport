<?php

	$shop_sidebar = get_theme_mod('shop_sidebar');

	if (is_active_sidebar('shop-widgets') && empty($shop_sidebar) && !defined('ENOVATHEMES_ADDONS')) {
		$shop_sidebar = 'true';
	}

	$data_shop  = (isset($_GET["data_shop"]) && !empty($_GET["data_shop"])) ? $_GET["data_shop"] : "default";
	if($data_shop == 'nosidebar'){
		$shop_sidebar = '';
	}
?>
<div class="container et-clearfix">
	<?php if (have_posts()): ?>
		<?php if (!empty($shop_sidebar)): ?>
			<div class="layout-sidebar product-sidebar et-clearfix">
				<?php get_sidebar('shop'); ?>
			</div>
			<div class="layout-content product-content et-clearfix">
				<?php

					$loading  = (isset($_GET["ajax"]) && !empty($_GET["ajax"])) ? 'loading' : '';

				?>
				<div class="product-filter-overlay <?php echo esc_attr($loading); ?>"></div>
				<?php woocommerce_content(); ?>
			</div>
		<?php else: ?>
			<?php woocommerce_content(); ?>
		<?php endif ?>
	<?php else: ?>
		<?php

			$default_not_found = true;

			if (isset($_GET['vin']) && $_GET['vin']) {
                $vehicle_attributes = enovathemes_addons_vin_decoder($_GET['vin']);

                if ($vehicle_attributes && isset($vehicle_attributes['error'])) {
                	echo '<div class="woocommerce-no-products-found">
						<div class="woocommerce-info vin-error">'.$vehicle_attributes['error'].'</div>
					</div>';
					$default_not_found = false;
                }
            }

			$product_notfound_form = get_theme_mod('product_notfound_form');

			if ($default_not_found) {
	            do_action( 'woocommerce_no_products_found' );
	        }

            if (
                shortcode_exists('contact-form-7') && 
                isset($product_notfound_form) && !empty($product_notfound_form)
            ) {
                echo '<div class="no-vehicles-form">';
                    echo '<h3>'.esc_html__("Can't find your part or vehicle?","mobex").'</h3>';
                    echo '<p>'.esc_html__("No worries. Our team is here to help you find the perfect part for your car. Just provide us with some details and we will get to work!","mobex").'</p>';
                    echo do_shortcode('[contact-form-7 id="'.$product_notfound_form.'"]');
                echo '</div>';
            } else {

	            $shop_link = (function_exists('wc_get_page_id')) ? get_permalink( wc_get_page_id( 'shop' ) ) : '';
	            if ('' === get_option( 'permalink_structure' )) {
	                $shop_link = get_home_url().'?post_type=product';
	            }

        		echo '<a class="shop-page et-button medium button" href="'.esc_url($shop_link).'">'.esc_html__("Go back to shop","mobex").'</a>';

            }


        ?>
        
	<?php endif ?>
</div>
