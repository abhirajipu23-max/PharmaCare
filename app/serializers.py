from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from django.contrib.auth.models import User
from . models import Productlist

class ChecklistSerializer(serializers.Serializer):
    title = serializers.CharField()
    is_deleted = serializers.BooleanField()
    created_on = serializers.DateTimeField()
    is_archived = serializers.BooleanField()
    updated_on = serializers.DateTimeField()