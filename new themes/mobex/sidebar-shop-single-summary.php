<?php if(is_active_sidebar('shop-single-summary-widgets')): ?>
	<aside class='shop-single-summary-widgets widget-area'>  
		<?php if ( function_exists( 'dynamic_sidebar' )){dynamic_sidebar('shop-single-summary-widgets');} ?>
	</aside>
<?php endif ?>	