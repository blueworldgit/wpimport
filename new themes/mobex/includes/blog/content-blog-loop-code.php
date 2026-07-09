<?php

	$modes               = et_get_theme_mods();
	$post_excerpt_length = isset($modes['post_excerpt_length']) ? $modes['post_excerpt_length'] : 128;
	$post_title_length   = isset($modes['post_title_length']) ? $modes['post_title_length'] : 56;
	$blog_layout         = isset($modes['blog_layout']) ? $modes['blog_layout'] : 'masonry';
    $blog_navigation     = isset($modes['blog_navigation']) ? $modes['blog_navigation'] : 'pagination';

	$class   = array();
	$class[] = 'loop-posts';
	$class[] = 'only-posts';

?>

<?php if (have_posts()) : ?>

	<main id="loop-posts" class="<?php echo esc_attr(implode(' ', $class)); ?>" data-nav="<?php echo esc_attr($blog_navigation); ?>">

		<?php $thumb_size = ($blog_layout == 'full') ? 'post_img' : 'medium'; ?>

		<?php while (have_posts()) : the_post(); ?>
			<?php echo mobex_enovathemes_post($blog_layout,$post_excerpt_length,$post_title_length,$thumb_size,false); ?>
		<?php endwhile; ?>

	</main>

	<?php echo mobex_enovathemes_navigation('post',$blog_navigation); ?>

<?php else : ?>
	<?php mobex_enovathemes_not_found('post'); ?>
<?php endif; ?>