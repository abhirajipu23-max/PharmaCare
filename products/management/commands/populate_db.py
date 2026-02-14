from django.core.management.base import BaseCommand
from products.models import Category, Product
from django.utils.text import slugify
import random

class Command(BaseCommand):
    help = 'Populates the database with dummy products'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating database...')

        categories = {
            'Medicines': ['Paracetamol', 'Ibuprofen', 'Antibiotic', 'Pain Relief', 'Cough Syrup', 'Antacid', 'Allergy Pill', 'Eye Drops', 'Nasal Spray', 'Ointment'],
            'Vitamins': ['Multivitamin', 'Vitamin C', 'Vitamin D3', 'B12 Complex', 'Omega 3', 'Zinc', 'Calcium', 'Magnesium', 'Iron Supplement', 'Biotin'],
            'Diabetes': ['Glucometer', 'Test Strips', 'Insulin Pen', 'Sugar Free Tablets', 'Diabetic Socks', 'Foot Cream', 'Needles', 'Lancets', 'Glucose Gel', 'Monitor Case'],
            'Devices': ['Thermometer', 'BP Monitor', 'Oximeter', 'Nebulizer', 'Heating Pad', 'Massager', 'Weight Scale', 'Steamer', 'Support Belt', 'Walker'],
            'Ayurveda': ['Chyawanprash', 'Triphala', 'Ashwagandha', 'Neem Tablets', 'Tulsi Drops', 'Hair Oil', 'Face Pack', 'Digestive Powder', 'Joint Oil', 'Immunity Booster'],
            'Baby Care': ['Diapers', 'Baby Oil', 'Baby Powder', 'Wipes', 'Baby Shampoo', 'Lotion', 'Rash Cream', 'Feeding Bottle', 'Pacifier', 'Teether'],
        }

        prefixes = ['Ultra', 'Max', 'Pro', 'Neo', 'Bio', 'Vital', 'Pure', 'Safe', 'Medi', 'Cure', 'Life', 'Health']
        suffixes = ['Plus', 'Forte', 'Extra', 'Advanced', 'Care', 'Guard', 'Shield', 'Ease', 'Relief', 'Glow', 'Active', 'Fit']

        # Ensure categories exist
        for cat_name, items in categories.items():
            category, created = Category.objects.get_or_create(
                name=cat_name,
                defaults={'slug': slugify(cat_name), 'description': f'All kinds of {cat_name}'}
            )
            
            self.stdout.write(f'Processing Category: {cat_name}')
            
            # Generate 50 products for each category
            count = 0
            while count < 50:
                base_item = random.choice(items)
                prefix = random.choice(prefixes)
                suffix = random.choice(suffixes)
                
                # Create a unique name
                name = f"{prefix} {base_item} {suffix}"
                
                # Check if exists to avoid slug collision
                if not Product.objects.filter(name=name).exists():
                    price = round(random.uniform(50.00, 5000.00), 2)
                    stock = random.randint(10, 100)
                    
                    Product.objects.create(
                        name=name,
                        slug=slugify(name),
                        category=category,
                        description=f"High quality {base_item} by {prefix} {suffix}. Genuine product for your needs.",
                        price=price,
                        stock=stock,
                        requires_prescription=(cat_name == 'Medicines' and random.choice([True, False])),
                        active=True
                    )
                    count += 1
            
            self.stdout.write(self.style.SUCCESS(f'Successfully added 50 products to {cat_name}'))

        self.stdout.write(self.style.SUCCESS('Database population complete!'))
