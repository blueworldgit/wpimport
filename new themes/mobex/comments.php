<?php if ( post_password_required() ) {return;} ?>
<div id="comments" class="post-comments-area">

	<?php if ( have_comments() ) : ?>

		<a href="#" class="et-button small see-responses"><?php echo esc_html__( 'See comments', 'mobex'); ?></a>

		<div class="responses">

			<div class="comments-title">
				<span><?php printf( _nx( '1 comment', '%1$s comments', get_comments_number(), 'comments title', 'mobex'), number_format_i18n( get_comments_number() )); ?></span>
			</div>

			<!-- cooment list start -->
			<div class="comment-list">
		        <?php

					function mobex_enovathemes_comment( $comment, $args, $depth ) {

						$GLOBALS['comment'] = $comment;

						global $post;

						if ($comment->comment_type == 'pingback' || $comment->comment_type == 'trackback'): ?>
							<div <?php comment_class(); ?> id="comment-<?php comment_ID(); ?>">
								<div class="comment-body">
									<div class="comment-content">
										<?php echo esc_html__( 'Pingback:', 'mobex'); ?> <?php comment_author_link(); ?> <?php edit_comment_link( esc_html__( 'Edit', 'mobex' ), '<span class="edit-link">', '</span>' ); ?>
									</div>
								</div>
							<!-- </div> -->
						<?php else: ?>
							<div <?php comment_class(); ?> id="comment-<?php comment_ID(); ?>">
								<div class="comment-body">
									<?php if ( '0' == $comment->comment_approved ) : ?><p class="comment-awaiting-moderation"><?php esc_html__( 'Your comment is awaiting moderation.', 'mobex'); ?></p><?php endif; ?>
									<div class="replay"><?php comment_reply_link( array_merge( $args, array( 'reply_text' => esc_html__( 'Reply', 'mobex'), 'after' => '', 'depth' => $depth, 'max_depth' => $args['max_depth'] ) ) ); ?></div>
									<div class="comment-meta-group">
										<?php if ("" !=  get_avatar($comment, 72)): ?>
											<div class="comment-gavatar"><?php echo get_avatar( $comment, 72 ); ?></div>
										<?php endif ?>
										<div class="comment-meta">
											<?php echo mobex_enovathemes_output_html(( $comment->user_id === $post->post_author ) ? '<span class="post-author-ind">' . esc_html__( 'Post author', 'mobex') . '</span>' : ''); ?>
										</div>
									</div>

									<div class="comment-content">
										<div class="comment-heading">
											<h5 class="comment-author"><?php printf( '<cite>%1$s</cite>', get_comment_author_link()); ?></h5>
											<div class="comment-date-time"><span class="post-date"><?php printf( '<a href="%1$s"><time datetime="%2$s">%3$s</time></a>', esc_url( get_comment_link( $comment->comment_ID ) ), get_comment_time( 'c' ), sprintf( esc_html__( '%1$s at %2$s', 'mobex'), get_comment_date(), get_comment_time() )); ?></span></div>
										</div>
										<div class="comment-text et-clearfix">
											<?php comment_text(); ?>
											<?php edit_comment_link( esc_html__( 'Edit', 'mobex'), '<span class="edit-link">', '</span>' ); ?>
										</div>
									</div>
								</div>
							<!-- </div> -->
						<?php endif; ?>
					<?php }

					wp_list_comments( array( 
						'callback' => 'mobex_enovathemes_comment',
						'avatar_size' => 100,
						'short_ping'  => true,
						'style'       => 'div',
					) );

				?>
			</div>
			<!-- cooment list end -->

			<?php if ( get_comment_pages_count() > 1 && get_option( 'page_comments' ) ) : ?>

				<nav class="navigation comment-navigation" role="navigation">
					<div class="nav-previous"><?php previous_comments_link( esc_html__( '&larr; Older Comments', 'mobex') ); ?></div>
					<div class="nav-next"><?php next_comments_link( esc_html__( 'Newer Comments &rarr;', 'mobex') ); ?></div>
				</nav>

			<?php endif; ?>

			<?php if ( ! comments_open() && get_comments_number() ) : ?>
				<br><br><p><?php echo esc_html__( 'Comments are closed', 'mobex'); ?></p>
			<?php endif; ?>

		</div>

	<?php endif;?>

	<?php 

		$req      = get_option( 'require_name_email' );
		$aria_req = ( $req ? " aria-required='true'" : '' );

		$fields =  array(
			'author' => '<p class="comment-form-author"><input class="enovathemes-placeholder" name="author" type="text" tabindex="1" placeholder="'.esc_attr__('Name *', 'mobex').'" size="30" ' . $aria_req . ' /></p>',
			'email'  => '<p class="comment-form-email"><input class="enovathemes-placeholder" name="email" type="text" tabindex="2" placeholder="'.esc_attr__('E-Mail *', 'mobex').'" size="30" ' . $aria_req . ' /></p>',
			'url' 	 => '<p class="comment-form-url"><input class="enovathemes-placeholder" name="url" type="text" tabindex="3" placeholder="'.esc_attr__('Website', 'mobex').'" size="30" /></p>'
		);

		$comments_args = array(
			'comment_field'       => '<div class="et-clearfix"></div><p class="respond-textarea"><textarea id="comment" name="comment" aria-required="true" cols="58" rows="10" tabindex="4"></textarea></p>',
			'fields'              => $fields,
			'comment_notes_after' => '',
			'label_submit'        => esc_html__('Post Comment', 'mobex')
		);

		comment_form($comments_args);

	?>

</div>