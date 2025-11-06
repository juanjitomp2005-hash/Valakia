from django.urls import path
from django.contrib.auth import views as auth_views

from .views import (
	AboutPageView,
	HomePageView,
	ProductCreateView,
	ProductIndexView,
	ProductShowView,
	add_to_cart,
	cart_view,
	mercado_pago_checkout,
	product_inventory_api,
	register,
	remove_from_cart,
	payment_success,
	payment_failure,
	payment_pending,
	orders_list,
	order_detail,
)

urlpatterns = [
	path('', HomePageView.as_view(), name='home'),
	path('about/', AboutPageView.as_view(), name='about'),
	path('products/', ProductIndexView.as_view(), name='products'),
	path('products/<str:id>', ProductShowView.as_view(), name='show'),
	path('products/create', ProductCreateView.as_view(), name='form'),
	path('login/', auth_views.LoginView.as_view(template_name='pages/login.html'), name='login'),
	path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
	path("register/", register, name="register"),
	path("cart/", cart_view, name="cart"),
	path("cart/add/<int:product_id>/", add_to_cart, name="add_to_cart"),
	path("cart/remove/<int:product_id>/", remove_from_cart, name="remove_from_cart"),
	path("checkout/", mercado_pago_checkout, name="checkout"),
	path("payments/success/", payment_success, name="payment_success"),
	path("payments/failure/", payment_failure, name="payment_failure"),
	path("payments/pending/", payment_pending, name="payment_pending"),
	path("api/products/", product_inventory_api, name="product_inventory_api"),
	path("orders/", orders_list, name="orders_list"),
	path("orders/<int:pk>/", order_detail, name="order_detail"),
]
