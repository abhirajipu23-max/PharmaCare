from rest_framework import serializers
from . models import Cart, CartItem


from rest_framework import serializers
from .models import Cart

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = "__all__"



class CartItemSerializer(serializers.ModelSerializer):
    class meta:
        model = CartItem
        field = "__all__"       