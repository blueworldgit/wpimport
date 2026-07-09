<?php if (class_exists('Woocommerce')): ?>
    <div class="container et-clearfix">

        <?php

            $args = array(
                'parent'     => 0,
                'hide_empty' => true,
                'meta_key'   => 'order',
                'orderby'    => 'meta_value_num'
            );

            $object_ids = [];

            $vehicle_params = apply_filters( 'vehicle_params','');

            $vehicle_attributes = [];

            foreach ($_GET as $key => $value) {

                $key = ($key == 'yr') ? 'year' : $key;

                if (in_array($key, $vehicle_params)) {
                    $vehicle_attributes[$key] = urldecode($value);
                }
            }

            if (isset($_GET['vin']) && !empty($_GET['vin'])) {
                $vehicle_attributes = enovathemes_addons_vin_decoder($_GET['vin']);
            } else {
                $vehicle_attributes = vehicle_set_from_cookies_if_empty($vehicle_attributes);
            }

            if ($vehicle_attributes && !empty($vehicle_attributes) && !isset($vehicle_attributes['error'])) {
                
                $vehicles = vehicle_filter_component($vehicle_attributes);

                if ($vehicles && !empty($vehicles)) {

                    $products_with_vehicles = new WP_Query( array (
                        'post_type'     => 'product',
                        'posts_per_page'=> -1,
                        'post_status'   => 'publish',
                        'tax_query'    => array(
                            'relation' => 'AND',
                            array(
                                'taxonomy'  => 'product_visibility',
                                'terms'     => array( 'exclude-from-catalog' ),
                                'field'     => 'name',
                                'operator'  => 'NOT IN'
                            ),
                            array(
                                "taxonomy" => "vehicles",
                                "field" => "term_id",
                                "terms" => $vehicles,
                                "operator" => "IN",
                            ),
                        )
                    ));

                    if ($products_with_vehicles->have_posts()){
                        while($products_with_vehicles->have_posts()) { $products_with_vehicles->the_post();

                            $product_cat = wp_get_post_terms(get_the_ID(),'product_cat',array(
                                'parent'     => 0,
                                'hide_empty' => true,
                                'meta_key'   => 'order',
                                'orderby'    => 'meta_value_num',
                            ));

                            if(!empty($product_cat) && !is_wp_error($product_cat)){
                                foreach ( $product_cat as $term ){
                                    $object_ids[] = $term->term_id;
                                }
                            }

                        }
                        wp_reset_postdata();
                    }

                }

                
            }

            if (isset($_GET['s']) && !empty($_GET['s'])) {

                $products_with_search = new WP_Query( array (
                    'post_type'     => 'product',
                    'post_status'   => 'publish',
                    'posts_per_page'=> -1,
                    's'             => $_GET['s'],            
                    'tax_query'     => array(
                        array(
                            'taxonomy'  => 'product_visibility',
                            'terms'     => array( 'exclude-from-catalog' ),
                            'field'     => 'name',
                            'operator'  => 'NOT IN'
                        )
                    )
                ));

                if ($products_with_search->have_posts()){
                    while($products_with_search->have_posts()) { $products_with_search->the_post();

                        $product_cat = wp_get_post_terms(get_the_ID(),'product_cat',array(
                            'parent'     => 0,
                            'hide_empty' => true,
                            'meta_key'   => 'order',
                            'orderby'    => 'meta_value_num',
                        ));

                        if(!empty($product_cat) && !is_wp_error($product_cat)){
                            foreach ( $product_cat as $term ){
                                $object_ids[] = $term->term_id;
                            }
                        }

                    }
                    wp_reset_postdata();
                }
            }

            if (!empty($object_ids)) {

                $object_ids = array_unique($object_ids);
                $object_ids = array_filter($object_ids);

                $args['include'] = $object_ids;
            }

            if (is_tax('product_cat')) {
                $children = get_term_children(get_queried_object_id(),'product_cat');

                if (!is_wp_error($children) && is_array($children) && !empty($children)) {
                    $args['include'] = $children;
                    unset($args['parent']);
                } else {
                    $args = array();
                }

            }

            if (!empty($args)) {

                $link_component = '';

                if ($vehicle_attributes && !empty($vehicle_attributes)) {
                    foreach ($vehicle_attributes as $key => $value) {
                        $key = ($key == "year") ? 'yr' : $key;
                        $link_component .= '&'.$key.'='.$value;
                    }
                }

                $terms = get_terms( 'product_cat', $args);

                if (!empty($terms) && !is_wp_error($terms)) {
                    echo '<div class="swiper-container loop-categories-container" data-arrows-pos="top-right">';

                        echo '<div class="loop-categories-wrapper swiper">';
                            
                            echo '<ul id="loop-categories" class="loop-categories swiper-wrapper">';
                                foreach ( $terms as $term ){

                                    $link = get_term_link($term->term_id,'product_cat');

                                    if (!empty($link_component)) {
                                        $link .= $link_component;
                                    }

                                    if (!str_contains($link,'?')) {
                                        $link = preg_replace('/&/', '?', $link, 1);
                                    }

                                    echo '<li class="category-item swiper-slide"><a href="'.esc_url($link).'">';
                                        $thumbnail_id = get_term_meta($term->term_id, 'thumbnail_id', true);
                                        if ($thumbnail_id) {
                                            echo '<div class="image-container">';
                                                echo mobex_enovathemes_build_post_media('thumbnail',$thumbnail_id,'product');
                                            echo '</div>';
                                        }
                                        echo '<h5>'.esc_html($term->name).'</h5>';
                                    echo '</a></li>';
                                }
                            echo '</ul>';

                        echo '</div>';

                        echo '<div class="swiper-button swiper-button-prev loop-categories-prev"></div><div class="swiper-button swiper-button-next loop-categories-next"></div>';

                    echo '</div>';
                }

            }

        ?>

    </div>
<?php endif ?>