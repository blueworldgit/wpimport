<?php

class ET_Mobex_Custom_Menu {

	/*--------------------------------------------*
	 * Constructor
	 *--------------------------------------------*/

	/**
	 * Initializes the plugin by setting localization, filters, and administration functions.
	 */
	function __construct() {

		// add custom menu fields to menu
		add_filter( 'wp_setup_nav_menu_item', array( $this, 'mobex_enovathemes_scm_add_custom_nav_fields' ) );

		// save menu custom fields
		add_action( 'wp_update_nav_menu_item', array( $this, 'mobex_enovathemes_scm_update_custom_nav_fields'), 10, 3 );
		
		// edit menu walker
		add_filter( 'wp_edit_nav_menu_walker', array( $this, 'mobex_enovathemes_scm_edit_walker'), 10, 2 );

	} // end constructor
	
	
	/**
	 * Add custom fields to $item nav object
	 * in order to be used in custom Walker
	 *
	 * @access      public
	 * @since       1.0 
	 * @return      void
	*/
	function mobex_enovathemes_scm_add_custom_nav_fields( $menu_item ) {
	
	    $menu_item->icon             = get_post_meta( $menu_item->ID, '_menu_item_icon', true );
	    $menu_item->megamenu         = get_post_meta( $menu_item->ID, '_menu_item_megamenu', true );
	    $menu_item->megamenu_ajax    = get_post_meta( $menu_item->ID, '_menu_item_megamenu_ajax', true );
	    $menu_item->megamenu_content = get_post_meta( $menu_item->ID, '_menu_item_megamenu_content', true );
	    $menu_item->lcolor           = get_post_meta( $menu_item->ID, '_menu_item_lcolor', true );
	    $menu_item->ltextcolor       = get_post_meta( $menu_item->ID, '_menu_item_ltextcolor', true );
	    $menu_item->ltext            = get_post_meta( $menu_item->ID, '_menu_item_ltext', true );
	    return $menu_item;
	}
	
	/**
	 * Save menu custom fields
	 *
	 * @access      public
	 * @since       1.0 
	 * @return      void
	*/
	function mobex_enovathemes_scm_update_custom_nav_fields( $menu_id, $menu_item_db_id, $args ) {
	
	    // Check if element is properly sent

		if (isset($_REQUEST['menu-item-icon']) && is_array( $_REQUEST['menu-item-icon']) ) {
	        $icon_value = $_REQUEST['menu-item-icon'][$menu_item_db_id];
	        update_post_meta( $menu_item_db_id, '_menu_item_icon', $icon_value );
	    }

	    if (isset($_REQUEST['menu-item-megamenu']) && is_array( $_REQUEST['menu-item-megamenu']) ) {
	        $megamenu_value = $_REQUEST['menu-item-megamenu'][$menu_item_db_id];
	        update_post_meta( $menu_item_db_id, '_menu_item_megamenu', $megamenu_value );
	    }

	    if (isset($_REQUEST['menu-item-megamenu-ajax']) && is_array( $_REQUEST['menu-item-megamenu-ajax']) ) {
	        $megamenu_value = $_REQUEST['menu-item-megamenu-ajax'][$menu_item_db_id];
	        update_post_meta( $menu_item_db_id, '_menu_item_megamenu_ajax', $megamenu_value );
	    }

	    if (isset($_REQUEST['menu-item-megamenu_content']) && is_array( $_REQUEST['menu-item-megamenu_content']) ) {
	        $megamenu_content_value = $_REQUEST['menu-item-megamenu_content'][$menu_item_db_id];
	        update_post_meta( $menu_item_db_id, '_menu_item_megamenu_content', $megamenu_content_value );
	    }
		
	    if (isset($_REQUEST['menu-item-lcolor']) && is_array( $_REQUEST['menu-item-lcolor']) ) {
	        $lcolor_value = $_REQUEST['menu-item-lcolor'][$menu_item_db_id];
	        update_post_meta( $menu_item_db_id, '_menu_item_lcolor', $lcolor_value );
	    }

	    if (isset($_REQUEST['menu-item-ltextcolor']) && is_array( $_REQUEST['menu-item-ltextcolor']) ) {
	        $ltextcolor_value = $_REQUEST['menu-item-ltextcolor'][$menu_item_db_id];
	        update_post_meta( $menu_item_db_id, '_menu_item_ltextcolor', $ltextcolor_value );
	    }

	    if (isset($_REQUEST['menu-item-ltext']) && is_array( $_REQUEST['menu-item-ltext']) ) {
	        $ltext_value = $_REQUEST['menu-item-ltext'][$menu_item_db_id];
	        update_post_meta( $menu_item_db_id, '_menu_item_ltext', $ltext_value );
	    }
	}
	
	/**
	 * Define new Walker edit
	 *
	 * @access      public
	 * @since       1.0 
	 * @return      void
	*/
	function mobex_enovathemes_scm_edit_walker($walker,$menu_id) {
	
	    return 'Walker_Nav_Menu_Edit_Custom';
	    
	}

}

// instantiate plugin's class
$GLOBALS['custom_menu'] = new ET_Mobex_Custom_Menu();

include_once( get_template_directory() .'/includes/menu/edit_custom_walker.php' );
include_once( get_template_directory() .'/includes/menu/custom_walker.php' );