<?php

/*  Theme mode
/*-------------------*/

    function et_get_theme_mods(){

        $mods = get_theme_mods();

        if (is_array($mods) && function_exists('efp_get_theme_custom_mods')) {
            $custom_mods = apply_filters( 'efp_get_theme_custom_mods',$mods);

            if ($custom_mods) {
                $mods = $custom_mods;
            }
        }

        return $mods;
    }


/*  Post format chat
/*-------------------*/

    function mobex_enovathemes_post_chat_format($content) {
        global $post;
        if (has_post_format('chat')) {
            $chatoutput = "<ul class=\"chat\">\n";
            $split = preg_split("/(\r?\n)+|(<br\s*\/?>\s*)+/", $content);

            foreach($split as $haystack) {
                if (strpos($haystack, ":")) {
                    $string = explode(":", trim($haystack), 2);
                    $who = strip_tags(trim($string[0]));
                    $what = strip_tags(trim($string[1]));
                    $row_class = empty($row_class)? " class=\"chat-highlight\"" : "";
                    $chatoutput = $chatoutput . "<li><span class='name'>$who:</span><p>$what</p></li>\n";
                } else {
                    $chatoutput = $chatoutput . $haystack . "\n";
                }
            }

            $content = $chatoutput . "</ul>\n";
            return $content;
        } else { 
            return $content;
        }
    }
    add_filter( "the_content", "mobex_enovathemes_post_chat_format", 9);

/*  Post image overlay
/*-------------------*/

    function mobex_enovathemes_post_image_overlay($blog_post_layout){

        $post_format   = get_post_format(get_the_ID());
        $link_url      = get_post_meta( get_the_ID(), 'enovathemes_addons_link', true );

        $read_more_link = ($blog_post_layout == "full" && $post_format == "link" && !empty($link_url)) ? $link_url : get_the_permalink();

        $output = '';

        $output .='<a class="post-image-overlay" href="'.esc_url($read_more_link).'" title="'.esc_attr__("Read more about", 'mobex').' '.esc_attr(the_title_attribute( 'echo=0' )).'">';
        $output .='</a>';

        return $output;
    }

/*  Pagination
/*-------------------*/

    function mobex_enovathemes_post_nav_num($post_type){

        if( is_singular() ){
            return;
        }

        global $wp_query;

        $big    = 999999;
        $output = "";

        switch ($post_type) {
            case 'product':
                $posts_per_page = get_theme_mod('product_number');
                if (empty($posts_per_page) || !isset($posts_per_page)) {
                    $posts_per_page = get_option( 'posts_per_page' );
                }
            break;
            default:
                $posts_per_page = '';
            break;
        }

        $total  = (empty($posts_per_page)) ? $wp_query->max_num_pages : ceil($wp_query->found_posts/$posts_per_page);

        $args = array(
        'base'      => str_replace($big, '%#%', get_pagenum_link($big)),
        'format'    => '?paged=%#%',
        'total'     => $total,
        'current'   => max(1, get_query_var('paged')),
        'show_all'  => false,
        'end_size'  => 2,
        'mid_size'  => 3,
        'prev_next' => true,
        'prev_text' => '',
        'next_text' => '',
        'type'      => 'list');

        // if ($posts_per_page < $wp_query->found_posts) {
            $output .='<nav class="enovathemes-navigation">';
                $output .= paginate_links($args);
            $output .='</nav>';
        // }
        
        return mobex_enovathemes_output_html($output);
    }

/*  Simple pagination
/*-------------------*/
    
    function mobex_enovathemes_post_nav($post_type,$post_id){

            $single_nav_mob = "false";

            $post_prev_text = esc_html__('Previous', 'mobex');
            $post_next_text = esc_html__('Next', 'mobex');

            $prev_post = get_adjacent_post(false, '', true);
            $next_post = get_adjacent_post(false, '', false);
            
        ?>
        <nav class="post-single-navigation <?php echo esc_attr($post_type) ?> mob-hide-false">  
          <?php if(!empty($next_post)) {echo '<a rel="prev" href="' . esc_url(get_permalink($next_post->ID)) . '" title="'.esc_attr__("Previous ","mobex").'">'.$post_prev_text.'</a>'; } ?>
          <?php if(!empty($prev_post)) {echo '<a rel="next" href="' . esc_url(get_permalink($prev_post->ID)) . '" title="'.esc_attr__("Next ","mobex").'">'.$post_next_text.'</a>'; } ?>
        </nav>
        <?php 
    }

/*  Navigation
/*-------------------*/

    function mobex_enovathemes_navigation($post_type, $navigation){

        $hidden  = (isset($_GET["ajax"]) && !empty($_GET["ajax"])) ? 'hidden' : '';

    ?>
        <?php 
        switch ($navigation) {
            case 'infinite':
            case 'loadmore':

                $attributes = array();
                $class      = array();
                $class[]    = 'post-ajax-button';
                $class[]    = 'et-button';
                $class[]    = 'hover-scale';
                $class[]    = 'rounded';
                $class[]    = 'medium';

                $attributes[] = 'href="#"';
                $attributes[] = 'data-effect="scale"';
                $attributes[] = 'class="'.implode(" ", $class).'"';
                $attributes[] = 'id="'.$navigation.'"';

                $output ='<div class="nav-wrapper '.esc_attr($hidden).'">';
                    $output .='<a '.implode(" ", $attributes).' >';
                        $output .='<span class="text">'.esc_html__('Load more','mobex').'</span>';

                        $output .='<svg viewBox="0 0 48 48">';
                            $output .='<circle class="loader-path" cx="24" cy="24" r="20" />';
                        $output .='</svg>';

                        $output .='<span class="button-back"></span>';
                    $output .='</a>';
                $output .='</div>';

                return $output;

                break;
            default:
                return mobex_enovathemes_post_nav_num($post_type);
                break;
        }
        ?>
    <?php }

/*  Excerpt
/*-------------------*/

    function mobex_enovathemes_substrwords($text, $maxchar, $end='..') {
        if (strlen($text) > $maxchar || $text == '') {
            $words = preg_split('/\s/', $text);      
            $output = '';
            $i      = 0;
            while (1) {
                $length = strlen($output)+strlen($words[$i]);
                if ($length > $maxchar) {
                    break;
                } 
                else {
                    $output .= " " . $words[$i];
                    ++$i;
                }
            }
            $output .= $end;
        } 
        else {
            $output = $text;
        }
        return $output;
    }

/*  Loop post content
/*-------------------*/

    function mobex_enovathemes_build_post_media($thumb_size,$id,$post_type ='post'){

        $placeholder  = !empty(get_theme_mod('placeholder')) ? false : true;

        $output = '';

        $thumbnail_id  = ($id) ? $id: get_post_thumbnail_id( get_the_ID() );
        $image         = wp_get_attachment_image_src($thumbnail_id,$thumb_size);

        if ($image) {

            $image_src     = $image[0];
            $image_width   = $image[1];
            $image_height  = $image[2];

            $thumbnail_alt = get_post_meta($thumbnail_id, '_wp_attachment_image_alt', true); 
            $image_caption = get_the_post_thumbnail_caption($image);
            $image_alt     = (empty($image_caption)) ? ((empty($thumbnail_alt)) ? get_bloginfo('name') : $thumbnail_alt) : $image_caption;
            
            $x_center = ($image_width/2);
            $y_center = ($image_height/2);

            $cl = array('lazy-inline-image');

            if(!empty($class)){
                $cl[]= $class;  
            }

            if ($placeholder) {
                $lazy_image = wp_get_attachment_image_src($thumbnail_id,'lazy_img');
                $output .= '<img class="lazy" data-src="'.esc_url($image_src).'" src="'.esc_url($lazy_image[0]).'" width="'.esc_attr($image_width).'" height="'.esc_attr($image_height).'" alt="'.esc_attr($image_alt).'" />';
                $output .= '<svg viewBox="0 0 '.esc_attr($image_width).' '.esc_attr($image_height).'"><path d="M0,0H'.$image_width.'V'.$image_height.'H0V0Z" /></svg>';
            } else {
                $output .= '<img '.implode(' ',$attributes).' src="'.esc_url($image_src).'" width="'.esc_attr($image_width).'" height="'.esc_attr($image_height).'" alt="'.esc_attr($image_alt).'" />';
            }

        } elseif($post_type == 'product') {
            $output .= wc_placeholder_img( $thumb_size);
        }

        if (!empty($output)) {
            return $output;
        }

    }

    

    function mobex_enovathemes_post_media($blog_post_layout,$thumb_size){
        
        $post_format   = get_post_format(get_the_ID());
        $video         = get_post_meta( get_the_ID(), 'enovathemes_addons_video', true );
        $video_embed   = get_post_meta( get_the_ID(), 'enovathemes_addons_video_embed', true );
        $gallery       = get_post_meta( get_the_ID(), 'enovathemes_addons_gallery', true );
        $output        = "";

        $date_output = '<div class="post-date-side">';
            $date_output .= '<span>'.date_i18n('d', strtotime(get_the_date())).'</span>';
            $date_output .= '<span>'.date_i18n('M', strtotime(get_the_date())).'</span>';
        $date_output .= '</div>';


        if ($blog_post_layout == "full"){

            if (
                $post_format == "0" || 
                $post_format == 'chat' || 
                $post_format == 'aside'  || 
                $post_format == 'quote' || 
                $post_format == 'status' || 
                $post_format == 'audio' || 
                $post_format == 'link'){
                if (has_post_thumbnail()){
                    $output .='<div class="post-image overlay-hover post-media">';
                        
                        $output .= $date_output;

                        $output .='<div class="image-container">';
                            $output .= mobex_enovathemes_build_post_media($thumb_size,false);
                        $output .='</div>';
                        $output .= mobex_enovathemes_post_image_overlay($blog_post_layout);
                    $output .='</div>';
                }
            } elseif($post_format == "gallery") {

                if (!empty($gallery)) {

                    $output .='<div class="swiper-container post-gallery-wrapper" data-arrows-pos="inside">';
                        
                        $output .= $date_output;

                        $output .='<div id="swiper-'.rand().'" class="post-gallery post-media slider swiper et-gallery">';
                            $output .='<ul class="slides swiper-wrapper enova-carousel">';
                                foreach ($gallery as $image => $url){
                                    $output .='<li class="swiper-slide">';
                                        $output .='<div class="image-container">';
                                            $output .= mobex_enovathemes_build_post_media($thumb_size,$image);
                                        $output .='</div>';
                                        $output .= mobex_enovathemes_post_image_overlay($blog_post_layout);
                                    $output .='</li>';
                                }
                            $output .='</ul>';
                        $output .='</div>';
                        $output .='<div id="swiper-button-prev-'.rand().'" class="swiper-button swiper-button-prev"></div><div id="swiper-button-next-'.rand().'" class="swiper-button swiper-button-next"></div>';
                    $output .='</div>';

                } else {

                    if (has_post_thumbnail()){
                        $output .='<div class="post-image overlay-hover post-media">';

                            $output .= $date_output;

                            $output .='<div class="image-container">';
                                $output .= mobex_enovathemes_build_post_media($thumb_size,false);
                            $output .='</div>';
                            $output .= mobex_enovathemes_post_image_overlay($blog_post_layout);

                        $output .='</div>';
                    }

                }
            } elseif($post_format == "video") {
                if (!empty($video) || !empty($video_embed)){
                    $output .='<div class="post-video post-media">';

                        if (has_post_thumbnail()){

                            $link_class[] = 'video-btn';

                            $attributes   = array();
                            $attributes[] = 'href="#"';
                            $attributes[] = 'class="'.implode(" ", $link_class).'"';

                            $output .='<div class="image-container">';

                                $output .= mobex_enovathemes_build_post_media($thumb_size,false);

                                $output .='<a '.implode(" ", $attributes).'>';
                                    $output .='<svg viewBox="0 0 512 512">';
                                        $output .='<path class="back" d="M501.64,132.36a64.13,64.13,0,0,0-45.13-45.13c-40.06-11-200.33-11-200.33-11s-160.26,0-200.32,10.55a65.46,65.46,0,0,0-45.13,45.55C.19,172.42.19,255.51.19,255.51s0,83.5,10.54,123.14a64.16,64.16,0,0,0,45.13,45.13c40.48,11,200.33,11,200.33,11s160.26,0,200.32-10.55a64.11,64.11,0,0,0,45.13-45.13c10.55-40.06,10.55-123.14,10.55-123.14S512.61,172.42,501.64,132.36Z" />';
                                        $output .='<path class="play" d="M346.89,261.61,205.11,350c-4.76,3-11.11-.24-11.11-5.61V167.62c0-5.37,6.35-8.57,11.11-5.61l141.78,88.38A6.61,6.61,0,0,1,346.89,261.61Z"/>';
                                    $output .='</svg>';
                                $output .='</a>';
                                
                            $output .='</div>';
                        }

                        if(!empty($video_embed) && empty($video)) {

                            $video_embed = str_replace('watch?v=', 'embed/', $video_embed);
                            $video_embed = str_replace('//vimeo.com/', '//player.vimeo.com/video/', $video_embed);

                            $output .='<iframe allowfullscreen="allowfullscreen" allow="autoplay" frameBorder="0" src="'.$video_embed.'" class="iframevideo video-element"></iframe>';

                        } elseif(!empty($video)) {

                            $output .='<video poster="'.MOBEX_ENOVATHEMES_IMAGES.'/transparent.png'.'" id="video-'.get_the_ID().'" class="lazy video-element" playsinline controls>';

                                if (!empty($video)) {
                                    $output .='<source data-src="'.$video.'" src="'.MOBEX_ENOVATHEMES_IMAGES.'/video_placeholder.mp4'.'" type="video/mp4">';
                                }
                                
                            $output .='</video>';

                        }

                        $output .= $date_output;

                    $output .='</div>';
                }
            }
        } else {


            if (!empty($video) || !empty($video_embed)){

                $video_class='';

                $output .='<div class="post-video post-media">';

                    if (has_post_thumbnail()){

                        $link_class[] = 'video-btn';

                        $attributes   = array();
                        $attributes[] = 'href="#"';
                        $attributes[] = 'class="'.implode(" ", $link_class).'"';

                        $output .='<div class="image-container">';

                            $output .= mobex_enovathemes_build_post_media($thumb_size,false);

                            $output .='<a '.implode(" ", $attributes).'>';
                                $output .='<svg viewBox="0 0 512 512">';
                                    $output .='<path class="back" d="M501.64,132.36a64.13,64.13,0,0,0-45.13-45.13c-40.06-11-200.33-11-200.33-11s-160.26,0-200.32,10.55a65.46,65.46,0,0,0-45.13,45.55C.19,172.42.19,255.51.19,255.51s0,83.5,10.54,123.14a64.16,64.16,0,0,0,45.13,45.13c40.48,11,200.33,11,200.33,11s160.26,0,200.32-10.55a64.11,64.11,0,0,0,45.13-45.13c10.55-40.06,10.55-123.14,10.55-123.14S512.61,172.42,501.64,132.36Z" />';
                                    $output .='<path class="play" d="M346.89,261.61,205.11,350c-4.76,3-11.11-.24-11.11-5.61V167.62c0-5.37,6.35-8.57,11.11-5.61l141.78,88.38A6.61,6.61,0,0,1,346.89,261.61Z"/>';
                                $output .='</svg>';
                            $output .='</a>';
                            
                        $output .='</div>';
                    } else {
                        $video_class = "loaded";
                    }

                    if(!empty($video_embed) && empty($video)) {

                        $video_embed = str_replace('watch?v=', 'embed/', $video_embed);
                        $video_embed = str_replace('//vimeo.com/', '//player.vimeo.com/video/', $video_embed);

                        $output .='<iframe allowfullscreen="allowfullscreen" allow="autoplay" frameBorder="0" src="'.$video_embed.'" class="iframevideo video-element '.esc_attr($video_class).'"></iframe>';

                    } elseif(!empty($video)) {

                        $output .='<video poster="'.MOBEX_ENOVATHEMES_IMAGES.'/transparent.png'.'" id="video-'.get_the_ID().'" class="lazy video-element" playsinline controls>';

                            if (!empty($video)) {
                                $output .='<source data-src="'.$video.'" src="'.MOBEX_ENOVATHEMES_IMAGES.'/video_placeholder.mp4'.'" type="video/mp4">';
                            }
                            
                        $output .='</video>';

                    }

                    if (in_array($blog_post_layout, array('grid','grid-3','masonry'))) {
                        $output .= $date_output;
                    }

                $output .='</div>';
            } elseif (has_post_thumbnail()) {

                $output .='<div class="post-image overlay-hover post-media">';

                    $output .='<div class="image-container">';

                        if (in_array($blog_post_layout, array('grid','grid-3','masonry'))) {
                            $output .= $date_output;
                        }

                        $output .=mobex_enovathemes_build_post_media($thumb_size,false);
                    $output .='</div>';

                    $output .= mobex_enovathemes_post_image_overlay($blog_post_layout);

                $output .='</div>';

            }

            
        }

        return $output;
    }

    function mobex_enovathemes_post_body($blog_post_layout,$blog_post_excerpt,$blog_post_title_excerpt){

        $post_format   = get_post_format(get_the_ID());
        $link_url      = get_post_meta( get_the_ID(), 'enovathemes_addons_link', true );
        $status_author = get_post_meta( get_the_ID(), 'enovathemes_addons_status', true );
        $quote_author  = get_post_meta( get_the_ID(), 'enovathemes_addons_quote', true );
        $audio         = get_post_meta( get_the_ID(), 'enovathemes_addons_audio', true );
        $audio_embed   = get_post_meta( get_the_ID(), 'enovathemes_addons_audio_embed', true );

        $read_more_link = ($blog_post_layout == "full" && $post_format == "link" && !empty($link_url)) ? $link_url : get_the_permalink();
        
        $output = "";

        $output .='<div class="post-body et-clearfix">';

            if (!in_array($blog_post_layout,array('grid-2','full'))){

                $output .= '<div class="post-meta">';

                    $output .= '<div class="post-categories">';

                        $categories = get_the_category();

                        foreach( $categories as $category) {
                            $name = $category->name;
                            $category_link = get_category_link( $category->term_id );

                            $output .= '<a href="'.$category_link.'" title="'.esc_attr($name).'">'.esc_html($name).'</a>';
                        }

                    $output .='</div>';

                    if ($blog_post_layout == "list") {
                        $output .= '<div class="post-date">'.get_the_date().'</div>';
                    }

                $output .='</div>';

            }

            if ( '' != the_title_attribute( 'echo=0' ) ){
                $output .='<h4 class="post-title entry-title">';
                    $output .= '<a href="'.esc_url($read_more_link).'" title="'.esc_attr__("Read more about", 'mobex').' '.the_title_attribute( 'echo=0' ).'" rel="bookmark">';
                        if (empty($blog_post_title_excerpt)) {
                            $output .= the_title_attribute( 'echo=0' );
                        } else {
                            $output .= mobex_enovathemes_substrwords(the_title_attribute( 'echo=0' ),$blog_post_title_excerpt);
                        }
                    $output .= '</a>';
                $output .='</h4>';
            }

            if ($blog_post_layout == "full"){

                if ($post_format == "aside" || $post_format == "quote" || $post_format == "status"){

                    if ( '' != get_the_content() ){
                        $output .='<div class="post-excerpt">';

                            $output .= get_the_content(); 
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
                            $output .= wp_link_pages($defaults);

                        $output .='</div>';
                    }

                    if (!empty($quote_author)){
                        $output .= '<div class="post-quote-author">'.esc_attr($quote_author).'</div>';
                    }

                    if (!empty($status_author)){
                        $output .= '<div class="post-status-author">'.esc_attr($status_author).'</div>';
                    }

                } else {

                    $content =  ('' != get_the_excerpt() ?  get_the_excerpt() : ('' != get_the_content() ? get_the_content() : ''));

                    if ( !empty($content) && $blog_post_excerpt > 0){
                        $output .='<div class="post-excerpt">'.mobex_enovathemes_substrwords(get_the_excerpt(),$blog_post_excerpt).'</div>';
                    }

                    $output .='<a href="'.esc_url($read_more_link).'" class="post-read-more" title="'.esc_attr__("Read more about", 'mobex').' '.the_title_attribute( 'echo=0' ).'">'.esc_html__("Read more", 'mobex').'</a>';
                }

            } else {
                if (in_array($blog_post_layout, array('list','grid','masonry'))) {
                    if ($blog_post_excerpt > 0){
                        
                        if ('' != get_the_excerpt()) {
                            $output .='<div class="post-excerpt">'.mobex_enovathemes_substrwords(get_the_excerpt(),$blog_post_excerpt).'</div>';
                        }

                    }

                    if (in_array($blog_post_layout, array('list'))) {
                        $output .='<a href="'.esc_url($read_more_link).'" class="post-read-more" title="'.esc_attr__("Read more about", 'mobex').' '.the_title_attribute( 'echo=0' ).'">'.esc_html__("Read more", 'mobex').'</a>';
                    }
                }
            }

        $output .='</div>';

        if (!in_array($blog_post_layout, array('list','grid-2','full'))){

            $output .='<a href="'.esc_url($read_more_link).'" class="post-read-more" title="'.esc_attr__("Read more about", 'mobex').' '.the_title_attribute( 'echo=0' ).'">'.esc_html__("Read more", 'mobex').'</a>';

        }

        return $output;
        
    }

    function mobex_enovathemes_post($blog_post_layout,$blog_post_excerpt,$blog_post_title_excerpt,$thumb_size){

        $output = "";
        $class  = "";

        if (!has_post_thumbnail()){
            $class = ' no-media';
        }

        $output .='<article class="post swiper-slide'.$class.'" id="post-'.get_the_ID().'">';
        
            $output .='<div class="post-inner et-item-inner">';

                if (has_post_thumbnail(get_the_ID())) {
                    // Post media
                    $output .= mobex_enovathemes_post_media($blog_post_layout,$thumb_size);
                }
                
                // Post body
                $output .= mobex_enovathemes_post_body($blog_post_layout,$blog_post_excerpt,$blog_post_title_excerpt);

            $output .='</div>';
        $output .='</article>';

        return $output;

    }

/*  Not found
/*-------------------*/

    function mobex_enovathemes_not_found($post_type){

        $output = '';

        $output .= '<p class="enovathemes-not-found">';

        switch ($post_type) {

            case 'products':
                $output .= esc_html__('No products found.', 'mobex');
                break;

            case 'general':
                $output .= esc_html__('No search results found. Try a different search', 'mobex');
                break;
            
            default:
                $output .= esc_html__('No posts found.', 'mobex');
                break;
        }

        $output .= '</p>';

        return $output;
    }

/*  Output html
/*-------------------*/

    function mobex_enovathemes_output_html($html) {
        return $html;
    }

/*  Default header
/*-------------------*/

    function mobex_enovathemes_default_header($header_type){

        if ($header_type == "mobile") { ?>

            <header id="et-mobile-default" class="header et-mobile desktop-false">
                <div class="container">
                    <a id="mobile-header-logo" class="header-logo" href="<?php echo esc_url(home_url('/')); ?>" title="<?php echo esc_attr(get_bloginfo('name')); ?>">
                        <img class="logo" src="<?php echo esc_url(MOBEX_ENOVATHEMES_IMAGES.'/logo.svg'); ?>" alt="<?php echo esc_attr(get_bloginfo('name')); ?>">
                    </a>
                    <div id="mobile-toggle-default" class="mobile-toggle"></div>
                    <div id="mobile-container-default" class="mobile-container">


                        <?php

                            $class   = array();
                            $class[] = 'et-mobile-container-top';

                            $output = '<div class="'.implode(" ", $class).'">';

                                $output .= '<div class="mobile-toggle active hbe-toggle"></div>';

                                $avatar = $email = $user = '';

                                if ( is_user_logged_in() ) {
                                        $current_user = wp_get_current_user();
                                        $user         = ($current_user->user_firstname) ? $current_user->user_firstname : $current_user->display_name;
                                        $avatar       = get_avatar($current_user->ID, '56');
                                        $email        = $current_user->user_email;
                                    }

                                    $my_account_link = (empty($my_account_link)) ? 

                                    class_exists("woocommerce") ? (get_option('woocommerce_myaccount_page_id')) ? get_permalink(get_option('woocommerce_myaccount_page_id')) : '' : '' : $my_account_link;

                                $output .= '<div class="logged-in info-wrap">';

                                    $output .= $avatar;
                                        $output .='<div class="info">';
                                            if (!empty($user)) {
                                                $output .='<span>'.esc_html($user).'</span>';
                                            }

                                            if (!empty($email)) {
                                                $output .='<span>'.esc_html($email).'</span>';
                                            }
                                        $output .= '</div>';

                                        if (!empty($my_account_link)) {
                                            $output .= '<a href="'.esc_url($my_account_link).'" class="et-button small">'.esc_html__("Dashboard","enovathemes-addons").'</a>';
                                        }

                                $output .= '</div>';

                                $output .= '<div class="logged-out info-wrap">';

                                    $output .= '<div class="avatar-placeholder"></div>';
                                        $output .='<div class="info">';
                                            $output .='<span>'.esc_html__("Hello Guest","enovathemes-addons").'</span>';
                                            $output .='<span>'.esc_html__("For better experience","enovathemes-addons").'</span>';
                                        $output .= '</div>';
                                        if (!empty($my_account_link)) {
                                            $output .= '<a href="'.esc_url($my_account_link).'" class="et-button small">'.esc_html__("Login","enovathemes-addons").'</a>';
                                        }
                                $output .= '</div>';
                                    

                            $output .= '</div>';

                            echo mobex_enovathemes_output_html($output);

                            if (has_nav_menu( 'header-menu' )) {

                                $menu_arg = array(
                                    'theme_location'  => 'header-menu',
                                    'menu_class'      => 'mobile-menu hbe-inner et-clearfix',
                                    'menu_id'         => 'mobile-menu-default',
                                    'echo'            => true,
                                );

                                wp_nav_menu($menu_arg);
                            }

                        ?>
                    </div>
                </div>
            </header>

        <?php } elseif($header_type == "desktop"){ ?>
            <header id="et-desktop-default" class="header et-desktop mobile-false">
                <div class="container et-clearfix">

                    <a id="desktop-header-logo" class="header-logo" href="<?php echo esc_url(home_url('/')); ?>" title="<?php echo esc_attr(get_bloginfo('name')); ?>">
                        <img class="logo" src="<?php echo esc_url(MOBEX_ENOVATHEMES_IMAGES.'/logo.svg'); ?>" alt="<?php echo esc_attr(get_bloginfo('name')); ?>">
                    </a>
                    
                    <?php

                        $class   = array();
                        $class[] = 'header-menu-container';
                        $class[] = 'nav-menu-container';
                        $class[] = 'one-page-offset-false';
                        $class[] = 'hide-default-false';
                        $class[] = 'hide-sticky-false';
                        $class[] = 'menu-hover-none';
                        $class[] = 'submenu-appear-fade';
                        $class[] = 'submenu-shadow-true';
                        $class[] = 'tl-submenu-ind-false';
                        $class[] = 'sl-submenu-ind-true';
                        $class[] = 'top-separator-false';

                        $menu_arg = array(
                            'theme_location'  => 'header-menu',
                            'menu_class'      => 'header-menu nav-menu hbe-inner et-clearfix',
                            'container'       => 'nav',
                            'container_id'    => 'header-menu-container-default',
                            'menu_id'         => 'header-menu-default',
                            'container_class' => implode(" ", $class),
                            'items_wrap'      => '<ul id="%1$s" class="%2$s" data-color="#ffffff" data-color-hover="#ffffff">%3$s</ul>',
                            'echo'            => true,
                            'link_before'     => '<span class="txt">',
                            'link_after'      => '</span><span class="arrow"></span><span class="effect"></span>',
                            'walker'          => new et_scm_walker
                        );

                        if (has_nav_menu('header-menu')) {
                            wp_nav_menu($menu_arg);
                        }
                    ?>
                            
                </div>
            </header>
        <?php }
    }

/*  Default footer
/*-------------------*/

    function mobex_enovathemes_default_footer(){ ?>
        <footer id="et-footer-default" class="footer et-footer et-clearfix">
            <?php echo '&copy; '.date("Y").' '.esc_html__( 'Copyright', 'mobex' ).' '.esc_html(get_bloginfo('name')); ?>        
        </footer>
    <?php }

/*  Woo Hooks
/*-------------------*/

    function is_woo_pcc(){
        return (is_product() || is_cart() || is_checkout()) ? true : false;
    }

    function mobex_enovathemes_wishlist_compare_quickview($layout,$product){
        
        $wishlist  = (get_theme_mod('product_wishlist') != null && !empty(get_theme_mod('product_wishlist'))) ? "true" : "false";
        $compare   = (get_theme_mod('product_compare') != null && !empty(get_theme_mod('product_compare'))) ? "true" : "false";
        $quickview = (get_theme_mod('product_quick_view') != null && !empty(get_theme_mod('product_quick_view'))) ? "true" : "false";

        $output   = '';

        if ($quickview == "true") {
            $output.='<div title="'.esc_html__("Quick view","mobex").'" class="en-quick-view" data-product="'.esc_attr($product->get_id()).'"></div>';
        }

        $title = esc_html__("Add to wishlist","mobex");
        $class = '';

        if($wishlist == "true"){

            if (is_user_logged_in()) {
                $current_user = wp_get_current_user();
                $current_user_wishlist = get_user_meta( $current_user->ID, 'wishlist',true);

                if (isset($current_user_wishlist) && !empty($current_user_wishlist) && in_array($product->get_id(), explode(',', $current_user_wishlist))) {
                   $title = esc_html__("In wishlist","mobex");
                   $class = 'active';
                   $wishlist_count = '';
                }

            }

            $output.= '<a class="wishlist-toggle '.esc_attr($class).'" data-product="'.esc_attr($product->get_id()).'" href="'.esc_url(get_permalink(get_option('woocommerce_myaccount_page_id'))).'wishlist'.'" title="'.$title.'"></a><span class="wishlist-title">'.$title.'</span>';

        }
        if($compare == "true"){
            $output.= '<a class="compare-toggle" data-product="'.esc_attr($product->get_id()).'" href="#" title="'.esc_attr__("Compare","mobex").'"></a><span class="compare-title">'.esc_attr__("Add to compare","mobex").'</span>';
        }
        if (!empty($output)) {
            return $output;
        }
    }

    function mobex_enovathemes_loop_product_thumbnail($layout,$discount = false) { ?>

        <?php

            global $post,$product;

            $quickview = (get_theme_mod('product_quick_view') != null && !empty(get_theme_mod('product_quick_view'))) ? "true" : "false";

            $product_id = $product->get_id();
            $thumb_size = 'woocommerce_thumbnail';


            $image_class = array();
            $image_class[] = 'post-image';
            $image_class[] = 'post-media';
            $image_class[] = 'overlay-hover';

            $output = '';

            $output.='<div class="'.implode(' ', $image_class).'">';

                $output.=mobex_enovathemes_wishlist_compare_quickview($layout,$product);

                $output.='<div title="'.esc_html__("Quick view","mobex").'" class="en-quick-view" data-product="'.esc_attr($product->get_id()).'"></div>';
                
                $output.='<a href="'.get_the_permalink().'" >';

                    if ( $product->is_on_sale() ){
                        if ($discount == "true"){

                            if($product->is_type( 'variable' ) )
                            {

                                $variations = $product->get_available_variations();

                                $all_variation_prices = array();

                                foreach ($variations as $variation) {
                                    $variation_prices = array();
                                    $variation_prices['regular_price'] = $variation['display_regular_price'];
                                    $variation_prices['sale_price']    = $variation['display_price'];

                                    array_push($all_variation_prices, $variation_prices);
                                }

                                $all_regular_prices = array();
                                $all_sale_prices    = array();

                                foreach ($all_variation_prices as $variation_price) {
                                    array_push($all_regular_prices, $variation_price['regular_price']);
                                    array_push($all_sale_prices, $variation_price['sale_price']);
                                }

                                $regular_price = array_sum($all_regular_prices)/count($all_regular_prices);
                                $sale_price    = array_sum($all_sale_prices)/count($all_sale_prices);

                            } else {
                                $regular_price = $product->get_regular_price();
                                $sale_price    = $product->get_sale_price();
                            }

                            if (!$product->is_type( 'grouped' )) {

                                if (!empty($regular_price)) {
                                    $off = round((($regular_price-$sale_price)/$regular_price)*100,0);
                                    $output.='<span class="onsale discount"><span class="onsale-inner">-'.$off . '%</span></span>';
                                }

                            }

                        } else {
                            $output.=apply_filters( 'woocommerce_sale_flash', '<span class="onsale">' . esc_html__( 'Sale', 'mobex' ) . '</span>', $post, $product );
                        }
                    }

                    $mobex_enovathemes_label1 = get_post_meta($product->get_id(),'mobex_enovathemes_label1',true);
                    $mobex_enovathemes_label2 = get_post_meta($product->get_id(),'mobex_enovathemes_label2',true);

                    if (isset($mobex_enovathemes_label1) && !empty($mobex_enovathemes_label1)) {
                        $mobex_enovathemes_label1_color = get_post_meta($product->get_id(),'mobex_enovathemes_label1_color',true);

                        $style = '';

                        if (isset($mobex_enovathemes_label1_color) && !empty($mobex_enovathemes_label1_color)) {
                            $style = 'style="background:'.$mobex_enovathemes_label1_color.';';
                            $style .='"';
                        }

                         $output.='<span class="label" '.$style.'>' . esc_html($mobex_enovathemes_label1) . '</span>';

                    }

                    if (isset($mobex_enovathemes_label2) && !empty($mobex_enovathemes_label2)) {
                        $mobex_enovathemes_label2_color = get_post_meta($product->get_id(),'mobex_enovathemes_label2_color',true);

                        $style = '';

                        if (isset($mobex_enovathemes_label2_color) && !empty($mobex_enovathemes_label2_color)) {
                            $style = 'style="background:'.$mobex_enovathemes_label2_color.';';
                            $style .='"';
                        }

                        $output.='<span class="label" '.$style.'>' . esc_html($mobex_enovathemes_label2) . '</span>';

                    }

                    $output.='<div class="image-container">';
                        $output.=mobex_enovathemes_build_post_media($thumb_size,false,'product');
                    $output.='</div>';

                $output.='</a>';
            $output.='</div>';

            if (!empty($output)) {
                return $output;
            }

        ?>

    <?php }

    function woocommerce_template_loop_add_to_cart_theme( $args = array() ) {
        global $product;

        if ( $product ) {
            $defaults = array(
                'quantity'   => 1,
                'class'      => implode(
                    ' ',
                    array_filter(
                        array(
                            'button',
                            'product_type_' . $product->get_type(),
                            $product->is_purchasable() && $product->is_in_stock() ? 'add_to_cart_button' : '',
                            $product->supports( 'ajax_add_to_cart' ) && $product->is_purchasable() && $product->is_in_stock() ? 'ajax_add_to_cart' : '',
                        )
                    )
                ),
                'attributes' => array(
                    'data-product_id'  => $product->get_id(),
                    'data-product_sku' => $product->get_sku(),
                    'aria-label'       => $product->add_to_cart_description(),
                    'rel'              => 'nofollow',
                ),
            );

            $args = apply_filters( 'woocommerce_loop_add_to_cart_args', wp_parse_args( $args, $defaults ), $product );

            if ( isset( $args['attributes']['aria-label'] ) ) {
                $args['attributes']['aria-label'] = wp_strip_all_tags( $args['attributes']['aria-label'] );
            }

            return apply_filters(
                'woocommerce_loop_add_to_cart_link', // WPCS: XSS ok.
                sprintf(
                    '<a href="%s" data-quantity="%s" class="%s" %s>%s</a>',
                    esc_url( $product->add_to_cart_url() ),
                    esc_attr( isset( $args['quantity'] ) ? $args['quantity'] : 1 ),
                    esc_attr( isset( $args['class'] ) ? $args['class'] : 'button' ),
                    isset( $args['attributes'] ) ? wc_implode_html_attributes( $args['attributes'] ) : '',
                    esc_html( $product->add_to_cart_text() )
                ),
                $product,
                $args
            );
        }
    }

    function mobex_enovathemes_loop_product_rating($product_ID=false){

        global $product;

        $rating_count = $product->get_rating_count();

        $output = '';

        if(get_option( 'woocommerce_enable_reviews' ) === "yes"){

            if ($rating_count){
                if ( wc_review_ratings_enabled() ) {
                    $output.='<div class="star-rating-wrap">';
                        $output.= wc_get_rating_html( $product->get_average_rating() );
                        $output.='<span>'.esc_html($rating_count).'</span>';
                    $output.='</div>';
                }
            } else {
                $output.='<div class="star-rating-wrap">';
                    $output.='<div class="star-rating empty"></div>';
                $output.='</div>';
            }

        }

        if (!empty($output)) {
            return $output;
        }
    }

    function mobex_enovathemes_loop_product_title($layout) { ?>

        <?php
            
            global $product, $woocommerce_loop;

            $product_title_length = get_theme_mod('product_title_length');
            $shop_layout_excerpt  = (null != get_theme_mod('shop_layout_excerpt') && !empty(get_theme_mod('shop_layout_excerpt'))) ? true : false;
		
            if (empty($product_title_length)) {
                $product_title_length = '56';
            }
            
            $output ='';

        $output.='<div class="post-body">';
            $output.='<div class="post-body-inner">';

                $output.='<div class="post-content-wrap">';

                    $output.= mobex_enovathemes_wishlist_compare_quickview($layout,$product);

                    $categories = wp_get_post_terms($product->get_id(),'product_cat');
     
                    $title = the_title_attribute( 'echo=0' );

                    if ($title) {
                        $output.='<h4 class="post-title">';
                            $output.='<a href="'.get_the_permalink().'" title="'.esc_attr__("Read more avbout", 'mobex').' '.$title.'">'.mb_strimwidth($title,0,$product_title_length,'').'</a>';
                        $output.='</h4>';
                    }

                    $sku   = $product->get_sku();
                    if (!empty($sku)) {
                        $output .= '<span class="product-sku">'.esc_html__( 'SKU:', 'mobex' ).' '.$sku.'</span>';
                    }

                    $output.=mobex_enovathemes_loop_product_rating();

                    $product_attributes = array();

                    $display_dimensions = apply_filters( 'wc_product_enable_dimensions_display', $product->has_weight() || $product->has_dimensions() );

                    if ( $display_dimensions && $product->has_weight() ) {
                        $product_attributes['weight'] = array(
                          'label' => __( 'Weight', 'mobex' ),
                          'value' => wc_format_weight( $product->get_weight() ),
                        );
                    }

                    if ( $display_dimensions && $product->has_dimensions() ) {
                        $product_attributes['dimensions'] = array(
                          'label' => __( 'Dimensions', 'mobex' ),
                          'value' => wc_format_dimensions( $product->get_dimensions( false ) ),
                        );
                    }

                    // Add product attributes to list.
                    $attributes = array_filter( $product->get_attributes(), 'wc_attributes_array_filter_visible' );

                    foreach ( $attributes as $attribute ) {
                    $values = array();

                    if ( $attribute->is_taxonomy() ) {
                      $attribute_taxonomy = $attribute->get_taxonomy_object();
                      $attribute_values   = wc_get_product_terms( $product->get_id(), $attribute->get_name(), array( 'fields' => 'all' ) );

                      foreach ( $attribute_values as $attribute_value ) {
                        $value_name = esc_html( $attribute_value->name );

                        if ( $attribute_taxonomy->attribute_public ) {
                          $values[] = '<a href="' . esc_url( get_term_link( $attribute_value->term_id, $attribute->get_name() ) ) . '" rel="tag">' . $value_name . '</a>';
                        } else {
                          $values[] = $value_name;
                        }
                      }
                    } else {
                      $values = $attribute->get_options();

                      foreach ( $values as &$value ) {
                        $value = make_clickable( esc_html( $value ) );
                      }
                    }

                    $product_attributes[ 'attribute_' . sanitize_title_with_dashes( $attribute->get_name() ) ] = array(
                      'label' => wc_attribute_label( $attribute->get_name() ),
                      'value' => apply_filters( 'woocommerce_attribute', wpautop( wptexturize( implode( ', ', $values ) ) ), $attribute, $values ),
                    );
                    }
                    
                    $product_attributes = apply_filters( 'woocommerce_display_product_attributes', $product_attributes, $product );

                    $output .= '<div class="product-attributes-wrapper">';

                        $output .= '<h6>'.esc_html__("Product information","mobex").'</h6>';

                        $output .= '<ul class="product-attributes">';

                            $index = 1;

                            foreach ($product_attributes as $product_attribute_key => $product_attribute) {
                                $output.= '<li><span class="attr-label">'.wp_kses_post( $product_attribute['label'] ).'</span><span class="attr-value">'.wp_kses_post( $product_attribute['value'] ).'</span></li>';
                                if ($index > 6) {
                                    break;
                                }    
                                $index++;
                            }

                        $output .= '</ul>';

                        $output .= '<a class="button et-button small comp-details" href="'.get_the_permalink().'" title="'.esc_attr__("Read more avbout", 'mobex').' '.$title.'">'.esc_html__("Details...","mobex").'</a>';

                    $output .= '</div>';

                $output.='</div>';


                $output.='<div class="price-button-wrapp">';

                    if ( $price_html = $product->get_price_html() ){
                        $output.='<span class="price">'.$price_html.'</span>';
                    }

                    $output.= woocommerce_template_loop_add_to_cart_theme();

                $output .= '</div>';


                if (!empty($output)) {
                    return $output;
                }

            ?>

    <?php }

    function mobex_enovathemes_loop_product_inner_close($layout) {

        global $product;

        $output = '';

            $output .= '<div class="comp-body">';
                $output .= '<div class="comp-body-inner">';

                    if (taxonomy_exists('pa_brand')) {

                        $attr = get_the_terms($product->get_id(),'pa_brand');

                        if ($attr && !is_wp_error($attr)) {

                            foreach ($attr as $key => $term) {
                                $image = get_term_meta($term->term_id,'image',true);
                                if (isset($image) && !empty($image)) {
                                    $output.='<div class="product-brand"><img alt="'.esc_attr($term->name).'" src="'.wp_get_attachment_url($image).'"></div><div class="et-clearfix"></div>';
                                }
                                
                            }
                            
                        }
                    }

                    $stock_quantity = $product->get_stock_quantity();

                    if ( $price_html = $product->get_price_html() ){
                        $output.='<span class="price">'.$price_html.'</span>';
                    }

                    $output .= '<div class="comp-form">';
                        $output .= '<div class="comp-counter-btn">';
                            if (!empty($stock_quantity) && $stock_quantity < 10) {
                                $output .= '<div class="comp-quantity">'.esc_html__("Quantity","mobex").' <span>'.esc_html__("Only","mobex").' '.$stock_quantity.' '.esc_html__("left in stock!","mobex").'</span></div>';
                            }
                            if($product->is_type( 'simple' )){
                                $output .= '<div class="comp-counter"><span class="minus">-</span><input type="number" value="1"><span class="plus">+</span></div>';
                            }
                        $output .= '</div>';
                        $output.= woocommerce_template_loop_add_to_cart_theme();
                    $output .= '</div>';

                    $output .= mobex_enovathemes_wishlist_compare_quickview($layout,$product);

               $output .= '</div>';
            $output .= '</div>';

            $output .= '</div>';
        $output .= '</div>';

        

        if (!empty($output)) {
            return $output;
        }

    }

    function mobex_enovathemes_fbt_output(){

        global $post;

        $product_title_length = get_theme_mod('product_title_length');

        if (empty($product_title_length)){
            $product_title_length = '56';
        }

        $fbt_ids = get_post_meta( get_the_ID(), 'fbt_ids', true );

        if (!empty($fbt_ids)) {

            $currency           = get_woocommerce_currency_symbol();
            $currency_pos       = get_option('woocommerce_currency_pos');
            $price_num_decimals = get_option('woocommerce_price_num_decimals');

            $column = count($fbt_ids);

            $style  = '';

            $class   = array();
            $class[] = 'loop-posts';
            $class[] = 'loop-products';
            $class[] = 'products';
            $class[] = 'fbt';

            if ($column > 3) {
                $column = 3;
            }

            if ($column > 0) {
                $style = 'grid-template-columns: repeat(3, 3fr);';
            }

            $output = '<div data-column="'.esc_attr($column).'" class="fbt-products post-layout product-layout list">';

                $output .= '<h4>'.esc_html__('Frequently bought together','mobex').'</h4>';

                $output .= '<div class="fbt-products-inner">';

                    $all_prices = array();

                    $output .= '<ul data-column="'.esc_attr($column).'" class="'.implode(' ', $class).'" style="'. $style.'">';
                        foreach ( $fbt_ids as $fbt_id ) {
                            $product = wc_get_product( $fbt_id );
                            if ( is_object( $product ) && $product->is_in_stock()) {

                                if($product->is_type( 'variable' ) )
                                {
                                    $price      = $product->get_variation_regular_price();
                                    $price_sale = $product->get_variation_price();
                                } else {
                                    $price       = $product->get_regular_price();
                                    $price_sale  = $product->get_sale_price();
                                }

                                $final_price = ($price_sale) ? $price_sale : $price;

                                if (!empty($final_price)) {

                                    $final_price = round($final_price,$price_num_decimals);

                                    array_push($all_prices, $final_price);
                                }

                                $output .= '<li class="product" id="product-'.esc_attr($product->get_id()).'">';

                                    $output .= '<div class="post-inner et-item-inner">';

                                        if ( $product->is_on_sale() ){
                                            $output.=apply_filters( 'woocommerce_sale_flash', '<span class="onsale">' . esc_html__( 'Sale', 'mobex' ) . '</span>', $post, $product );
                                        }

                                        $thumb_size = 'woocommerce_thumbnail';

                                        $image_class = array();
                                        $image_class[] = 'post-image';
                                        $image_class[] = 'post-media';
                                        $image_class[] = 'overlay-hover';

                                        $output .= '<div class="'.implode(' ', $image_class).'">';

                                            $output .= '<a href="'.get_permalink( $product->get_id() ).'" >';
                                                $output .='<div class="image-container">';
                                                    $output .= mobex_enovathemes_build_post_media($thumb_size,$product->get_image_id(),'product');
                                                $output .='</div>';
                                            $output .= '</a>';

                                        $output .= '</div>';

                                        $output .= '<div class="post-body et-clearfix">';
                                            $output .= '<div class="post-body-inner">';


                                                $output .= '<h4 class="post-title et-clearfix">';
                                                    $output .= '<a href="'.get_permalink( $product->get_id() ).'" title="'.esc_attr__("Read more avbout", "mobex").' '.$product->get_name().'">'.mb_strimwidth($product->get_name(),0,$product_title_length,'').'</a>';
                                                $output .= '</h4>';

                                                $rating_count = $product->get_rating_count();

                                                if(get_option( 'woocommerce_enable_reviews' ) === "yes"){

                                                    if ($rating_count){
                                                        if ( wc_review_ratings_enabled() ) {
                                                            $output.='<div class="star-rating-wrap">';
                                                                $output.= wc_get_rating_html( $product->get_average_rating() );
                                                                $output.='<span>'.esc_html($rating_count).'</span>';
                                                            $output.='</div>';
                                                        }
                                                    } else {
                                                        $output.='<div class="star-rating-wrap">';
                                                            $output.='<div class="star-rating empty"></div>';
                                                        $output.='</div>';
                                                    }

                                                }

                                                if ( $price_html = $product->get_price_html() ){
                                                    $output .= '<div class="product-price">';
                                                        $output .= '<span class="price">'.$price_html.'</span>';
                                                    $output .= '</div>';
                                                }

                                                $args = array();

                                                $defaults = array(
                                                    'quantity'   => 1,
                                                    'class'      => implode(
                                                        ' ',
                                                        array_filter(
                                                            array(
                                                                'button',
                                                                'product_type_' . $product->get_type(),
                                                                $product->is_purchasable() && $product->is_in_stock() ? 'add_to_cart_button' : '',
                                                                $product->supports( 'ajax_add_to_cart' ) && $product->is_purchasable() && $product->is_in_stock() ? 'ajax_add_to_cart' : '',
                                                            )
                                                        )
                                                    ),
                                                    'attributes' => array(
                                                        'data-product_id'  => $product->get_id(),
                                                        'data-product_sku' => $product->get_sku(),
                                                        'aria-label'       => $product->add_to_cart_description(),
                                                        'rel'              => 'nofollow',
                                                    ),
                                                );

                                                $args = apply_filters( 'woocommerce_loop_add_to_cart_args', wp_parse_args( $args, $defaults ), $product );

                                                if ( isset( $args['attributes']['aria-label'] ) ) {
                                                    $args['attributes']['aria-label'] = wp_strip_all_tags( $args['attributes']['aria-label'] );
                                                }

                                                $output .= apply_filters(
                                                    'woocommerce_loop_add_to_cart_link', // WPCS: XSS ok.
                                                    sprintf(
                                                        '<a href="%s" data-quantity="%s" class="%s" %s>%s</a>',
                                                        esc_url( $product->add_to_cart_url() ),
                                                        esc_attr( isset( $args['quantity'] ) ? $args['quantity'] : 1 ),
                                                        esc_attr( isset( $args['class'] ) ? $args['class'] : 'button' ),
                                                        isset( $args['attributes'] ) ? wc_implode_html_attributes( $args['attributes'] ) : '',
                                                        esc_html( $product->add_to_cart_text() )
                                                    ),
                                                    $product,
                                                    $args
                                                );

                                                $output .= '<div data-product="'.esc_attr($product->get_id()).'" data-price="'.esc_attr($final_price).'" class="chosen fbt-item"></div>';

                                            $output .= '</div>';
                                        $output .= '</div>';

                                    $output .= '</div>';

                                $output .= '</li>';
                            }
                        }
                    $output .= '</ul>';

                    $total_price = '<span>'.wc_price(array_sum($all_prices)).'</span>';

                    $output .= '<div class="fbt-info">';
                        $output .= '<div class="selected">';
                            $output .= '<div>'.esc_html__('Buy selected for','mobex').'</div>';
                            $output .= '<div class="total-price">'.$total_price.'</div>'; 
                            $output .= '<a class="add_to_cart_all et-button medium button" href="#">'.esc_html__('Add all to cart','mobex').'</a>';
                        $output .= '</div>';
                    $output .= '</div>';

                $output .= '</div>';

            $output .= '</div>';
            echo mobex_enovathemes_output_html($output);
        }
    }

?>