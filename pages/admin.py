from django.contrib import admin
from .models import Product

class ProductAdmin(admin.ModelAdmin):
	list_display = ("name", "price", "cantidad_vendidos")
	search_fields = ("name", "descripcion")
	list_filter = ("cantidad_vendidos",)
	fields = ("name", "price", "image", "descripcion", "cantidad_vendidos")

admin.site.register(Product, ProductAdmin)
