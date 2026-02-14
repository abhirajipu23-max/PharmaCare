from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "chatbot"

urlpatterns = [
    path("", views.home, name="home"),
    path("products/", views.product_list, name="product_list"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("api/chat/", views.chat_api, name="chat_api"),
]
