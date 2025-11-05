from django.http import HttpResponse # new
from django.views.generic import TemplateView
from django.views import View
from django import forms
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Product, CartItem, Cart
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse

@login_required(login_url='/login/')
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.cartitem_set.all()
    total = sum(item.get_total() for item in items)
    return render(request, 'pages/cart.html', {
        'cart_items': items,
        'total': total
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
