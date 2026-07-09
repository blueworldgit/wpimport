<?php if(is_active_sidebar('blog-single-widgets')): ?>
	<aside class='blog-single-widgets widget-area'>  
		<a href="#" title="<?php echo esc_attr__("Toggle sidebar","mobex"); ?>" class="content-sidebar-toggle active"></a>
		<?php if ( function_exists( 'dynamic_sidebar' )){dynamic_sidebar('blog-single-widgets');} ?>
	</aside>
<?php endif ?>	
