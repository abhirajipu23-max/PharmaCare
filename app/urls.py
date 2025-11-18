from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('register/', views.user_register, name="register"),
    path('login/', views.user_login, name="login"),
    path('profile/', views.user_profile, name="profile"),
    path('search_results/', views.search_results, name="search_results"),
    path('cart/', views.cart, name="cart"),
    
]
