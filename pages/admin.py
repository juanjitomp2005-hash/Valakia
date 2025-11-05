import io
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from .models import Product


class ProductAdmin(admin.ModelAdmin):
	list_display = ("name", "price", "stock", "cantidad_vendidos", "es_producto_dia")
	search_fields = ("name", "descripcion")
	list_filter = ("cantidad_vendidos", "es_producto_dia")
	fields = ("name", "price", "stock", "image", "descripcion", "cantidad_vendidos", "es_producto_dia")
	change_list_template = "admin/pages/product/change_list.html"

	def get_urls(self):
		urls = super().get_urls()
		custom_urls = [
			path(
				"export-inventory/",
				self.admin_site.admin_view(self.export_inventory_pdf),
				name="pages_product_export_inventory",
			),
		]
		return custom_urls + urls

	def export_inventory_pdf(self, request):
		buffer = io.BytesIO()
		pdf = canvas.Canvas(buffer, pagesize=letter)
		width, height = letter

		pdf.setFont("Helvetica-Bold", 16)
		pdf.drawString(72, height - 72, str(_("Inventory report")))
		pdf.setFont("Helvetica", 10)
		generated_at = timezone.localtime().strftime("%Y-%m-%d %H:%M")
		pdf.drawString(72, height - 90, f"{str(_('Generated on'))}: {generated_at}")

		pdf.setFont("Helvetica-Bold", 12)
		pdf.drawString(72, height - 120, str(_("Product")))
		pdf.drawString(320, height - 120, str(_("Stock")))

		y_position = height - 140
		pdf.setFont("Helvetica", 11)

		products = Product.objects.order_by("name")

		if not products:
			pdf.drawString(72, y_position, str(_("No products available.")))
		else:
			for product in products:
				pdf.drawString(72, y_position, product.name)
				pdf.drawRightString(400, y_position, str(product.stock))
				y_position -= 18
				if y_position < 72:
					pdf.showPage()
					pdf.setFont("Helvetica-Bold", 12)
					pdf.drawString(72, height - 72, str(_("Product")))
					pdf.drawString(320, height - 72, str(_("Stock")))
					pdf.setFont("Helvetica", 11)
					y_position = height - 90

		pdf.save()

		buffer.seek(0)
		response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
		response["Content-Disposition"] = "attachment; filename=inventory.pdf"
		return response

admin.site.register(Product, ProductAdmin)
