from django.shortcuts import render
from django.http import HttpResponse # new
from django.views.generic import TemplateView
from django.views import View
from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Product

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


class ProductIndexView(View):
    template_name = 'pages/products/index.html'
 
    def get(self, request):
        viewData = {}
        viewData["title"] = "Products - Online Store"
        viewData["subtitle"] = "List of products"
        viewData["products"] = Product.objects.all()  # ✅ ahora viene de la BD
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
