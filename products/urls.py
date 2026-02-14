from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import ProductsApi

app_name = "products"

router = DefaultRouter()
router.register(r"products", ProductsApi, basename="products")

urlpatterns = [
    path("", views.home, name="home"),
    path("products/", views.product_list, name="product_list"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("upload-rx/", views.upload_rx, name="upload_rx"),
    path("api/", include(router.urls)),
]
