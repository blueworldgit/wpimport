import os
import sys
import django
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper_oscar.log"),
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

from motorpartsdata.models import Part, ChildTitle, ParentTitle, SerialNumber
from oscar.apps.catalogue.models import Product, Category, ProductClass
from oscar.apps.partner.models import StockRecord
from django.utils.text import slugify
from django.db import transaction

def get_child_category(child_title):
    """Find the Oscar category for a given ChildTitle instance."""
    name = f"Child: {child_title.title}"
    return Category.objects.filter(name=name).first()

def get_or_create_product_class():
    """Get or create a generic product class for parts."""
    pc, _ = ProductClass.objects.get_or_create(name="Part")
    return pc

def create_oscar_product_for_part(part):
    child_title = part.child_title
    category = get_child_category(child_title)
    if not category:
        logger.warning(f"No Oscar category found for child title: {child_title.title}")
        return None
    product_class = get_or_create_product_class()
    title = part.usage_name or part.part_number
    upc = part.part_number
    slug = slugify(f"{title}-{upc}")
    # Check if product already exists
    product = Product.objects.filter(upc=upc).first()
    if product:
        logger.info(f"Product already exists for part_number {upc}")
        return product
    # Create product
    with transaction.atomic():
        product = Product.objects.create(
            title=title,
            upc=upc,
            product_class=product_class,
            slug=slug
        )
        product.categories.add(category)
        # Optionally create a stock record
        StockRecord.objects.create(
            product=product,
            partner_sku=upc,
            price_excl_tax=0,
            num_in_stock=part.unit_qty if hasattr(part, 'unit_qty') and str(part.unit_qty).isdigit() else 0
        )
        logger.info(f"Created Oscar product: {title} (UPC: {upc}) in category {category}")
    return product

def main():
    logger.info("Starting Oscar product creation for all parts...")
    parts = Part.objects.all()
    count = 0
    for part in parts:
        product = create_oscar_product_for_part(part)
        if product:
            count += 1
    logger.info(f"Created/linked {count} Oscar products.")
    logger.info("Done.")

if __name__ == "__main__":
    main()
