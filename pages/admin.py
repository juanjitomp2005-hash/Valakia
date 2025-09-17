from django.contrib import admin
from .models import Product


class ProductAdmin(admin.ModelAdmin):
	list_display = ("name", "price", "cantidad_vendidos", "es_producto_dia")
	search_fields = ("name", "descripcion")
	list_filter = ("cantidad_vendidos", "es_producto_dia")
	fields = ("name", "price", "image", "descripcion", "cantidad_vendidos", "es_producto_dia")

admin.site.register(Product, ProductAdmin)
