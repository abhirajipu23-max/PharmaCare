import os
import django
import random
from django.utils.text import slugify

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mr_doctor.settings')
django.setup()

from products.models import Product, Category

def populate():
    print("Populating database with sample data...")

    # 1. Create Categories
    categories_data = [
        'Medicines',
        'Vitamins',
        'Diabetes',
        'Devices',
        'Ayurveda',
        'Baby Care'
    ]
    
    categories = {}
    for cat_name in categories_data:
        cat, created = Category.objects.get_or_create(
            name=cat_name,
            defaults={'slug': slugify(cat_name), 'description': f'All {cat_name} products'}
        )
        categories[cat_name] = cat
        if created:
            print(f"Created Category: {cat_name}")
        else:
            print(f"Category {cat_name} already exists")

    # 2. Create Products
    products_data = [
        {
            'name': 'CardioGuard 10mg Tablets (Strip of 15)',
            'category': 'Medicines',
            'price': 45.50,
            'description': 'Maintains healthy heart rhythm. Prescription required.',
            'requires_prescription': True,
            'stock': 100
        },
        {
            'name': 'FastRelief Extra Strength Gel',
            'category': 'Medicines',
            'price': 12.99,
            'description': 'Rapid action pain reliever for muscle and joint pain.',
            'requires_prescription': False,
            'stock': 50
        },
        {
            'name': 'VitaBoost Multi-Vitamin Immunity',
            'category': 'Vitamins',
            'price': 19.99,
            'description': 'Vitamin C, D, and Zinc support for daily immunity.',
            'requires_prescription': False,
            'stock': 200
        },
        {
            'name': 'SoftTouch Baby Lotion (200ml)',
            'category': 'Baby Care',
            'price': 8.50,
            'description': 'Hypoallergenic & Gentle lotion for delicate baby skin.',
            'requires_prescription': False,
            'stock': 75
        },
        {
            'name': 'AccuCheck Instant Glucometer',
            'category': 'Diabetes',
            'price': 25.00,
            'description': 'Instant blood glucose monitoring system with 10 strips.',
            'requires_prescription': False,
            'stock': 30
        },
        {
            'name': 'Chyawanprash Immunity Booster',
            'category': 'Ayurveda',
            'price': 15.00,
            'description': 'Traditional ayurvedic formula for health and immunity.',
            'requires_prescription': False,
            'stock': 60
        },
        {
            'name': 'Digital Thermometer',
            'category': 'Devices',
            'price': 12.50,
            'description': 'Fast and accurate digital thermometer for fever measurement.',
            'requires_prescription': False,
            'stock': 150
        }
    ]

    for prod in products_data:
        category = categories.get(prod['category'])
        if not category:
            print(f"Skipping {prod['name']}, category not found.")
            continue

        product, created = Product.objects.get_or_create(
            name=prod['name'],
            defaults={
                'slug': slugify(prod['name']),
                'category': category,
                'price': prod['price'],
                'description': prod['description'],
                'requires_prescription': prod['requires_prescription'],
                'stock': prod['stock'],
                'active': True
            }
        )
        if created:
            print(f"Created Product: {prod['name']}")
        else:
            print(f"Product {prod['name']} already exists")

    print("\nDone! Database populated successfully.")

if __name__ == '__main__':
    populate()
