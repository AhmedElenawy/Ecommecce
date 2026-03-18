from django.shortcuts import render
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST



# Create your views here.
from store.models import Product
from .forms import add_or_replace_quantity
from .cart import Cart
from coupon.forms import CouponForm
from store.recommendation import recommendation
from django.conf import settings


def cart_detail(request):
    cart = Cart(request)
    form = CouponForm()
    
    # add form to each item
    products =[]
    for item in cart:
        item["add_or_update_form"] = add_or_replace_quantity(initial={
            "quantity": item["quantity"],
            "replace": True
        })
        products.append(item["item"])

    r = recommendation()
    similarproducts = r.recommendations_for(products, 4)
        
    return render(request, "cart/detail.html", {"cart": cart, "form": form, "similarproducts": similarproducts})

@require_POST
def add_or_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = add_or_replace_quantity(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        cart.add_or_update(product, quantity=data['quantity'], replace=data['replace'])

    return redirect("cart:cart_detail")

@require_POST
def remove_item(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove_item(product)
    return redirect("cart:cart_detail")


def cart_dropdown_partial(request):
    cart = Cart(request)
    return render(request, "cart/partials/cart_dropdown.html", {"cart": cart})

