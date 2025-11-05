from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    descripcion = models.TextField(blank=True, verbose_name=_("Description"))
    cantidad_vendidos = models.PositiveIntegerField(default=0, verbose_name=_("Quantity sold"))
    es_producto_dia = models.BooleanField(default=False, verbose_name=_("Is product of the day?"))

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Cart of {self.user.username}"

    def get_total(self):
        return sum(item.get_total() for item in self.cartitem_set.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"

    def get_total(self):
        return self.product.price * self.quantity
