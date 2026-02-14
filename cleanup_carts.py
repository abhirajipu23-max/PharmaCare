import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mr_doctor.settings')
django.setup()

from django.contrib.auth import get_user_model
from cart.models import Cart

User = get_user_model()

def clean_duplicate_carts():
    print("Checking for dup     licate carts...")
    for user in User.objects.all():
        carts = Cart.objects.filter(user=user).order_by('created_at')
        count = carts.count()
        if count > 1:
            print(f"User {user.username} has {count} carts. Cleaning up...")
            # Keep the last one, or merge items? 
            # For simplicity, keep the last created one as active, delete others (or just keep one).
            # Actually, let's keep the one with most items or latest.
            
            latest_cart = carts.last()
            for c in carts:
                if c != latest_cart:
                    print(f"Deleting duplicate cart {c.id}")
                    c.delete()
            print(f"User {user.username} now has 1 cart.")
        else:
            print(f"User {user.username} has {count} cart(s). OK.")

if __name__ == '__main__':
    clean_duplicate_carts()
