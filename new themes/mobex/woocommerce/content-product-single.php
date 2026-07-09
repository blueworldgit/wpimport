<?php

	$modes          = et_get_theme_mods();
	$product_layout = isset($modes['product_layout']) ? $modes['product_layout'] : 'simple';

    $class = array();

	$class[] = 'post-layout-single';
	$class[] = 'product-layout-single';
	$class[] = $product_layout;

?>
<div id="et-content" class="content et-clearfix padding-false">
	<div class="<?php echo implode(' ', $class); ?>">
		<div class="container et-clearfix">
			<?php woocommerce_content(); ?>
		</div>
		<?php
		
			global $product;

			$footer_banner = get_post_meta($product->get_id(),'enovathemes_addons_footer_banner',true);

			if (!empty($footer_banner) && function_exists('enovathemes_addons_get_the_widget')) {

				$args = array(
					'before_widget' => '<div class="shop-footer-widgets widget widget_banner">',
					'after_widget'  => '</div>',
					'before_title'  => '',
					'after_title'   => '',
				);

				$instance = array(
					'banner' => $footer_banner,
					'category' => '',
					'children' => '',
					'shop'     => '',
				);

				echo enovathemes_addons_get_the_widget( 'Enovathemes_Addons_WP_Widget_Banner', $instance,$args);
			}
		
		?>
	</div>
</div>