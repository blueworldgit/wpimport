<?php if(is_active_sidebar('blog-widgets')): ?>
	<aside class='blog-widgets widget-area'>  
		<a href="#" title="<?php echo esc_attr__("Toggle sidebar","mobex"); ?>" class="content-sidebar-toggle active"></a>
		<?php if ( function_exists( 'dynamic_sidebar' )){dynamic_sidebar('blog-widgets');} ?>
	</aside>
<?php endif ?>	
