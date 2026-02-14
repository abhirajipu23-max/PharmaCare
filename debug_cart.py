import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mr_doctor.settings')
django.setup()

from django.contrib.auth.models import User
from cart.models import Cart, CartItem

def debug_cart():
    try:
        # Assuming the user is 'admin' or the first user
        user = User.objects.first()
        print(f"Checking cart for user: {user.username}")

        # Check for multiple carts
        carts = Cart.objects.filter(user=user)
        print(f"Found {carts.count()} carts for this user.")

        if carts.count() > 1:
            print("WARNING: Multiple carts found! This causes get_or_create to crash.")
            for c in carts:
                print(f" - Cart ID: {c.id}, Created: {c.created_at}")

        # Try to simulate the view logic
        try:
            cart, created = Cart.objects.get_or_create(user=user)
            print(f"Cart retrieval successful. ID: {cart.id}")
            
            print("Items in cart:")
            for item in cart.items.all():
                print(f" - {item.product.name} (Qty: {item.quantity}, Price: {item.product.price})")
                print(f"   Subtotal: {item.get_subtotal()}")
            
            total = cart.get_total()
            print(f"Total Cart Value: {total}")

        except Exception as e:
            print(f"ERROR in view logic: {e}")

    except Exception as e:
        print(f"General Error: {e}")

if __name__ == '__main__':
    debug_cart()
