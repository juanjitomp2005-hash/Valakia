from django.urls import path, include
from .views import HomePageView, AboutPageView, ProductIndexView, ProductShowView, ProductCreateView, register
from django.contrib.auth import views as auth_views 
from django.contrib import admin

urlpatterns = [
 path('', HomePageView.as_view(), name='home'),
 path('about/', AboutPageView.as_view(), name='about'),
 path('products/', ProductIndexView.as_view(), name='products'),
 path('products/<str:id>', ProductShowView.as_view(), name='show'),
 path('products/create', ProductCreateView.as_view(), name='form'),
 path('login/', auth_views.LoginView.as_view(template_name='pages/login.html'), name='login'),
 path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
 path("register/", register, name="register"),

]
