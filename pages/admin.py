import io
from django.contrib import admin
import json
import urllib.error
import urllib.request
from django.http import HttpResponse
from django.urls import path
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.template.response import TemplateResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from .models import Order, OrderItem, Product


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
			path(
				"consume-api/",
				self.admin_site.admin_view(self.consume_api_view),
				name="pages_product_consume_api",
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

	def consume_api_view(self, request):
		default_endpoint = request.build_absolute_uri("/api/products/")
		endpoint = request.POST.get("endpoint", "").strip() if request.method == "POST" else default_endpoint
		error = None
		response_text = ""

		if request.method == "POST":
			if not endpoint:
				error = _("You must provide an endpoint URL.")
			else:
				try:
					with urllib.request.urlopen(endpoint) as response:
						charset = response.headers.get_content_charset() or "utf-8"
						payload = response.read().decode(charset)
					try:
						parsed = json.loads(payload)
						response_text = json.dumps(parsed, indent=2, ensure_ascii=False)
					except json.JSONDecodeError:
						response_text = payload
				except urllib.error.URLError as exc:
					error = str(exc.reason)
				except Exception as exc:  # pragma: no cover - defensive
					error = str(exc)

		context = dict(
			self.admin_site.each_context(request),
			title=_("Consume API"),
			opts=self.model._meta,
			endpoint=endpoint or default_endpoint,
			response_text=response_text,
			error=error,
		)
		return TemplateResponse(request, "admin/pages/product/consume_api.html", context)

admin.site.register(Product, ProductAdmin)


class OrderItemInline(admin.TabularInline):
	model = OrderItem
	extra = 0
	readonly_fields = ("product_name", "quantity", "unit_price", "get_total")

	def get_total(self, obj):
		return obj.get_total()

	get_total.short_description = "Total"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ("preference_id", "user", "status", "total", "created_at")
	list_filter = ("status", "created_at")
	search_fields = ("preference_id", "payment_id", "user__username")
	inlines = [OrderItemInline]
	readonly_fields = (
		"preference_id",
		"payment_id",
		"status",
		"status_detail",
		"total",
		"created_at",
		"updated_at",
	)
