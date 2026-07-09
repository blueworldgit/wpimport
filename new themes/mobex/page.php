<?php get_header(); ?>
<?php get_template_part('/includes/title-section'); ?>
<?php

	$page_full_width = get_post_meta( get_the_ID(), 'enovathemes_addons_page_full_width', true );

?>
<!-- content start -->
<div id="et-content" class='content et-clearfix padding-false'>
	<?php do_action('mobex_enovathemes_before_page_container'); ?>
	<?php if($page_full_width != "on"): ?>
		<div class='container'>
	<?php endif; ?>
		<?php while ( have_posts() ) : the_post(); ?>
			<!-- post start -->
			<div id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
				<section class="page-content et-clearfix">
					<?php the_content(); ?>
					<?php
						$defaults = array(
							'before'           => '<div class="et-clearfix"></div><div id="page-links">',
							'after'            => '</div>',
							'link_before'      => '',
							'link_after'       => '',
							'next_or_number'   => 'next',
							'separator'        => ' ',
							'nextpagelink'     => esc_html__( 'Continue reading', 'mobex' ),
							'previouspagelink' => esc_html__( 'Go back' , 'mobex'),
							'pagelink'         => '%',
							'echo'             => 1
						);
						wp_link_pages($defaults);
					?>
				</section>

			</div>
			<!-- post end -->
		<?php endwhile; ?>
		<?php do_action('mobex_enovathemes_after_page_body'); ?>
	<?php if($page_full_width != "on"): ?>
		</div>
	<?php endif; ?>
	<?php do_action('mobex_enovathemes_after_page_container'); ?>
</div>
<!-- content end -->
<?php get_footer(); ?>