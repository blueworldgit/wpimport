<?php $error  = get_theme_mod('error');?>
<?php get_header(); ?>
<?php get_template_part('/includes/title-section'); ?>

    <?php if (!empty($error)): ?>
        <?php $post_info = get_post($error); ?>
        <?php if (!is_wp_error($post_info) && is_object($post_info)): ?>
            <div id="et-content" class="content">
                <div class="page-content et-clearfix">
                    <?php 
                        
                        $pluginElementor = \Elementor\Plugin::instance();
                    
                        echo ((defined('ELEMENTOR_VERSION')) ? $pluginElementor->frontend->get_builder_content($post_info->ID,false) : apply_filters('the_content', $post_info->post_content));

                    ?>
                </div>
            </div>
        <?php endif ?>
    <?php else: ?>
        <div id="et-content" class="content default et-clearfix padding-true"><div class="container et-clearfix">
            <div class="message404 et-clearfix">
                <h1 class="error404-default-title">404</span></h1>
                <p class="error404-default-subtitle"><?php echo esc_html__('Page not found','mobex'); ?></p>
                <p class="error404-default-description"><?php echo esc_html__('The page you are looking for could not be found.','mobex'); ?></p>
                <br>
                <a href="<?php echo esc_url(home_url('/')); ?>" class="error404-button et-button medium" title="<?php echo esc_attr__('Go to home','mobex'); ?>"><?php echo esc_html__('Homepage','mobex'); ?></a>
            </div> 
        </div></div>
    <?php endif ?>

<?php get_footer(); ?>
