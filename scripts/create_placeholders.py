"""
Create placeholder images for WooCommerce products
Generates 3 placeholder images: General, Left, Right
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_placeholder(text, output_path, width=2000, height=1500, badge_text=None):
    """
    Create a placeholder image with text
    
    Args:
        text: Main text to display
        output_path: Path to save the image
        width: Image width in pixels
        height: Image height in pixels
        badge_text: Optional badge text (e.g., "LEFT", "RIGHT")
    """
    # Create white background
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add border
    border_color = '#cccccc'
    draw.rectangle([(10, 10), (width-10, height-10)], outline=border_color, width=5)
    
    # Try to load a nice font, fallback to default
    try:
        font_large = ImageFont.truetype("arial.ttf", 80)
        font_badge = ImageFont.truetype("arialbd.ttf", 120)
    except:
        try:
            font_large = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 80)
            font_badge = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 120)
        except:
            font_large = ImageFont.load_default()
            font_badge = ImageFont.load_default()
    
    # Center main text
    text_bbox = draw.textbbox((0, 0), text, font=font_large)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_position = ((width - text_width) // 2, (height - text_height) // 2)
    
    draw.text(text_position, text, fill='#666666', font=font_large)
    
    # Add badge if provided
    if badge_text:
        badge_bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
        badge_width = badge_bbox[2] - badge_bbox[0]
        badge_height = badge_bbox[3] - badge_bbox[1]
        
        # Position badge in top-right corner
        badge_x = width - badge_width - 100
        badge_y = 100
        
        # Draw badge background (semi-transparent effect with rounded rectangle)
        padding = 40
        badge_bg = [
            (badge_x - padding, badge_y - padding),
            (badge_x + badge_width + padding, badge_y + badge_height + padding)
        ]
        
        # Draw badge
        if badge_text == "LEFT":
            badge_color = '#3498db'  # Blue
        elif badge_text == "RIGHT":
            badge_color = '#e74c3c'  # Red
        else:
            badge_color = '#95a5a6'  # Gray
            
        draw.rectangle(badge_bg, fill=badge_color)
        draw.text((badge_x, badge_y), badge_text, fill='white', font=font_badge)
    
    # Save
    img.save(output_path, 'PNG')
    print(f"✓ Created placeholder: {output_path}")
    return output_path


def main():
    """Generate all 3 placeholder images"""
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'images', 'placeholders')
    
    print("\n" + "="*60)
    print("Creating Placeholder Images for WooCommerce")
    print("="*60 + "\n")
    
    # Create the 3 placeholders
    placeholders = [
        {
            'text': 'Diagram Image Coming Soon',
            'output': os.path.join(output_dir, 'placeholder_general.png'),
            'badge': None
        },
        {
            'text': 'Diagram Image Coming Soon',
            'output': os.path.join(output_dir, 'placeholder_left.png'),
            'badge': 'LEFT'
        },
        {
            'text': 'Diagram Image Coming Soon',
            'output': os.path.join(output_dir, 'placeholder_right.png'),
            'badge': 'RIGHT'
        }
    ]
    
    for placeholder in placeholders:
        create_placeholder(
            text=placeholder['text'],
            output_path=placeholder['output'],
            badge_text=placeholder['badge']
        )
    
    print("\n" + "="*60)
    print("✓ All placeholder images created successfully!")
    print(f"Location: {output_dir}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
