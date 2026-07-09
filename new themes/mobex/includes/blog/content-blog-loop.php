<?php
	
	$modes        = et_get_theme_mods();
	$blog_layout  = isset($modes['blog_layout']) ? $modes['blog_layout'] : 'masonry';
	$blog_sidebar = (isset($modes['blog_sidebar']) && $modes['blog_sidebar'] == 1) ? true : false;

	if (is_active_sidebar('blog-widgets') && $blog_sidebar == false && !defined('ENOVATHEMES_ADDONS')) {
		$blog_sidebar = true;
	}

	$class = array();

	if (!empty($blog_sidebar)){
		$class[] = 'sidebar-active';
	}

	$class[] = 'post-layout';
	$class[] = $blog_layout;

	if (in_array($blog_layout,array('grid-1','grid-2','grid-3'))) {
		$class[] = 'grid';
	}

?>
<div id="et-content" class="content et-clearfix padding-false">
	<div class="<?php echo implode(' ', $class); ?>">
		<div class="container et-clearfix">
			<?php if ($blog_sidebar): ?>
				<div class="layout-content blog-content et-clearfix">
					<?php get_template_part( '/includes/blog/content-blog-loop-code' ); ?>
				</div>
				<div class="layout-sidebar blog-sidebar et-clearfix">
					<?php get_sidebar(); ?>
				</div>
			<?php else: ?>
				<?php get_template_part( '/includes/blog/content-blog-loop-code' ); ?>
			<?php endif ?>
		</div>
	</div>
</div>