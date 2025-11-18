from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Product, Category

def home(request):
    featured_products = Product.objects.filter(active=True)[:8]
    categories = Category.objects.all()
    return render(request, 'products/home.html', {
        'featured_products': featured_products,
        'categories': categories
    })

def product_list(request):
    products = Product.objects.filter(active=True)
    query = request.GET.get('q')
    category_slug = request.GET.get('category')
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
    
    if category_slug:
        products = products.filter(category__slug=category_slug)
    
    categories = Category.objects.all()
    return render(request, 'products/product_list.html', {
        'products': products,
        'categories': categories,
        'query': query
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, active=True)
    return render(request, 'products/product_detail.html', {'product': product})