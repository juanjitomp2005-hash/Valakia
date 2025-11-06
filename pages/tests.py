from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Cart, CartItem, Order, OrderItem, Product


class ProductModelTests(TestCase):
	def test_string_representation_returns_name(self):
		product = Product.objects.create(name="Laptop", price=Decimal("999.99"))

		self.assertEqual(str(product), "Laptop")

	def test_default_stock_is_zero(self):
		product = Product.objects.create(name="Mouse", price=Decimal("49.99"))

		self.assertEqual(product.stock, 0)


class HomeViewTests(TestCase):
	def test_home_page_renders_successfully(self):
		response = self.client.get(reverse("home"))

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, "pages/home.html")


class ProductInventoryAPITests(TestCase):
	def test_inventory_api_returns_only_products_with_stock(self):
		Product.objects.create(name="Laptop", price=Decimal("1200.00"), stock=5)
		Product.objects.create(name="Mouse", price=Decimal("40.00"), stock=0)

		response = self.client.get(reverse("product_inventory_api"))

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertIn("products", payload)
		self.assertEqual(len(payload["products"]), 1)
		self.assertEqual(payload["products"][0]["name"], "Laptop")
		self.assertEqual(payload["products"][0]["stock"], 5)


class MercadoPagoCheckoutTests(TestCase):
	def setUp(self):
		self.user_model = get_user_model()
		self.user = self.user_model.objects.create_user(
			username="tester",
			email="tester@example.com",
			password="secret123",
		)
		self.product = Product.objects.create(name="Keyboard", price=Decimal("150000.00"), stock=10)
		self.client.login(username="tester", password="secret123")

	def _prepare_cart(self):
		cart, _ = Cart.objects.get_or_create(user=self.user)
		CartItem.objects.create(cart=cart, product=self.product, quantity=1)
		return cart

	def test_checkout_requires_configured_token(self):
		self._prepare_cart()
		with override_settings(MERCADOPAGO_ACCESS_TOKEN=""):
			response = self.client.post(reverse("checkout"))
		self.assertRedirects(response, reverse("cart"))
		self.assertEqual(Order.objects.count(), 0)

	@override_settings(MERCADOPAGO_ACCESS_TOKEN="TEST-TOKEN")
	@patch("pages.views._get_mercadopago_client")
	def test_checkout_redirects_to_init_point(self, mock_client_factory):
		self._prepare_cart()
		mock_client = Mock()
		mock_preference = Mock()
		mock_preference.create.return_value = {
			"response": {"id": "PREF-1", "init_point": "https://pay.mercadopago.com/PREF-1"}
		}
		mock_client.preference.return_value = mock_preference
		mock_client_factory.return_value = mock_client

		response = self.client.post(reverse("checkout"))

		self.assertRedirects(response, "https://pay.mercadopago.com/PREF-1", fetch_redirect_response=False)
		self.assertEqual(Order.objects.count(), 1)
		order = Order.objects.first()
		self.assertEqual(order.preference_id, "PREF-1")
		self.assertEqual(order.total, Decimal("150000.00"))
		self.assertEqual(order.items.count(), 1)

	@override_settings(MERCADOPAGO_ACCESS_TOKEN="TEST-TOKEN")
	@patch("pages.views._get_mercadopago_client")
	def test_payment_success_updates_order(self, mock_client_factory):
		cart = self._prepare_cart()
		CartItem.objects.filter(cart=cart).update(quantity=2)
		order = Order.objects.create(user=self.user, preference_id="PREF-2", total=Decimal("300000.00"))
		OrderItem.objects.create(
			order=order,
			product=self.product,
			product_name=self.product.name,
			quantity=2,
			unit_price=self.product.price,
		)

		mock_payment_client = Mock()
		mock_payment_client.get.return_value = {
			"response": {"status": "approved", "id": "PAY-1", "status_detail": "approved"}
		}
		mock_client = Mock()
		mock_client.payment.return_value = mock_payment_client
		mock_client_factory.return_value = mock_client

		response = self.client.get(
			reverse("payment_success"),
			{"preference_id": "PREF-2", "payment_id": "PAY-1"},
		)

		self.assertEqual(response.status_code, 200)
		order.refresh_from_db()
		self.assertEqual(order.status, Order.Status.APPROVED)
		self.assertEqual(order.payment_id, "PAY-1")
		self.assertEqual(CartItem.objects.filter(cart=cart).count(), 0)
