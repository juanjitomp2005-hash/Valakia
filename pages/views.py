from django.http import HttpResponse # new
from django.views.generic import TemplateView
from django.views import View
from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Product, CartItem, Cart
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db.models import Q


def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.cartitem_set.all()
    total = sum(item.get_total() for item in items)  # 👈 calcular total
    return render(request, 'pages/cart.html', {
        'cart': cart,
        'cart_items': items,  # 👈 ahora el template recibe cart_items
        'total': total,       # 👈 y también total
    })

@login_required(login_url='/login/')
def add_to_cart(request, product_id):
    if request.method != "POST":
        return redirect('products')

    print("Entrando a add_to_cart con product_id:", product_id)  # 👈 debug

    product = get_object_or_404(Product, pk=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('cart')

@login_required
def remove_from_cart(request, product_id):
    cart = get_object_or_404(Cart, user=request.user)
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.filter(cart=cart, product=product).first()
    if cart_item:
        cart_item.delete()
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
 
class AboutPageView(TemplateView):
    template_name = 'pages/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "About us - Online Store",
            "subtitle": "About us",
            "description": "This is an about page ...",
            "author": "Developed by: Juan Jose Montoya",
        })
        return context


from django.db.models import Q  # 👈 para búsquedas con OR

class ProductIndexView(View):
    template_name = 'pages/products/index.html'
 
    def get(self, request):
        query = request.GET.get("q")  # obtiene lo que se busca
        if query:
            products = Product.objects.filter(
                Q(name__icontains=query)
            )
        else:
            products = Product.objects.all()

        viewData = {
            "title": "Products - Online Store",
            "subtitle": "List of products",
            "products": products,
            "query": query,  # para que el input no pierda el texto buscado
        }
        return render(request, self.template_name, viewData)



class ProductShowView(View):
    template_name = 'pages/products/show.html'
 
    def get(self, request, id):
        viewData = {}
        product = Product.objects.get(pk=id)  # ✅ busca en la BD
        viewData["title"] = product.name + " - Online Store"
        viewData["subtitle"] = product.name + " - Product information"
        viewData["product"] = product
        return render(request, self.template_name, viewData)

class ProductForm(forms.Form):
    name = forms.CharField(required=True)
    price = forms.FloatField(required=True)


class ProductCreateView(View):
    template_name = 'pages/products/create.html'

    def get(self, request):
        form = ProductForm()
        viewData = {}
        viewData["title"] = "Create product"
        viewData["form"] = form
        return render(request, self.template_name, viewData)

    def post(self, request):
        form = ProductForm(request.POST)
        if form.is_valid():
           return redirect("products") 
        else:
            viewData = {}
            viewData["title"] = "Create product"
            viewData["form"] = form
            return render(request, self.template_name, viewData)
