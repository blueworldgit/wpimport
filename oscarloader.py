import os
import json
import logging
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'epcdata.settings')
django.setup()

from motorpartsdata.models import Part, PricingData
from rest_framework import serializers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pricing_loader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create a simple serializer for PricingData
class PricingDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingData
        fields = '__all__'

# Index mapping based on the comments in models.py
INDEX_MAPPING = {
    3: 'part_number_value',  # Used to lookup Part instance
    8: 'replacement',        # index 8
    4: 'description',        # index 4
    5: 'active',            # index 5
    10: 'oldest',           # index 10
    55: 'range_code',       # index 55
    13: 'discount_code',    # index 13
    14: 'class_code',       # index 14
    22: 'vat_code',         # index 22
    24: 'list_price',       # index 24
    29: 'vor',              # index 29
    34: 'stock_order',      # index 34
    41: 'replacement_code', # index 41
}

def extract_value_from_inputs(all_inputs, index):
    """Extract value from allInputs array by index"""
    try:
        if index < len(all_inputs):
            input_item = all_inputs[index]
            if isinstance(input_item, dict):
                return input_item.get('value', '')
            else:
                return str(input_item) if input_item else ''
        return ''
    except (IndexError, TypeError):
        return ''

def process_json_file(json_path):
    """Process a single JSON file and extract pricing data"""
    try:
        logger.info(f"Processing file: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Extract the allInputs directly from the root level
        all_inputs = data.get('allInputs', [])
        
        # Extract warehouse stock data
        whs_stock = data.get('whs_stock', {})
        whs = whs_stock.get('whs', '')
        stock_available = whs_stock.get('stock_available', '')
        
        # Extract values based on index mapping
        extracted_data = {}
        for index, field_name in INDEX_MAPPING.items():
            value = extract_value_from_inputs(all_inputs, index)
            extracted_data[field_name] = value
            print(f"DEBUG: index {index} maps to '{field_name}' with value: '{value}'")  # Debug output

        # Get the part number value to lookup the Part instance
        part_number_value = extracted_data.pop('part_number_value', '')
        
        if not part_number_value:
            logger.warning(f"No part number found in {json_path}")
            return
        
        # Look up all Part instances with this part number
        part_instances = Part.objects.filter(part_number=part_number_value)
        
        if not part_instances.exists():
            # Extract part number from filename as fallback
            filename = os.path.basename(json_path)
            filename_part_number = filename.replace('.json', '')
            
            logger.warning(f"Part with number '{part_number_value}' not found in database, trying filename part number '{filename_part_number}'")
            
            # Try searching with the filename part number
            part_instances = Part.objects.filter(part_number=filename_part_number)
            
            if not part_instances.exists():
                logger.error(f"Part with number '{filename_part_number}' (from filename) also not found in database")
                return
            else:
                logger.info(f"Found part(s) using filename part number '{filename_part_number}'")
                # Update the part_number_value for logging purposes
                part_number_value = filename_part_number
        
        logger.info(f"Found {part_instances.count()} parts with number '{part_number_value}'")
        
        # Create pricing data for ALL parts with this part number that don't already have it
        success_count = 0
        skipped_count = 0
        
        for part_instance in part_instances:
            # Check if THIS specific part instance already has pricing data
            if PricingData.objects.filter(part_number=part_instance).exists():
                logger.info(f"Pricing data already exists for part ID {part_instance.id} with number {part_number_value}, skipping this instance")
                skipped_count += 1
                continue
            
            # Prepare the pricing data for this specific part instance
            pricing_data = {
                'part_number': part_instance.id,
                'whs': whs,
                'stock_available': stock_available,
                **extracted_data  # Add all the extracted field data
            }
            
            # Create the pricing data record
            pricing_serializer = PricingDataSerializer(data=pricing_data)
            if pricing_serializer.is_valid():
                pricing_serializer.save()
                success_count += 1
                logger.info(f"Created pricing data for part ID {part_instance.id} with number: {part_number_value}")
            else:
                logger.error(f"Pricing data serializer errors for part ID {part_instance.id} with number {part_number_value}: {pricing_serializer.errors}")
        
        if skipped_count > 0:
            logger.info(f"Skipped {skipped_count} parts that already had pricing data")
        logger.info(f"Successfully created pricing data for {success_count} of {part_instances.count()} parts with number {part_number_value}")
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {json_path}: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing {json_path}: {str(e)}")

def process_folder(folder_path):
    """Process all JSON files in a folder"""
    if not os.path.exists(folder_path):
        logger.error(f"Folder does not exist: {folder_path}")
        return
    
    if not os.path.isdir(folder_path):
        logger.error(f"Path is not a directory: {folder_path}")
        return
    
    json_files = []
    for file_name in os.listdir(folder_path):
        if file_name.lower().endswith('.json'):
            json_files.append(os.path.join(folder_path, file_name))
    
    if not json_files:
        logger.warning(f"No JSON files found in folder: {folder_path}")
        return
    
    logger.info(f"Found {len(json_files)} JSON files to process")
    
    success_count = 0
    error_count = 0
    
    for json_file in json_files:
        try:
            process_json_file(json_file)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to process {json_file}: {str(e)}")
            error_count += 1
    
    logger.info(f"Processing complete. Success: {success_count}, Errors: {error_count}")

def main():
    """Main function to run the pricing data loader"""
    import sys
    
    # Check for command-line argument
    if len(sys.argv) != 2:
        print("Usage: python loadprices.py <folder_path>")
        print("Example: python loadprices.py output_20250701_112614")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    
    # If it's a relative path, make it absolute based on current working directory
    if not os.path.isabs(folder_path):
        folder_path = os.path.join(os.getcwd(), folder_path)
    
    logger.info(f"Starting pricing data loading from folder: {folder_path}")
    
    try:
        process_folder(folder_path)
        logger.info("Pricing data loading completed successfully")
    except Exception as e:
        logger.error(f"Fatal error during processing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()