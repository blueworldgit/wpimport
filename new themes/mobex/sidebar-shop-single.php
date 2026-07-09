<?php if(is_active_sidebar('shop-single-widgets')): ?>
	<aside class='shop-single-widgets widget-area'>  
		<a href="#" title="<?php echo esc_attr__("Toggle sidebar","mobex"); ?>" class="content-sidebar-toggle active"></a>
		<?php if ( function_exists( 'dynamic_sidebar' )){dynamic_sidebar('shop-single-widgets');} ?>
	</aside>
<?php endif ?>