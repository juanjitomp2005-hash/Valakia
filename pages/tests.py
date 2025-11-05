from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Product


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
