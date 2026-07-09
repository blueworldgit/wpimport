<?php

	$post_related_posts = (!empty(get_theme_mod('post_related_posts'))) ? "true" : "false";

	
	$modes        = et_get_theme_mods();
	$post_sidebar = (isset($modes['post_sidebar']) && $modes['post_sidebar'] == 1) ? true : false;
	
	$columns      = empty($post_sidebar) ? 4 : 3;
	$columns_landscape = empty($post_sidebar) ? 3 : 2;
	
	$arrows_pos   = empty($post_sidebar) ? 'side' : 'top-right';

?>

<?php if ($post_related_posts == "true"): ?>
	<?php $categories = wp_get_post_categories(get_the_ID());?>
	<?php if ($categories): ?>

		<?php

			$args = array(
				'post_type'           => 'post',
				'category__in'        => $categories,
				'posts_per_page'      => 4,
				'ignore_sticky_posts' => 1,
				'orderby'             => 'date',
				'post__not_in'        => array($post->ID)
			);

		    $related_posts = new WP_Query($args);

		    $thumb_size = 'medium';

		    $rand = rand();

		?>

		<?php if ($related_posts->have_posts()): ?>


			<div class="related-posts-wrapper et-clearfix swiper-container" data-arrows-pos="<?php echo esc_attr($arrows_pos); ?>" data-columns="<?php echo esc_attr($columns); ?>" data-tab-land-columns="<?php echo esc_attr($columns_landscape); ?>">
				<h4 class="related-posts-title"><?php echo esc_html__("Related posts", 'mobex'); ?></h4>
				<div id="swiper-<?php echo esc_attr($rand); ?>" class="grid swiper">
					<div id="related-posts" class="related-posts loop-posts only-posts swiper-wrapper">
						<?php while($related_posts->have_posts()) : $related_posts->the_post(); ?>
							<?php echo mobex_enovathemes_post('grid',0,50,$thumb_size); ?>
						<?php endwhile; ?>
						<?php wp_reset_postdata(); ?>
					</div>
				</div>
                <div id="prev-<?php echo esc_attr($rand); ?>" class="swiper-button swiper-button-prev"></div><div id="next-<?php echo esc_attr($rand); ?>" class="swiper-button swiper-button-next"></div>
			</div>
		<?php endif ?>
		
	<?php endif ?>
<?php endif ?>