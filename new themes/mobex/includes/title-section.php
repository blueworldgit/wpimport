<?php

	$title = '';

	/* Page
    ---------------*/

        if (is_page()) {

            $title_section_off = get_post_meta( get_the_ID(), 'enovathemes_addons_title_section', true );

            if ($title_section_off != "on") {
                $title = get_the_title( get_the_ID() );
            }
            
        }

    /* Blog
    ---------------*/

        elseif (is_home()) {
        	if(!empty(get_option('page_for_posts'))){
        		$title = get_the_title( get_option('page_for_posts') );
        	} else {
        		$title = get_bloginfo();
        	}
        }elseif (is_category() || is_tag()) {
            $title = single_cat_title('', false);
        }elseif (is_day()) {
            $title = get_the_date('F dS Y');
        }elseif (is_month()) {
            $title = get_the_date('Y, F');
        }elseif (is_year()) {
            $title = get_the_date('Y');
            }elseif (is_author()) {
                $userdata = get_userdata($GLOBALS['author']);
                $author   = (!empty($userdata->first_name) && !empty($userdata->last_name)) ? esc_attr($userdata->first_name)." ".esc_attr($userdata->last_name) : $userdata->user_login;
                $title    = $author;
            }elseif ( is_search()) {
            $title = esc_html__('Search','mobex');
        }elseif ( is_singular('post')) {
            $title = '';
        }elseif ( is_tax()) {
            $title = get_queried_object()->name;
        }

    /*  CPT
    -------------------*/

        elseif (!is_search()  && !is_404()) {                        

            $post_info = get_post(get_the_ID());

            if (!is_wp_error($post_info) && is_object($post_info)) {

                $post_type   = $post_info->post_type;

                if ($post_type != 'post' && $post_type != 'page') {
                    switch ($post_type) {
                        case 'product':
                            if(!empty(get_option('woocommerce_shop_page_id'))){
			            		$title = get_the_title( get_option('woocommerce_shop_page_id') );
			            	} else {
			            		$post_type_name = get_post_type_object('product');
			            		if ($post_type_name) {
			            			$title = $post_type_name->labels->singular_name;
			            		}
			            	}
                            break;
                        default :
                            $post_type_name = get_post_type_object($post_type);
		            		if ($post_type_name) {
		            			$title = $post_type_name->labels->singular_name;
		            		}
                            break;
                    }

                    if ( is_tax()) {
                        $title = single_cat_title('', false);
                    }
                }

            } else {
                $q_object = get_queried_object();
                if (!is_wp_error($q_object) && is_object($q_object)) {
                    if ($q_object->name == 'product') {
                        if(!empty(get_option('woocommerce_shop_page_id'))){
		            		$title = get_the_title( get_option('woocommerce_shop_page_id') );
		            	} else {
		            		$post_type_name = get_post_type_object($q_object->name);
		            		if ($post_type_name) {
		            			$title = $post_type_name->labels->singular_name;
		            		}
		            	}
                    }
                }
            }

        }

        elseif (is_404()) {
            $title = '';
        }

?>

<?php if (is_singular('post') || is_singular('product')): ?>
    <div class="title-section">
        <div class="container">
            <?php if (function_exists('enovathemes_addons_breadcrumbs')): ?>
                <?php enovathemes_addons_breadcrumbs(); ?>
            <?php endif ?>
        </div>
    </div>
<?php else: ?>
    <?php if (!empty($title)): ?>
        <div class="title-section">
            <div class="container et-clearfix">
                <?php if (function_exists('enovathemes_addons_breadcrumbs')): ?>
                    <?php enovathemes_addons_breadcrumbs(); ?>
                <?php endif ?>
                <div class="title-section-title">
                    <h1><?php echo esc_html($title); ?></h1>
                </div>
            </div>
        </div>
    <?php endif ?>
<?php endif ?>


<?php if (
    class_exists('Woocommerce') && 
    (is_shop() || is_tax('product_cat') || is_tax('product_tag'))
){
    // get_template_part('/includes/woocommerce-category-carousel');
    if (function_exists('et__product_categories_carousel')) { ?>
        <div class="container et-clearfix product-categories-carousel-container">
        <?php echo et__product_categories_carousel(); ?>
        </div>
    <?php }
}

