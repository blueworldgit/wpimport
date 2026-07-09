<?php

class et_scm_walker extends Walker_Nav_Menu{

	function start_el(&$output, $item, $depth = 0, $args = array(), $id = 0){

		$indent = ( $depth ) ? str_repeat( "\t", $depth ) : '';

		$class_names = '';
		$classes     = empty( $item->classes ) ? array() : (array) $item->classes;
		$class_names = join( ' ', apply_filters( 'nav_menu_css_class', array_filter( $classes ), $item ) );

		$class_names .= ' depth-'.$depth;

		$megamenu_output = '';
		$megamenu_data   = '';

		if (!empty( $item->megamenu_content) && $item->megamenu_content != "select" && !empty( $item->megamenu ) && $item->megamenu == "true") {

			$class_names .= ' mm-true';
			$class_names .= ' menu-item-has-children';

			$megamenu = enovathemes_addons_megamenus();

			if (is_singular('header')) {
				$item->megamenu_ajax = 'false';
			}

			if (!is_wp_error($megamenu)) {
				if (!empty( $item->megamenu_ajax ) && $item->megamenu_ajax == "true") {
					$megamenu_data   .= ' data-megamenu="'.$item->megamenu_content.'"';
					$class_names .= ' mm-ajax';
				} elseif(isset($megamenu[$item->megamenu_content])) {

					$mm_id = $item->megamenu_content;

					$pluginElementor = \Elementor\Plugin::instance();

					$content = (is_plugin_active( 'elementor/elementor.php' )) ? $pluginElementor->frontend->get_builder_content($mm_id,false) : get_the_content($mm_id);

                    $megamenu_html = '<div id="megamenu-'. $mm_id . '" '.implode(' ', $megamenu[$mm_id]['data']).'>';
                        $megamenu_html .= do_shortcode($content);
                    $megamenu_html .= '</div>';

					$megamenu_output .= $megamenu_html;
				}
			}

		}


		$attributes  = (!empty($item->attr_title)) ? ' title="'.esc_attr($item->attr_title).'"' : '';
		$attributes .= (!empty($item->target))     ? ' target="'.esc_attr($item->target).'"' : '';
		$attributes .= (!empty($item->xfn))        ? ' rel="'.esc_attr($item->xfn).'"' : '';
		$attributes .= (!empty($item->url))        ? ' href="'.esc_url($item->url).'"' : '';
		$attributes .= (!empty($item->icon))       ? ' class="mi-link has-icon"' : ' class="mi-link"';

		$prepend = $append  = '';

		if($depth != 0){$append = $prepend = "";}

		if (is_object($args)) {

			$item_output = $args->before;

				$item_output .= '<a'. $attributes .'>';

					if (!empty($item->icon)) {

						if (str_ends_with($item->icon,'.svg')) {
							$icon  = '<span class="menu-icon" style="-webkit-mask: url('.$item->icon.');mask: url('.$item->icon.');"></span>';
						} else {
							$icon  = '<span class="menu-icon img" style="background: url('.$item->icon.');"></span>';
							$class_names .= ' img';
						}

					}

					if(!empty( $item->icon )){$item_output .= $icon;}

					$item_output .= $args->link_before .$prepend.apply_filters( 'the_title', $item->title, $item->ID ).$append.$args->link_after;


					if (!empty( $item->ltext )) {
						$label_color = (!empty( $item->lcolor )) ? esc_attr($item->lcolor) : "#034c8c";
						$label_textcolor = (!empty( $item->ltextcolor )) ? esc_attr($item->ltextcolor) : "#ffffff";
						$item_output .= '<span class="label" data-labelc="'.$label_color.'" style="background-color:'.$label_color.';color:'.$label_textcolor.';">'.esc_attr($item->ltext).'</span>';
					}

					if(!empty( $item->description )) {
						$item_output .='<span class="description">'.esc_attr( $item->description ).'</span>';
					}

				$item_output .= '</a>';

				if (!empty($megamenu_output) && !((\Elementor\Plugin::$instance->editor->is_edit_mode() || \Elementor\Plugin::$instance->preview->is_preview_mode()))) {
					$item_output .= $megamenu_output;
				}

			$item_output .= $args->after;

			if (function_exists('enovathemes_addons_extra_white_space')) {
				$class_names = enovathemes_addons_extra_white_space($class_names);
			}

			$output .= $indent . '<li id="menu-item-'. $item->ID . '" class="'. esc_attr( $class_names ) . '" '.$megamenu_data.'>';
			$output .= apply_filters( 'walker_nav_menu_start_el', $item_output, $item, $depth, $args );

		}

	}

}

class et_scm_walker_light extends Walker_Nav_Menu{

	function start_el(&$output, $item, $depth = 0, $args = array(), $id = 0){

		$indent = ( $depth ) ? str_repeat( "\t", $depth ) : '';

		$class_names = '';
		$classes     = empty( $item->classes ) ? array() : (array) $item->classes;
		$class_names = join( ' ', apply_filters( 'nav_menu_css_class', array_filter( $classes ), $item ) );

		$class_names .= ' depth-'.$depth;

		if (function_exists('enovathemes_addons_extra_white_space')) {
			$class_names = enovathemes_addons_extra_white_space($class_names);
		}

		$output .= $indent . '<li id="menu-item-'. $item->ID . '" class="'. esc_attr( $class_names ) . '">';

			$attributes  = (!empty($item->attr_title)) ? ' title="'.esc_attr($item->attr_title).'"' : '';
			$attributes .= (!empty($item->target))     ? ' target="'.esc_attr($item->target).'"' : '';
			$attributes .= (!empty($item->xfn))        ? ' rel="'.esc_attr($item->xfn).'"' : '';
			$attributes .= (!empty($item->url))        ? ' href="'.esc_url($item->url).'"' : '';
			$attributes .= (!empty($item->icon))       ? ' class="mi-link has-icon"' : ' class="mi-link"';

			$prepend = $append  = '';

			if($depth != 0){$append = $prepend = "";}

			if (is_object($args)) {

				$item_output = $args->before;

					$item_output .= '<a'. $attributes .'>';

						if (!empty($item->icon)) {
							$icon  = '<span class="menu-icon" style="-webkit-mask: url('.$item->icon.');mask: url('.$item->icon.');"></span>';
						}

						if($depth == 0 && !empty( $item->icon )){$item_output .= $icon;}

						$item_output .= $args->link_before .$prepend.apply_filters( 'the_title', $item->title, $item->ID ).$append.$args->link_after;

						if($depth != 0 && !empty( $item->icon )){$item_output .= $icon;}

						if (!empty( $item->ltext )) {
							$label_color = (!empty( $item->lcolor )) ? esc_attr($item->lcolor) : "#034c8c";
							$label_textcolor = (!empty( $item->ltextcolor )) ? esc_attr($item->ltextcolor) : "#ffffff";
							$item_output .= '<span class="label" data-labelc="'.$label_color.'" style="background-color:'.$label_color.';color:'.$label_textcolor.';">'.esc_attr($item->ltext).'</span>';
						}

						if(!empty( $item->description )) {
							$item_output .='<span class="description">'.esc_attr( $item->description ).'</span>';
						}

					$item_output .= '</a>';

				$item_output .= $args->after;

				$output .= apply_filters( 'walker_nav_menu_start_el', $item_output, $item, $depth, $args );

			}

	}

}

?>
