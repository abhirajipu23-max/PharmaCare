from django.db import models
from django.contrib.auth.models import User

class Productlist(models.Model):
    productId = models.AutoField(primary_key=True)
    productName = models.CharField()
    price = models.PositiveIntegerField()
    image = models.ImageField()
    description = models.TextField(max_length=50)

class OrderDetail(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)