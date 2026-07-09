<?php
	
	$modes        = et_get_theme_mods();
	$shop_sidebar = (isset($modes['shop_sidebar']) && $modes['shop_sidebar'] == 1) ? true : false;
	$data_shop    = (isset($_GET["data_shop"]) && !empty($_GET["data_shop"])) ? $_GET["data_shop"] : "default";

?>

<?php if ($data_shop != 'default' && has_action('efp_filter_demo')): ?>
	<?php do_action('efp_filter_demo',$shop_sidebar); ?>
<?php else: ?>
	<?php if (is_active_sidebar('shop-widgets')): ?>
		<aside class='shop-widgets widget-area'>  
			<a href="#" title="<?php echo esc_attr__("Toggle sidebar","mobex"); ?>" class="content-sidebar-toggle active"></a>
			<?php if ( function_exists( 'dynamic_sidebar' )){dynamic_sidebar('shop-widgets');} ?>
		</aside>
	<?php endif ?>
<?php endif ?>	
