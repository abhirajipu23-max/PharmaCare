from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.utils import timezone

DEMO_PRODUCTS = [
{ 'id': 1, 'name': 'Paracetamol 500mg', 'price': 49, 'description': 'Pain relief and fever reducer', 'image': 'https://via.placeholder.com/300x200?text=Paracetamol' },
{ 'id': 2, 'name': 'Cough Syrup', 'price': 129, 'description': 'Soothes cough and throat', 'image': 'https://via.placeholder.com/300x200?text=Cough+Syrup' },
{ 'id': 3, 'name': 'Vitamin C 500mg', 'price': 199, 'description': 'Boosts immunity', 'image': 'https://via.placeholder.com/300x200?text=Vitamin+C' },
{ 'id': 4, 'name': 'Antacid Tablets', 'price': 79, 'description': 'Relief from acidity', 'image': 'https://via.placeholder.com/300x200?text=Antacid' },
{ 'id': 5, 'name': 'Allergy Relief', 'price': 149, 'description': 'Relief from seasonal allergies', 'image': 'https://via.placeholder.com/300x200?text=Allergy' },
{ 'id': 6, 'name': 'Multivitamin Capsule', 'price': 249, 'description': 'Daily nutritional support', 'image': 'https://via.placeholder.com/300x200?text=Multivitamin' },
]


def home(request):
    cart = request.session.get('cart', {})
    cart_count = sum(cart.values()) if isinstance(cart, dict) else 0
    context = {
    'products': DEMO_PRODUCTS,
    'cart_count': cart_count,
    'now': timezone.now(),
    }
    return render(request, 'base.html', context)



def user_register(request):
    return render(request, "register.html")


def user_login(request):
    return render(request, "login.html")


def user_profile(request):
    return render(request, "profile.html")


def search_results(request):
    return render(request, "search_results.html")


def cart(request):
    return render(request, "cart.html")