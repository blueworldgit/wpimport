<?php if(is_active_sidebar('shop-top-widgets')): ?>
	<aside class='shop-top-widgets widget-area'>  
		<?php if ( function_exists( 'dynamic_sidebar' )){dynamic_sidebar('shop-top-widgets');} ?>
	</aside>
<?php endif ?>	