from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Cart, CartItem
from products.models import Product, Order, OrderItem

@login_required
def cart_detail(request):
    # Ensure only one cart exists
    carts = Cart.objects.filter(user=request.user)
    if carts.exists():
        cart = carts.last()
        if carts.count() > 1:
            # Delete older duplicates if they exist
            carts.exclude(id=cart.id).delete()
    else:
        cart = Cart.objects.create(user=request.user)
    
    return render(request, 'cart/cart_detail.html', {'cart': cart})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # robust cart retrieval
    carts = Cart.objects.filter(user=request.user)
    if carts.exists():
        cart = carts.last()
    else:
        cart = Cart.objects.create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f'{product.name} added to cart!')
    return redirect('cart:cart_detail')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, 'Item removed from cart!')
    return redirect('cart:cart_detail')

@login_required
def update_cart(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
    
    return redirect('cart:cart_detail')

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    
    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address')
        
        order = Order.objects.create(
            user=request.user,
            total_price=cart.get_total(),
            shipping_address=shipping_address
        )
        
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
        
        cart.items.all().delete()
        messages.success(request, 'Order placed successfully!')
        return redirect('products:home')
    
    return render(request, 'cart/checkout.html', {'cart': cart})





from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Cart
from .serializers import CartSerializer

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    queryset = Cart.objects.none()  # REQUIRED

    def get_queryset(self):
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
        return Cart.objects.filter(session_key=self.request.session.session_key)

    def perform_create(self, serializer):
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
        serializer.save(session_key=self.request.session.session_key)

    @action(detail=True, methods=["get"])
    def schedule(self, request, pk=None):
        cart = self.get_object()
        return Response({
            "cart_id": cart.id,
            "total": cart.get_total(),
            "created_at": cart.created_at,
        })