<?php
/**
 *  /!\ This is a copy of Walker_Nav_Menu_Edit class in core
 *
 * Create HTML list of nav menu input items.
 *
 * @package WordPress
 * @since 3.0.0
 * @uses Walker_Nav_Menu
 */
class Walker_Nav_Menu_Edit_Custom extends Walker_Nav_Menu  {
	/**
	 * @see Walker_Nav_Menu::start_lvl()
	 * @since 3.0.0
	 *
	 * @param string $output Passed by reference.
	 */
	function start_lvl(&$output, $depth = 0, $args = array()) {
	}

	/**
	 * @see Walker_Nav_Menu::end_lvl()
	 * @since 3.0.0
	 *
	 * @param string $output Passed by reference.
	 */
	function end_lvl(&$output, $depth = 0, $args = array()) {
	}

	/**
	 * @see Walker::start_el()
	 * @since 3.0.0
	 *
	 * @param string $output Passed by reference. Used to append additional content.
	 * @param object $item Menu item data object.
	 * @param int $depth Depth of menu item. Used for padding.
	 * @param object $args
	 */
	function start_el(&$output, $item, $depth = 0, $args = array(), $id = 0) {
	    global $_wp_nav_menu_max_depth;

	    $_wp_nav_menu_max_depth = $depth > $_wp_nav_menu_max_depth ? $depth : $_wp_nav_menu_max_depth;

	    $indent = ( $depth ) ? str_repeat( "\t", $depth ) : '';

	    ob_start();
	    $item_id = esc_attr( $item->ID );
	    $removed_args = array(
	        'action',
	        'customlink-tab',
	        'edit-menu-item',
	        'menu-item',
	        'page-tab',
	        '_wpnonce',
	    );


	    $original_title = false;
		if ( 'taxonomy' == $item->type ) {
			$original_title = get_term_field( 'name', $item->object_id, $item->object, 'raw' );
			if ( is_wp_error( $original_title ) )
				$original_title = false;
		} elseif ( 'post_type' == $item->type ) {
			$original_object = get_post( $item->object_id );
			$original_title = get_the_title( $original_object->ID );
		} elseif ( 'post_type_archive' == $item->type ) {
			$original_object = get_post_type_object( $item->object );
			if ( $original_object ) {
				$original_title = $original_object->labels->archives;
			}
		}


	    $classes = array(
	        'menu-item menu-item-depth-' . $depth,
	        'menu-item-' . esc_attr( $item->object ),
	        'menu-item-edit-' . ( ( isset( $_GET['edit-menu-item'] ) && esc_attr($item_id) == $_GET['edit-menu-item'] ) ? 'active' : 'inactive'),
	    );

	    $title = $item->title;

	    if ( ! empty( $item->_invalid ) ) {
	        $classes[] = 'menu-item-invalid';
	        /* translators: %s: title of menu item which is invalid */
	        $title = sprintf( esc_html__( '%s (Invalid)' , 'mobex' ), $item->title );
	    } elseif ( isset( $item->post_status ) && 'draft' == $item->post_status ) {
	        $classes[] = 'pending';
	        /* translators: %s: title of menu item in draft status */
	        $title = sprintf( esc_html__('%s (Pending)' , 'mobex'), $item->title );
	    }

	    $title = empty( $item->label ) ? $title : $item->label;

	    ?>
	    <li id="menu-item-<?php echo esc_attr($item_id); ?>" class="<?php echo implode(' ', $classes ); ?>">
	        <dl class="menu-item-bar">
	            <dt class="menu-item-handle">
	                <span class="item-title"><?php echo esc_html( $title ); ?></span>
	                <span class="item-controls">
	                    <span class="item-type"><?php echo esc_html( $item->type_label ); ?></span>
	                    <span class="item-order hide-if-js">
	                        <a href="<?php
	                            echo wp_nonce_url(
	                                add_query_arg(
	                                    array(
	                                        'action' => 'move-up-menu-item',
	                                        'menu-item' => esc_attr($item_id),
	                                    ),
	                                    remove_query_arg($removed_args, admin_url( 'nav-menus.php' ) )
	                                ),
	                                'move-menu_item'
	                            );
	                        ?>" class="item-move-up"><abbr title="<?php echo esc_attr__('Move up', 'mobex'); ?>">&#8593;</abbr></a>
	                        |
	                        <a href="<?php
	                            echo wp_nonce_url(
	                                add_query_arg(
	                                    array(
	                                        'action' => 'move-down-menu-item',
	                                        'menu-item' => esc_attr($item_id),
	                                    ),
	                                    remove_query_arg($removed_args, admin_url( 'nav-menus.php' ) )
	                                ),
	                                'move-menu_item'
	                            );
	                        ?>" class="item-move-down"><abbr title="<?php echo esc_attr__('Move down', 'mobex'); ?>">&#8595;</abbr></a>
	                    </span>
	                    <a class="item-edit" id="edit-<?php echo esc_attr($item_id); ?>" href="<?php
	                        echo ( isset( $_GET['edit-menu-item'] ) && esc_attr($item_id) == $_GET['edit-menu-item'] ) ? admin_url( 'nav-menus.php' ) : add_query_arg( 'edit-menu-item', esc_attr($item_id), remove_query_arg( $removed_args, admin_url( 'nav-menus.php#menu-item-settings-' . esc_attr($item_id) ) ) );
	                    ?>"></a>
	                </span>
	            </dt>
	        </dl>

	        <div class="menu-item-settings" id="menu-item-settings-<?php echo esc_attr($item_id); ?>">
	            <?php if( 'custom' == $item->type ) : ?>
	                <p class="field-url description description-wide">
	                    <label for="edit-menu-item-url-<?php echo esc_attr($item_id); ?>">
	                        <?php echo esc_html__( 'URL', 'mobex' ); ?><br />
	                        <input type="text" id="edit-menu-item-url-<?php echo esc_attr($item_id); ?>" class="widefat code edit-menu-item-url" name="menu-item-url[<?php echo esc_attr($item_id); ?>]" value="<?php echo esc_attr( $item->url ); ?>" />
	                    </label>
	                </p>
	            <?php endif; ?>
	            <p class="description description-thin">
	                <label for="edit-menu-item-title-<?php echo esc_attr($item_id); ?>">
	                    <?php echo esc_html__( 'Navigation Label', 'mobex' ); ?><br />
	                    <input type="text" id="edit-menu-item-title-<?php echo esc_attr($item_id); ?>" class="widefat edit-menu-item-title" name="menu-item-title[<?php echo esc_attr($item_id); ?>]" value="<?php echo esc_attr( $item->title ); ?>" />
	                </label>
	            </p>
	            <p class="description description-thin">
	                <label for="edit-menu-item-attr-title-<?php echo esc_attr($item_id); ?>">
	                    <?php echo esc_html__( 'Title Attribute', 'mobex' ); ?><br />
	                    <input type="text" id="edit-menu-item-attr-title-<?php echo esc_attr($item_id); ?>" class="widefat edit-menu-item-attr-title" name="menu-item-attr-title[<?php echo esc_attr($item_id); ?>]" value="<?php echo esc_attr( $item->post_excerpt ); ?>" />
	                </label>
	            </p>
	            <p class="field-link-target description">
	                <label for="edit-menu-item-target-<?php echo esc_attr($item_id); ?>">
	                    <input type="checkbox" id="edit-menu-item-target-<?php echo esc_attr($item_id); ?>" value="_blank" name="menu-item-target[<?php echo esc_attr($item_id); ?>]"<?php checked( $item->target, '_blank' ); ?> />
	                    <?php echo esc_html__( 'Open link in a new window/tab', 'mobex' ); ?>
	                </label>
	            </p>
	            <p class="field-css-classes description description-thin">
	                <label for="edit-menu-item-classes-<?php echo esc_attr($item_id); ?>">
	                    <?php echo esc_html__( 'CSS Classes (optional)', 'mobex' ); ?><br />
	                    <input type="text" id="edit-menu-item-classes-<?php echo esc_attr($item_id); ?>" class="widefat code edit-menu-item-classes" name="menu-item-classes[<?php echo esc_attr($item_id); ?>]" value="<?php echo esc_attr( implode(' ', $item->classes ) ); ?>" />
	                </label>
	            </p>
	            <p class="field-xfn description description-thin">
	                <label for="edit-menu-item-xfn-<?php echo esc_attr($item_id); ?>">
	                    <?php echo esc_html__( 'Link Relationship (XFN)', 'mobex' ); ?><br />
	                    <input type="text" id="edit-menu-item-xfn-<?php echo esc_attr($item_id); ?>" class="widefat code edit-menu-item-xfn" name="menu-item-xfn[<?php echo esc_attr($item_id); ?>]" value="<?php echo esc_attr( $item->xfn ); ?>" />
	                </label>
	            </p>
	            <p class="field-description description description-wide">
	                <label for="edit-menu-item-description-<?php echo esc_attr($item_id); ?>">
	                    <?php echo esc_html__( 'Description' , 'mobex'); ?><br />
	                    <textarea id="edit-menu-item-description-<?php echo esc_attr($item_id); ?>" class="widefat edit-menu-item-description" rows="3" cols="20" name="menu-item-description[<?php echo esc_attr($item_id); ?>]"><?php echo esc_html( $item->description ); // textarea_escaped ?></textarea>
	                    <span class="description"><?php echo esc_html__('The description will be displayed in the menu if the current theme supports it.',  'mobex'); ?></span>
	                </label>
	            </p>

	            <?php
	            /* New fields insertion starts here */
	            ?>
	            <div class="et-clearfix">
		            <div class="field-custom megamenu-options description description-wide">
	                	<div class="megamenu-opt mms">
		                	<?php $selected2 = get_post_meta( esc_attr($item_id), '_menu_item_megamenu', true ); ?>
		                	<br><label for="edit-menu-item-megamenu-<?php echo esc_attr($item_id); ?>"><?php echo esc_html__( 'Megamenu','mobex' ); ?></label>
		                	<select class="widefull" id="edit-menu-item-megamenu-<?php echo esc_attr($item_id); ?>" name="menu-item-megamenu[<?php echo esc_attr($item_id); ?>]">
				                <option value="false" <?php if($selected2 == "false"){echo 'selected';}?>><?php echo esc_html__('false','mobex'); ?></option>
				                <option value="true" <?php if($selected2 == "true"){echo 'selected';}?>><?php echo esc_html__('true','mobex'); ?></option>
				            </select>
	                	</div>
	                	<div class="megamenu-opt hidden mmc">
		                	<?php $selected = get_post_meta( esc_attr($item_id), '_menu_item_megamenu_content', true ); ?>
		                	<br><label for="edit-menu-item-megamenu_content-<?php echo esc_attr($item_id); ?>"><?php echo esc_html__( 'Megamenu content','mobex' ); ?></label>

		                	<?php

		                		$query_options = array(
									'post_type'           => 'megamenu',
									'post_status'         => 'publish',
									'ignore_sticky_posts' => 1,
									'orderby'             => 'title',
									'order'               => 'ASK',
									'posts_per_page' 	  => -1,
								);

								$megamenu = new WP_Query($query_options);

		                	?>

		                	<?php if ($megamenu->have_posts()): ?>
		                		<select class="widefull" id="edit-menu-item-megamenu_content-<?php echo esc_attr($item_id); ?>" name="menu-item-megamenu_content[<?php echo esc_attr($item_id); ?>]">
		                		<option value="select" <?php if($selected == "select"){echo 'selected';}?>><?php echo esc_html__('-- Select -- ','mobex'); ?></option>
		                		<?php while($megamenu->have_posts()) : $megamenu->the_post(); ?>
		                			<?php $postid = get_the_ID(); ?>
		                			<option value="<?php echo esc_attr($postid) ?>" <?php if($selected == $postid){echo 'selected';}?>><?php echo esc_html(get_the_title($postid)); ?></option>
								<?php endwhile; ?>
								</select>
								<?php wp_reset_postdata(); ?>
		                	<?php else: ?>
		                		<p><?php echo esc_html__('First you must create a megamenu from ','mobex'); ?> <a href="<?php echo esc_url(home_url('/')).'wp-admin/post-new.php?post_type=megamenu'; ?>"><?php echo esc_html__('here','mobex'); ?></a></p>
		                	<?php endif ?>
		                	<br><br><label for="edit-menu-item-megamenu_ajax-<?php echo esc_attr($item_id); ?>"><?php echo esc_html__( 'Load megamenu asynchronous?','mobex' ); ?></label>
		                	<?php $selected3 = get_post_meta( esc_attr($item_id), '_menu_item_megamenu_ajax', true ); ?>
		                	<select class="widefull" id="edit-menu-item-megamenu-ajax-<?php echo esc_attr($item_id); ?>" name="menu-item-megamenu-ajax[<?php echo esc_attr($item_id); ?>]">
				                <option value="false" <?php if($selected3 == "false"){echo 'selected';}?>><?php echo esc_html__('false','mobex'); ?></option>
				                <option value="true" <?php if($selected3 == "true"){echo 'selected';}?>><?php echo esc_html__('true','mobex'); ?></option>
				            </select>

			            </div>
			            <p class="field-custom">
			                <label for="edit-menu-item-ltext-<?php echo esc_attr($item_id); ?>">
			                    <?php echo esc_html__( 'Submenu item label text','mobex' ); ?><br />
			                    <input type="text" id="edit-menu-item-ltext-<?php echo esc_attr($item_id); ?>" class="widefull edit-menu-item-custom" name="menu-item-ltext[<?php echo esc_attr($item_id); ?>]" value="<?php echo esc_attr( $item->ltext ); ?>" />
			                </label>
			            </p>
			            <p class="field-custom">
			                <label for="edit-menu-item-ltextcolor-<?php echo esc_attr($item_id); ?>">
			                    <?php echo esc_html__( 'Submenu item label text color','mobex' ); ?>
			                </label>
			                <input type="text" id="edit-menu-item-ltextcolor-<?php echo esc_attr($item_id); ?>" class="enovathemes-color-picker widefat code edit-menu-item-custom" name="menu-item-ltextcolor[<?php echo esc_attr($item_id); ?>]" value="<?php echo esc_attr( $item->ltextcolor ); ?>" />

			            </p>
			            <p class="field-custom">
			                <label for="edit-menu-item-lcolor-<?php echo esc_attr($item_id); ?>">
			                    <?php echo esc_html__( 'Submenu item label color','mobex' ); ?>
			                </label>
			                <input type="text" id="edit-menu-item-lcolor-<?php echo esc_attr($item_id); ?>" class="enovathemes-color-picker widefat code edit-menu-item-custom" name="menu-item-lcolor[<?php echo esc_attr($item_id); ?>]" value="<?php echo esc_attr( $item->lcolor ); ?>" />

			            </p>
			            <p class="field-custom description description-wide">
			                <label for="edit-menu-item-icon-<?php echo esc_attr($item_id); ?>">
			                    <?php echo esc_html__( 'SVG icon url','mobex' ); ?><br />
			                    <input type="text" id="edit-menu-item-icon-<?php echo esc_attr($item_id); ?>" class="widefull edit-menu-item-custom" name="menu-item-icon[<?php echo esc_attr($item_id); ?>]" value="<?php echo esc_attr( $item->icon ); ?>" />
			                </label>
			            </p>
	            	</div>
	            <?php
	            /* New fields insertion ends here */
	            ?>
		            <div class="menu-item-actions description-wide submitbox">
		                <?php if( 'custom' != $item->type && $original_title !== false ) : ?>
		                    <p class="link-to-original">
		                        <?php printf( esc_html__('Original: %s', 'mobex'), '<a href="' . esc_attr( $item->url ) . '">' . esc_html( $original_title ) . '</a>' ); ?>
		                    </p>
		                <?php endif; ?>
		                <a class="item-delete submitdelete deletion" id="delete-<?php echo esc_attr($item_id); ?>" href="<?php
		                echo wp_nonce_url(
		                    add_query_arg(
		                        array(
		                            'action' => 'delete-menu-item',
		                            'menu-item' => esc_attr($item_id),
		                        ),
		                        remove_query_arg($removed_args, admin_url( 'nav-menus.php' ) )
		                    ),
		                    'delete-menu_item_' . esc_attr($item_id)
		                ); ?>"><?php echo esc_html__('Remove', 'mobex'); ?></a> <span class="meta-sep"> | </span> <a class="item-cancel submitcancel" id="cancel-<?php echo esc_attr($item_id); ?>" href="<?php echo esc_url( add_query_arg( array('edit-menu-item' => esc_attr($item_id), 'cancel' => time()), remove_query_arg( $removed_args, admin_url( 'nav-menus.php' ) ) ) );
		                    ?>#menu-item-settings-<?php echo esc_attr($item_id); ?>"><?php echo esc_html__('Cancel', 'mobex'); ?></a>
			            <input class="menu-item-data-db-id" type="hidden" name="menu-item-db-id[<?php echo esc_attr($item_id); ?>]" value="<?php echo esc_attr($item_id); ?>" />
			            <input class="menu-item-data-object-id" type="hidden" name="menu-item-object-id[<?php echo esc_attr($item_id); ?>]" value="<?php echo esc_attr( $item->object_id ); ?>" />
			            <input class="menu-item-data-object" type="hidden" name="menu-item-object[<?php echo esc_attr($item_id); ?>]" value="<?php echo esc_attr( $item->object ); ?>" />
			            <input class="menu-item-data-parent-id" type="hidden" name="menu-item-parent-id[<?php echo esc_attr($item_id); ?>]" value="<?php echo esc_attr( $item->menu_item_parent ); ?>" />
			            <input class="menu-item-data-position" type="hidden" name="menu-item-position[<?php echo esc_attr($item_id); ?>]" value="<?php echo esc_attr( $item->menu_order ); ?>" />
			            <input class="menu-item-data-type" type="hidden" name="menu-item-type[<?php echo esc_attr($item_id); ?>]" value="<?php echo esc_attr( $item->type ); ?>" />
			       	</div>
		       	</div>
	        </div><!-- .menu-item-settings-->
	        <ul class="menu-item-transport"></ul>
	    <?php

	    $output .= ob_get_clean();

	    }
}
