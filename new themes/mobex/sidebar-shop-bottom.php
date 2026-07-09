<?php if(is_active_sidebar('shop-bottom-widgets')): ?>
	<aside class='shop-bottom-widgets widget-area'>  
		<?php if ( function_exists( 'dynamic_sidebar' )){dynamic_sidebar('shop-bottom-widgets');} ?>
	</aside>
<?php endif ?>