<?php

	$modes        = et_get_theme_mods();
	$post_sidebar = (isset($modes['post_sidebar']) && $modes['post_sidebar'] == 1) ? true : false;

	$class = array();

	if (is_active_sidebar('blog-single-widgets') && $post_sidebar == "none" && !defined('ENOVATHEMES_ADDONS')) {
		$post_sidebar = 'true';
	}

	if (!empty($post_sidebar)){
		$class[] = 'sidebar-active';
	}

	$class[] = 'post-layout';
	$class[] = 'layout-single';

?>
<div id="et-content" class="content et-clearfix padding-false">
	<div class="<?php echo implode(' ', $class); ?>">
		<div class="container">
			<?php if (!empty($post_sidebar)): ?>
				<div class="blog-content layout-content et-clearfix">
					<?php get_template_part( '/includes/blog/content-blog-single-code' ); ?>
				</div>
				<div class="blog-sidebar layout-sidebar single et-clearfix">
					<?php get_sidebar('single'); ?>
				</div>
			<?php else: ?>
				<?php get_template_part( '/includes/blog/content-blog-single-code' ); ?>
			<?php endif ?>
		</div>	
	</div>
</div>