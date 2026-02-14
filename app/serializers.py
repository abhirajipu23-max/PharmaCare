from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from django.contrib.auth.models import User
from . models import Productlist

class ProductlistSerializer(serializers.ModelSerializer):
    class meta:
        model = Productlist
        field = "__all__"