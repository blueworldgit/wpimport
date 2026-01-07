# WordPress SVG Support Setup

Two options to enable SVG uploads in WordPress:

## Option 1: Plugin (Recommended - Safer)

Install the **Safe SVG** plugin:

1. Go to WordPress Admin → Plugins → Add New
2. Search for "Safe SVG"
3. Install and activate "Safe SVG" by 10up
4. That's it! SVG uploads are now enabled and sanitized

**Benefits:**
- Sanitizes SVG files for security
- Simple one-click solution
- No code changes needed

---

## Option 2: Code Snippet (Manual)

Add this code to your theme's `functions.php` or use a code snippets plugin:

```php
<?php
/**
 * Enable SVG Upload Support
 */
function enable_svg_upload($mimes) {
    $mimes['svg'] = 'image/svg+xml';
    $mimes['svgz'] = 'image/svg+xml';
    return $mimes;
}
add_filter('upload_mimes', 'enable_svg_upload');

/**
 * Fix SVG Display in Media Library
 */
function fix_svg_display($response, $attachment, $meta) {
    if ($response['mime'] === 'image/svg+xml') {
        $svg_path = get_attached_file($attachment->ID);
        
        if (file_exists($svg_path)) {
            // Get SVG dimensions
            $svg = simplexml_load_file($svg_path);
            if ($svg) {
                $attributes = $svg->attributes();
                $width = (int) $attributes->width;
                $height = (int) $attributes->height;
                
                // If no dimensions, use viewBox
                if (!$width || !$height) {
                    $viewBox = (string) $attributes->viewBox;
                    if ($viewBox) {
                        $viewBoxArr = explode(' ', $viewBox);
                        if (count($viewBoxArr) >= 4) {
                            $width = (int) $viewBoxArr[2];
                            $height = (int) $viewBoxArr[3];
                        }
                    }
                }
                
                // Default dimensions if still not found
                if (!$width) $width = 800;
                if (!$height) $height = 600;
                
                $response['width'] = $width;
                $response['height'] = $height;
                
                // Add sizes for compatibility
                $response['sizes'] = array(
                    'full' => array(
                        'url' => $response['url'],
                        'width' => $width,
                        'height' => $height,
                    )
                );
            }
        }
    }
    return $response;
}
add_filter('wp_prepare_attachment_for_js', 'fix_svg_display', 10, 3);

/**
 * Display SVG in Media Library (Admin)
 */
function svg_media_library_display($content, $post_id) {
    $attachment = get_post($post_id);
    if ($attachment && $attachment->post_mime_type === 'image/svg+xml') {
        $svg_url = wp_get_attachment_url($post_id);
        $content = '<img src="' . esc_url($svg_url) . '" style="width: 100%; height: auto;">';
    }
    return $content;
}
add_filter('wp_admin_attachment_thumbnail', 'svg_media_library_display', 10, 2);
```

### Where to add this code:

#### Using Code Snippets Plugin (Recommended):
1. Install "Code Snippets" plugin
2. Go to Snippets → Add New
3. Paste the code above
4. Set to run everywhere
5. Save and activate

#### Or in theme's functions.php:
1. Go to Appearance → Theme File Editor
2. Select `functions.php`
3. Add the code at the end
4. Click "Update File"

---

## Verify SVG Support

After enabling SVG support:

1. Go to Media → Add New
2. Try uploading a `.svg` file
3. If successful, SVG support is working!

---

## Security Note

SVGs can contain JavaScript and pose security risks. The **Safe SVG plugin** sanitizes uploads. If using the code method, only allow trusted users to upload SVGs, or add SVG sanitization library like:

- DOMPurify for SVG sanitization
- Or use Safe SVG plugin for production

---

## For WooCommerce Products

Once SVG support is enabled:

1. SVGs can be uploaded like any image
2. Will display in product galleries
3. Scale perfectly at any size
4. Much better for technical diagrams than PNGs

---

## Testing

Upload the extracted SVG:
```
images/converted/LSFAL11A4PA157987_Body_Interior_&_Exterior_Electronics.svg
```

Check if it displays correctly in:
- Media Library
- Product image
- Frontend product page
