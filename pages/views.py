from decimal import Decimal
import logging

import mercadopago

from django.http import HttpResponse # new
from django.views.generic import TemplateView
from django.views import View
from django import forms
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from .models import Cart, CartItem, Order, OrderItem, Product
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse

logger = logging.getLogger(__name__)

@login_required(login_url='/login/')
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.cartitem_set.all()
    total = sum(item.get_total() for item in items)
    return render(request, 'pages/cart.html', {
        'cart_items': items,
        'total': total,
        'mercadopago_ready': bool(settings.MERCADOPAGO_ACCESS_TOKEN),
    })

@login_required(login_url='/login/')
def add_to_cart(request, product_id):
    if request.method == "POST":
        product = get_object_or_404(Product, id=product_id)
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            total_items = sum(item.quantity for item in cart.cartitem_set.all())
            return JsonResponse({
                "success": True,
                "cart_count": total_items,
                "message": _("Product added to cart."),
            })

        messages.success(request, _("Product added to cart."))
        return redirect("cart")

@login_required
def remove_from_cart(request, product_id):
    cart = get_object_or_404(Cart, user=request.user)
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.filter(cart=cart, product=product).first()
    if cart_item:
        cart_item.delete()
        messages.info(request, _("Product removed from cart."))
    return redirect("cart")

def profile(request):
    return render(request, "pages/profile.html", {"user": request.user})

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "pages/register.html", {"form": form})

class HomePageView(TemplateView):
    template_name = 'pages/home.html'

    def get_context_data(self, **kwargs):
        import random
        context = super().get_context_data(**kwargs)
        productos_mas_vendidos = Product.objects.order_by('-cantidad_vendidos')[:4]
        context['productos_mas_vendidos'] = productos_mas_vendidos
        producto_dia = Product.objects.filter(es_producto_dia=True).first()
        if producto_dia:
            context['producto_aleatorio'] = producto_dia
        else:
            productos = list(Product.objects.all())
            context['producto_aleatorio'] = random.choice(productos) if productos else None
        # Contar productos en carrito si autenticado
        if self.request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=self.request.user)
            context['cart_count'] = sum(item.quantity for item in cart.cartitem_set.all())
        else:
            context['cart_count'] = 0
        return context
 
class AboutPageView(TemplateView):
    template_name = 'pages/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "title": _("About us - Online Store"),
            "subtitle": _("About us"),
            "description": _("This is an about page ..."),
            "author": _("Developed by: Juan Jose Montoya"),
        })
        return context


from django.db.models import Q  # 👈 para búsquedas con OR

class ProductIndexView(View):
    template_name = 'pages/products/index.html'
 
    def get(self, request):
        query = request.GET.get("q")
        order = request.GET.get("order")
        products = Product.objects.all()
        if query:
            products = products.filter(
                Q(name__icontains=query)
            )
        if order == "price_asc":
            products = products.order_by("price")
        elif order == "price_desc":
            products = products.order_by("-price")

        # Contar productos en carrito si autenticado
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
            cart_count = sum(item.quantity for item in cart.cartitem_set.all())
        else:
            cart_count = 0

        viewData = {
            "title": _("Products - Online Store"),
            "subtitle": _("List of products"),
            "products": products,
            "query": query,
            "cart_count": cart_count,
        }
        return render(request, self.template_name, viewData)



class ProductShowView(View):
    template_name = 'pages/products/show.html'
 
    def get(self, request, id):
        viewData = {}
        product = Product.objects.get(pk=id)  # ✅ busca en la BD
        viewData["title"] = _("%(product)s - Online Store") % {"product": product.name}
        viewData["subtitle"] = _("%(product)s - Product information") % {"product": product.name}
        viewData["product"] = product
        # Contar productos en carrito si autenticado
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
            cart_count = sum(item.quantity for item in cart.cartitem_set.all())
        else:
            cart_count = 0
        viewData["cart_count"] = cart_count
        return render(request, self.template_name, viewData)

class ProductForm(forms.Form):
    name = forms.CharField(required=True, label=_("Name"))
    price = forms.FloatField(required=True, label=_("Price"))


class ProductCreateView(View):
    template_name = 'pages/products/create.html'

    def get(self, request):
        form = ProductForm()
        viewData = {}
        viewData["title"] = _("Create product")
        viewData["form"] = form
        return render(request, self.template_name, viewData)

    def post(self, request):
        form = ProductForm(request.POST)
        if form.is_valid():
           return redirect("products") 
        else:
            viewData = {}
            viewData["title"] = _("Create product")
            viewData["form"] = form
            return render(request, self.template_name, viewData)


@require_GET
def product_inventory_api(request):
    products = Product.objects.filter(stock__gt=0).order_by("name")
    data = {
        "products": [
            {
                "id": product.id,
                "name": product.name,
                "price": str(product.price),
                "stock": product.stock,
            }
            for product in products
        ]
    }
    return JsonResponse(data)


def _get_mercadopago_client():
    access_token = settings.MERCADOPAGO_ACCESS_TOKEN
    if not access_token:
        raise ValueError("Mercado Pago access token is not configured.")
    return mercadopago.SDK(access_token)


def _cart_items_with_totals(cart):
    items = cart.cartitem_set.select_related("product")
    total = sum((item.get_total() for item in items), Decimal("0"))
    return items, total


@login_required(login_url='/login/')
def mercado_pago_checkout(request):
    if request.method != "POST":
        return redirect("cart")

    try:
        sdk = _get_mercadopago_client()
    except ValueError:
        messages.error(request, _("Payment processor is not configured."))
        return redirect("cart")

    cart = get_object_or_404(Cart, user=request.user)
    items_qs, total = _cart_items_with_totals(cart)

    if not items_qs:
        messages.error(request, _("You have no products in the cart."))
        return redirect("cart")

    success_url = request.build_absolute_uri(reverse("payment_success"))
    failure_url = request.build_absolute_uri(reverse("payment_failure"))
    pending_url = request.build_absolute_uri(reverse("payment_pending"))

    preference_data = {
        "items": [
            {
                "id": str(item.product.id),
                "title": item.product.name,
                "quantity": int(item.quantity),
                "currency_id": "COP",
                "unit_price": float(item.product.price),
            }
            for item in items_qs
        ],
        "payer": {
            "name": request.user.first_name,
            "surname": request.user.last_name,
            "email": request.user.email,
        },
        "back_urls": {
            "success": success_url,
            "failure": failure_url,
            "pending": pending_url,
        },
    }

    if success_url.startswith("https://"):
        preference_data["auto_return"] = "approved"

    print("Mercado Pago preference payload:", preference_data)

    try:
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response.get("response", {})
        print("Mercado Pago preference response:", preference_response)
    except mercadopago.exceptions.MPApiException as exc:
        error_response = getattr(exc, "response", {}) or {}
        error_msg = error_response.get("message") or error_response.get("error") or str(exc)
        logger.warning("Mercado Pago API error while creating preference: %s", error_response)
        print("Mercado Pago API error while creating preference:", error_response)
        messages.error(request, _("Mercado Pago error: %(msg)s") % {"msg": error_msg})
        return redirect("cart")
    except Exception as exc:  # pragma: no cover - network failure safeguard
        logger.exception("Unexpected error while creating Mercado Pago preference")
        messages.error(request, str(exc))
        return redirect("cart")

    preference_id = preference.get("id")
    init_point = preference.get("init_point") or preference.get("sandbox_init_point")

    if not preference_id or not init_point:
        messages.error(request, _("There was an error creating the payment preference."))
        return redirect("cart")

    order = Order.objects.create(
        user=request.user,
        preference_id=preference_id,
        total=total,
    )

    order_items = [
        OrderItem(
            order=order,
            product=item.product,
            product_name=item.product.name,
            quantity=item.quantity,
            unit_price=item.product.price,
        )
        for item in items_qs
    ]
    OrderItem.objects.bulk_create(order_items)

    return redirect(init_point)


def _update_order_status(order, payment_response):
    response = payment_response.get("response", {})
    status = response.get("status")
    detail = response.get("status_detail", "")
    payment_id = response.get("id") or response.get("payment", {}).get("id")

    if payment_id:
        order.payment_id = str(payment_id)

    order.status_detail = detail

    if status == "approved":
        order.status = Order.Status.APPROVED
        CartItem.objects.filter(cart__user=order.user).delete()
    elif status in {"pending", "in_process"}:
        order.status = Order.Status.PENDING
    elif status == "cancelled":
        order.status = Order.Status.CANCELLED
    else:
        order.status = Order.Status.REJECTED

    order.save(update_fields=["payment_id", "status", "status_detail", "updated_at"])


def _handle_payment_feedback(request):
    preference_id = request.GET.get("preference_id")
    payment_id = request.GET.get("payment_id")

    if not preference_id:
        messages.error(request, _("Payment information is missing."))
        return None

    order = Order.objects.filter(preference_id=preference_id, user=request.user).first()
    if not order:
        messages.error(request, _("Order not found."))
        return None

    if payment_id:
        try:
            sdk = _get_mercadopago_client()
            payment_response = sdk.payment().get(payment_id)
            _update_order_status(order, payment_response)
        except Exception as exc:  # pragma: no cover - network failure safeguard
            messages.error(request, str(exc))
    else:
        # fallback to status provided in the query params
        status = request.GET.get("status")
        if status:
            mapped = {
                "approved": Order.Status.APPROVED,
                "pending": Order.Status.PENDING,
                "in_process": Order.Status.PENDING,
                "cancelled": Order.Status.CANCELLED,
                "rejected": Order.Status.REJECTED,
            }.get(status)
            if mapped:
                order.status = mapped
                order.save(update_fields=["status", "updated_at"])

    return order


@login_required(login_url='/login/')
def payment_success(request):
    order = _handle_payment_feedback(request)
    if not order:
        return redirect("cart")

    context = {
        "order": order,
    }
    return render(request, "pages/succes.html", context)


@login_required(login_url='/login/')
def payment_failure(request):
    order = _handle_payment_feedback(request)
    if order and order.status != Order.Status.APPROVED:
        order.status = Order.Status.REJECTED
        order.save(update_fields=["status", "updated_at"])
    return render(request, "pages/cancel.html", {"order": order})


@login_required(login_url='/login/')
def payment_pending(request):
    order = _handle_payment_feedback(request)
    if order and order.status == Order.Status.PENDING:
        messages.info(request, _("Your payment is pending confirmation."))
    return render(request, "pages/cancel.html", {"order": order})


@login_required(login_url='/login/')
def orders_list(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "pages/orders/list.html", {"orders": orders})


@login_required(login_url='/login/')
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, "pages/orders/detail.html", {"order": order})
