<?php


 	$post_social_share = (!empty(get_theme_mod('post_social_share'))) ? "true" : "false";

	$modes        = et_get_theme_mods();
	$post_sidebar = (isset($modes['post_sidebar']) && $modes['post_sidebar'] == 1) ? true : false;

	if (is_active_sidebar('blog-single-widgets') && empty($post_sidebar) && !defined('ENOVATHEMES_ADDONS')) {
		$post_sidebar = 'true';
	}

?>

<div id="single-post-page" class="single-post-page social-links-<?php echo esc_attr($post_social_share); ?>">
	<?php if (have_posts()) : ?>

		<?php while (have_posts()) : the_post(); ?>
			
			<div <?php post_class() ?> id="post-<?php the_ID(); ?>">

				<?php

					$post_format   = get_post_format(get_the_ID());
			        $video         = get_post_meta( get_the_ID(), 'enovathemes_addons_video', true );
			        $video_embed   = get_post_meta( get_the_ID(), 'enovathemes_addons_video_embed', true );
			        $gallery       = get_post_meta( get_the_ID(), 'enovathemes_addons_gallery', true );

					$media_output = "";
                    $body_output  = "";
                    $title_output = "";

                    $title_output .='<div class="post-title-section">';

						if ('' != get_avatar(get_the_author_meta('email'), '72')){
							$title_output .='<div class="post-author-gavatar">';
								$title_output .= get_avatar(get_the_author_meta('email'), '72');
							$title_output .='</div>';
						}

                    	$title_output .='<div>';

					        $title_output .='<div class="post-meta">';

					        	$title_output .= '<div class="post-categories">';

				                    $categories = get_the_category();

				                    foreach( $categories as $category) {
				                        $name = $category->name;
				                        $category_link = get_category_link( $category->term_id );

				                        $title_output .= '<a href="'.$category_link.'" title="'.esc_attr($name).'">'.esc_html($name).'</a>';
				                    }

				                $title_output .='</div>';

					        	$title_output .='<span class="post-date">'.get_the_date().'</span>';

								$title_output .='<a class="post-author-title" href="'.get_author_posts_url( get_the_author_meta("ID") ).'">'.get_the_author_meta("display_name").'</a>';

					        $title_output .='</div>';

							if ( '' != the_title_attribute( 'echo=0' ) ){
								$title_output .='<h1 class="post-title entry-title">';
									$title_output .=get_the_title();
								$title_output .='</h1>';
							}

							if ( '' != get_the_excerpt() ) {
								$title_output .='<div class="post-excerpt">';
									$title_output .= get_the_excerpt();
								$title_output .='</div>';
							}

						$title_output .='</div>';

					$title_output .='</div>';

					if ($post_format == "0"){
                        if (has_post_thumbnail()){

                            $media_output .='<div class="post-image overlay-hover post-media">';
                                $media_output .='<div class="image-container image-container-single">';
                                	$media_output .=mobex_enovathemes_build_post_media('post_img',false);
                                $media_output .='</div>';
                            $media_output .='</div>';
                        }
                    } elseif($post_format == "gallery") {
                        if (!empty($gallery)) {

                        	$media_output .='<div class="swiper-container post-gallery-wrapper post-media" data-arrows-pos="inside">';
		                        $media_output .='<div id="swiper-'.rand().'" class="post-gallery slider swiper et-gallery">';
		                            $media_output .='<ul class="slides swiper-wrapper enova-carousel">';
		                                foreach ($gallery as $image => $url){
		                                    $media_output .='<li class="swiper-slide">';
		                                        $media_output .='<div class="image-container">';
		                                            $media_output .= mobex_enovathemes_build_post_media('post_img',$image);
		                                        $media_output .='</div>';
		                                    $media_output .='</li>';
		                                }
		                            $media_output .='</ul>';
		                        $media_output .='</div>';
		                        $media_output .='<div id="swiper-button-prev-'.rand().'" class="swiper-button swiper-button-prev"></div><div id="swiper-button-next-'.rand().'" class="swiper-button swiper-button-next"></div>';
		                    $media_output .='</div>';

                        } else {

                            if (has_post_thumbnail()){
                                $media_output .='<div class="post-image overlay-hover post-media">';
                                    $media_output .='<div class="image-container image-container-single">';
                                    	$media_output .=mobex_enovathemes_build_post_media('post_img',false);
                                    $media_output .='</div>';
                                $media_output .='</div>';
                            }

                        }
                    } elseif($post_format == "video") {
                    	$media_output .='<div class="post-video post-media">';

	                        if (has_post_thumbnail()){

	                            $link_class[] = 'video-btn';

	                            $attributes   = array();
	                            $attributes[] = 'href="#"';
	                            $attributes[] = 'class="'.implode(" ", $link_class).'"';

	                            $media_output .='<div class="image-container image-container-single">';

	                                $media_output .= mobex_enovathemes_build_post_media('post_img',false);

	                                $media_output .='<a '.implode(" ", $attributes).'>';
	                                    $media_output .='<svg viewBox="0 0 512 512">';
                                        	$media_output .='<path class="back" d="M501.64,132.36a64.13,64.13,0,0,0-45.13-45.13c-40.06-11-200.33-11-200.33-11s-160.26,0-200.32,10.55a65.46,65.46,0,0,0-45.13,45.55C.19,172.42.19,255.51.19,255.51s0,83.5,10.54,123.14a64.16,64.16,0,0,0,45.13,45.13c40.48,11,200.33,11,200.33,11s160.26,0,200.32-10.55a64.11,64.11,0,0,0,45.13-45.13c10.55-40.06,10.55-123.14,10.55-123.14S512.61,172.42,501.64,132.36Z" />';
                                        	$media_output .='<path class="play" d="M346.89,261.61,205.11,350c-4.76,3-11.11-.24-11.11-5.61V167.62c0-5.37,6.35-8.57,11.11-5.61l141.78,88.38A6.61,6.61,0,0,1,346.89,261.61Z"/>';
	                                    $media_output .='</svg>';
	                                $media_output .='</a>';
	                                
	                            $media_output .='</div>';
	                        }

	                        if(!empty($video_embed) && empty($video)) {

	                            $video_embed = str_replace('watch?v=', 'embed/', $video_embed);
	                            $video_embed = str_replace('//vimeo.com/', '//player.vimeo.com/video/', $video_embed);

	                            $media_output .='<iframe allowfullscreen="allowfullscreen" allow="autoplay" frameBorder="0" src="'.$video_embed.'" class="iframevideo video-element"></iframe>';

	                        } elseif(!empty($video)) {

	                            $media_output .='<video poster="'.MOBEX_ENOVATHEMES_IMAGES.'/transparent.png'.'" id="video-'.get_the_ID().'" class="lazy video-element" playsinline controls>';

	                                if (!empty($video)) {
	                                    $media_output .='<source data-src="'.$video.'" type="video/mp4">';
	                                }
	                                
	                            $media_output .='</video>';

	                        }
                        $media_output .='</div>';
                    }

                    $body_output .='<div class="post-body et-clearfix">';

	                    $body_output .='<div class="post-body-inner">';

	                    	$body_output .='<div class="post-content et-clearfix">';

		                        if ( '' != get_the_content() ){

		                        	$content = apply_filters( 'the_content', get_the_content() );
		                        	$content = str_replace( ']]>', ']]&gt;', $content );

	                                $body_output .= $content; 
	                                $defaults = array(
	                                    'before'           => '<div id="page-links">',
	                                    'after'            => '</div>',
	                                    'link_before'      => '',
	                                    'link_after'       => '',
	                                    'next_or_number'   => 'next',
	                                    'separator'        => ' ',
	                                    'nextpagelink'     => esc_html__( 'Continue reading', 'mobex' ),
	                                    'previouspagelink' => esc_html__( 'Go back' , 'mobex'),
	                                    'pagelink'         => '%',
	                                    'echo'             => 0
	                                );
	                                $body_output .= wp_link_pages($defaults);
		                            
		                        }

							$body_output .='</div>';

							$body_output .='<div class="post-bottom et-clearfix">';

								if (has_tag()) {
									$body_output .='<div class="post-tags-single">'.esc_html__("Tags:", 'mobex').' '.get_the_tag_list( '', ' ', '' ).'</div>';
								}

								if (function_exists('enovathemes_addons_post_social_share') && $post_social_share == "true"){
									$body_output .= enovathemes_addons_post_social_share('post');
								}

							$body_output .='</div>';

						$body_output .='</div>';

					$body_output .='</div>';

				?>

				<div class="post-inner et-clearfix">

					<?php


						if (class_exists('\Detection\MobileDetect')) {
							$detect = new \Detection\MobileDetect;
				            if ($detect->isMobile()) {
								echo mobex_enovathemes_output_html($media_output);
								echo mobex_enovathemes_output_html($title_output);
				            } else {
								echo mobex_enovathemes_output_html($title_output);
				            	echo mobex_enovathemes_output_html($media_output);
				            }
						} else {
							echo mobex_enovathemes_output_html($title_output);
				            echo mobex_enovathemes_output_html($media_output);
						}

						echo mobex_enovathemes_output_html($body_output);

					?>

					<?php get_sidebar('after-single'); ?>

					<?php get_template_part( '/includes/blog/content-blog-related-posts' ); ?>

					<div class="post-comments-section">
						<?php comments_template(); ?>
					</div>

					<div class="nav-container">
						<?php mobex_enovathemes_post_nav('post',get_the_ID()); ?>
					</div>

				</div>

			</div>

		<?php endwhile; ?>

	<?php else : ?>
		<?php mobex_enovathemes_not_found('post'); ?>
	<?php endif; ?>
</div>