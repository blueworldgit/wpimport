<?php $data_blog  = (isset($_GET["data_blog"]) && !empty($_GET["data_blog"])) ? $_GET["data_blog"] : "default";?>
<?php if ($data_blog != 'default' && has_action('efp_single_post_banner_demo')): ?>
	<?php do_action('efp_single_post_banner_demo',$data_blog); ?>
<?php else: ?>
	<?php if(is_active_sidebar('blog-after-single-widgets')): ?>
		<aside class='blog-after-single-widgets widget-area'>  
			<?php if ( function_exists( 'dynamic_sidebar' )){dynamic_sidebar('blog-after-single-widgets');} ?>
		</aside>
	<?php endif ?>
<?php endif ?>	