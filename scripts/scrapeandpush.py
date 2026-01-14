import os
import sys
import django
from bs4 import BeautifulSoup
import logging

print("hello")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'epcdata.settings')

# Setup Django
django.setup()

# Import your serializers
from motorpartsdata.serializers import (
    SerialNumberSerializer,
    ParentTitleSerializer,
    ChildTitleSerializer,
    PartSerializer
)
from vehicle_utils import determine_vehicle_brand

def process_html_file(html_path, serial_instance, parent_instance):
    """Process an HTML file using your existing BeautifulSoup parsing logic"""
    try:
        logger.info(f"Processing file: {html_path}")
        
        with open(html_path, 'r', encoding='utf-8') as file:
            html = file.read()
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract the title from legend-title
        legend_title = soup.find('span', id='legend-title')
        title_content = legend_title.text.strip() if legend_title else os.path.basename(html_path).replace('.html', '')
        
        # Extract SVG code
        svg_element = soup.find('svg', attrs={"xmlns": "http://www.w3.org/2000/svg"})
        svg_content = str(svg_element) if svg_element else "<svg></svg>"
        
        # Create child title record
        child_data = {
            "title": title_content,
            "parent": parent_instance.id,
            "svg_code": svg_content,
        }
        
        child_serializer = ChildTitleSerializer(data=child_data)
        if child_serializer.is_valid():
            child_instance = child_serializer.save()
            logger.info(f"Created child title: {title_content}")
            
            # Now extract parts data using your approach
            # Get the extra information first (orientation and remarks)
            extra = []
            
            try:
                container = soup.find('div', class_='condition-entity')
                if container:
                    right_div = container.find('div', class_='parts-table-tbody parts-table-tbody-dflz')
                    if right_div:
                        right_rows = right_div.find_all('div', class_='parts-item')
                        filtered_items = [item for item in right_rows if 'dn' not in item.get('class', [])]
                        
                        for item in filtered_items:
                            first_column = item.find(lambda tag: tag.name == "span" and tag.get("class") == ["column"])
                            orientation = first_column.text.strip() if first_column else "N/A"
                            
                            note_column = item.select_one('.text-column-note span')
                            remark = note_column.text.strip() if note_column else "N/A"
                            
                            extra.append({
                                'orientation': orientation,
                                'remark': remark
                            })
            except Exception as e:
                logger.warning(f"Error extracting extra info: {str(e)}")
                
            # Get the main parts data
            parts_items = soup.find_all(lambda tag: tag.name == "div" and 
                                    "parts-item" in tag.get("class", []) and 
                                    tag.has_attr("data-callout"))
            
            filtered_items = [item for item in parts_items if 'dn' not in item.get('class', [])]
            count=0
            for item in filtered_items:
                try:
                    # Get orientation and notes from extra if available
                    orientation = extra[count]['orientation'] if count < len(extra) else "N/A"
                    notes = extra[count]['remark'] if count < len(extra) else "N/A"
                    
                    # Extract all the other fields
                    order_number_elem = item.select_one('.column.ordernumber')
                    order_number = order_number_elem.text.strip() if order_number_elem else "N/A"
                    
                    part_number_elem = item.select_one('.part-number a.text-link')
                    part_number = part_number_elem.text.strip() if part_number_elem else "N/A"
                    
                    description_elem = item.select_one('.column.describe')
                    description = description_elem.text.strip() if description_elem else "N/A"
                    
                    quantity_elem = item.select_one('.column.quantity')
                    quantity = quantity_elem.text.strip() if quantity_elem else "1"
                    
                    # Skip this item if any required field is "N/A"
                    if "N/A" in [order_number, part_number, description]:
                        continue
                    
                    # Create part record
                    part_data = {
                        "child_title": child_instance.id,
                        "call_out_order": int(order_number) if order_number.isdigit() else count + 1,
                        "part_number": part_number,
                        "usage_name": description,
                        "unit_qty": quantity,
                        "lr": orientation,
                        "remark": notes,
                        "nn_note": "",  # You can add note handling if needed
                    }

                    count+=1
                    
                    part_serializer = PartSerializer(data=part_data)
                    if part_serializer.is_valid():
                        part_serializer.save()
                        logger.info(f"Created part: {part_data['part_number']} - {part_data['usage_name']}")
                    else:
                        logger.error(f"Part serializer errors: {part_serializer.errors}")
                except Exception as e:
                    logger.warning(f"Error processing part {count}: {str(e)}")
        else:
            logger.error(f"Child title serializer errors: {child_serializer.errors}")
    
    except Exception as e:
        logger.error(f"Error processing {html_path}: {str(e)}")


def process_directory(root_dir):
    """Walk through the directory structure and process HTML files"""
    try:
        # Extract serial number from the root directory name
        serial_name = os.path.basename(root_dir)
        
        # Determine vehicle brand based on serial number patterns or default to Maxus
        vehicle_brand = determine_vehicle_brand(serial_name)
        
        serial_data = {
            "serial": serial_name,
            "vehicle_brand": vehicle_brand
        }
        
        # Check if this serial already exists
        from motorpartsdata.models import SerialNumber
        existing_serial = SerialNumber.objects.filter(serial=serial_name).first()
        
        if existing_serial:
            logger.info(f"Serial number {serial_name} already exists, using it")
            # Update the vehicle brand if it's different
            if existing_serial.vehicle_brand != vehicle_brand:
                existing_serial.vehicle_brand = vehicle_brand
                existing_serial.save()
                logger.info(f"Updated vehicle brand for {serial_name} to {vehicle_brand}")
            serial_instance = existing_serial
        else:
            serial_serializer = SerialNumberSerializer(data=serial_data)
            if serial_serializer.is_valid():
                serial_instance = serial_serializer.save()
                logger.info(f"Created serial number: {serial_data['serial']} for brand: {vehicle_brand}")
            else:
                logger.error(f"Serial number serializer errors: {serial_serializer.errors}")
                return
        
        # Walk through the directory structure
        for dirpath, dirnames, filenames in os.walk(root_dir):
            relative_path = os.path.relpath(dirpath, root_dir)
            
            # Skip the root directory itself
            if relative_path == '.':
                continue
                
            # Create parent title record for each directory (if there are HTML files)
            html_files = [f for f in filenames if f.lower().endswith('.html')]
            if html_files:
                parent_name = os.path.basename(dirpath)
                # Replace underscores and handle other formatting if needed
                parent_name = parent_name.replace('_', ' ').title()
                
                parent_data = {
                    "title": parent_name,
                    "serial_number": serial_instance.id
                }
                
                # Check if this parent already exists
                from motorpartsdata.models import ParentTitle
                existing_parent = ParentTitle.objects.filter(
                    title=parent_name, 
                    serial_number=serial_instance
                ).first()
                
                if existing_parent:
                    logger.info(f"Parent title {parent_name} already exists, using it")
                    parent_instance = existing_parent
                else:
                    parent_serializer = ParentTitleSerializer(data=parent_data)
                    if parent_serializer.is_valid():
                        parent_instance = parent_serializer.save()
                        logger.info(f"Created parent title: {parent_data['title']}")
                    else:
                        logger.error(f"Parent title serializer errors: {parent_serializer.errors}")
                        continue
                
                # Process HTML files in this directory
                for filename in html_files:
                    file_path = os.path.join(dirpath, filename)
                    process_html_file(file_path, serial_instance, parent_instance)
    
    except Exception as e:
        logger.error(f"Error processing directory {root_dir}: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        root_directory = sys.argv[1]
        logger.info(f"Starting processing for directory: {root_directory}")
        process_directory(root_directory)
        logger.info("Processing complete")
    else:
        logger.error("Please provide the root directory path as an argument")
        print("Usage: python scraper.py /path/to/root/directory")