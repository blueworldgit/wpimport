<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
	<!-- META TAGS -->
	<meta charset="<?php bloginfo( 'charset' ); ?>" />
	<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=8">
	<!-- LINK TAGS -->
	<?php wp_head(); ?>
</head>

<?php
	
	$blog_link = get_post_type_archive_link( 'post' );
    $shop_link = (function_exists('wc_get_page_id')) ? get_permalink( wc_get_page_id( 'shop' ) ) : '';

    $data   = array();
    $data[] = 'data-url="'.esc_url(home_url('/')).'"';
    $data[] = 'data-blog-url="'.esc_url($blog_link).'"';
    $data[] = 'data-shop-url="'.esc_url($shop_link).'"';

?>

<body <?php body_class(); ?> <?php echo implode(' ',$data); ?>>
<?php wp_body_open(); ?>
<?php
	
	$detect_class = array();

	if (class_exists('\Detection\MobileDetect')) {
    	$detect  = new \Detection\MobileDetect;

    	if ($detect->isMobile() || $detect->isTablet()) {
			$detect_class[] = 'detected';
		}
	}

?>
<!-- wrap start -->
<div id="wrap" class="wrap <?php echo esc_attr(implode(' ',$detect_class)); ?>">
<?php do_action('mobex_enovathemes_header'); ?>
