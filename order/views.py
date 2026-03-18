from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import gettext as _
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET
from django.contrib import messages
from django.template.loader import render_to_string
from django.db import transaction
from django.contrib.staticfiles import finders

from cart.cart import Cart
from .forms import CheckoutForm
from .models import Order, OrderItems
from .tasks import release_stock
from .shipping import Shipping, ShipmentError
from coupon.models import CouponUsage
from store.models import Product

import weasyprint

@login_required
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('cart:cart_detail')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Check Stock Availability First
                    for item in cart:
                        product = Product.objects.select_for_update().get(id=item['item'].id)
                        if item['quantity'] > product.stock:
                            messages.error(request, _('Out of stock: %(product)s') % {'product': product.name})
                            # If stock fails, we redirect and the transaction rolls back automatically
                            return redirect('cart:cart_detail')

                    # 2. Create Order Instance
                    order = Order(user=request.user)
                    
                    # 3. Handle Coupon
                    coupon = cart.coupon_object
                    if coupon:
                        try:  
                            if coupon.is_valid(request):
                                order.coupon = coupon
                                order.discount_amount = cart.discount()
                                CouponUsage.objects.create(user=request.user, coupon=coupon)
                        except Exception as e:
                            # Log error but maybe don't fail the whole order? 
                            # For now, following original logic: fail if coupon errors.
                            request.session['coupon_id'] = None
                            raise Exception(_('Error applying coupon: %(error)s') % {'error': str(e)})

                    # 4. Calculate Shipping Price securely
                    # We use the city name from the validated form data to get the rate
                    city_name = form.cleaned_data.get('city')
                    try:
                        shipping_service = Shipping()
                        # Get rate from API (returns float or dict, handled by get_shipping_rate wrapper below)
                        # We use the helper method defined in views usually, but here we call the class directly.
                        # The class method returns a dict usually, let's extract the price.
                        shipping_resp = shipping_service.get_shipping_rate(dropoff_city=city_name)
                        
                        # Handle response format from shipping.py
                        if isinstance(shipping_resp, dict):
                            shipping_price = shipping_resp.get('data', {}).get('priceAfterVat', 
                                             shipping_resp.get('data', {}).get('rate', 5))
                        else:
                            shipping_price = float(shipping_resp)
                            
                    except Exception:
                        # Fallback if API fails
                        shipping_price = 5.0
                    
                    order.shipping_price = shipping_price
                    order.save()
                    
                    # 5. Save Shipping Address
                    shipping_address = form.save(commit=False)
                    shipping_address.order = order
                    shipping_address.save()
                    
                    # 6. Create Order Items and Update Stock
                    for item in cart:
                        product = item['item']
                        # Re-fetch to be safe within transaction or use the locked instance if we kept it
                        # Simple approach: update the object we have since we are in atomic block
                        product.stock -= item['quantity']
                        product.sales += item['quantity']
                        product.save()

                        OrderItems.objects.create(
                            order=order,
                            item=product,
                            quantity=item['quantity'],
                            price=item['price']
                        )
                    
                    # 7. Finalize
                    cart.clear()
                    request.session['order_id'] = order.id
                    # remove coupon from session
                    request.session['coupon_id'] = None
                    release_stock.apply_async(args=[order.id], countdown=900)
                    
                    return redirect('payment:proccess')

            except Exception as e:
                messages.error(request, str(e))
                return redirect('cart:cart_detail')
        else:
            # Form is invalid
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CheckoutForm()

    return render(request, 'order/checkout.html', {'cart': cart, 'form': form})

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('order_items').select_related('shipping_address')
    return render(request, 'order/order_list.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related('coupon', 'shipping_address')
        .prefetch_related(
            'order_items', 
            Prefetch('order_items__item', queryset=Product.active.all().select_related('category'))
        ),
        id=order_id, 
        user=request.user
    )
    return render(request, 'order/order_detail.html', {'order': order})

@staff_member_required
def generate_invoice(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related('coupon', 'user', 'shipping_address')
        .prefetch_related(
            'order_items', 
            Prefetch('order_items__item', queryset=Product.active.all().select_related('category'))
        ),
        id=order_id
    )

    html = render_to_string('order/invoice.html', {'order': order})
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice_%(order_id)s.pdf"' % {'order_id': order.id}
    weasyprint.HTML(string=html).write_pdf(response)
    return response

# --- API VIEWS ---

@require_GET
def get_shipping_zones(request):
    """Return zones for a selected city as JSON"""
    city_id = request.GET.get('city_id')
    if not city_id:
        return JsonResponse({'error': 'City ID required'}, status=400)
    
    try:
        shipping = Shipping()
        zones = shipping.get_shipping_zones(city_id)
        return JsonResponse({'zones': zones})
    except ShipmentError as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_GET
def get_shipping_cities(request):
    """Return all cities as JSON"""
    try:
        shipping = Shipping()
        cities = shipping.get_shipping_cities()
        return JsonResponse({'cities': cities})
    except ShipmentError as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_GET
def get_shipping_districts(request):
    """Return districts for a selected zone as JSON"""
    city_id = request.GET.get('city_id')
    zone_id = request.GET.get('zone_id')
    
    if not city_id or not zone_id:
        return JsonResponse({'error': 'City ID and Zone ID required'}, status=400)
    
    try:
        shipping = Shipping()
        districts = shipping.get_shipping_districts(city_id, zone_id)
        return JsonResponse({'districts': districts})
    except ShipmentError as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_GET
def get_shipping_rate(request):
    """Calculate shipping rate for a selected city"""
    city_name = request.GET.get('city_name')
    
    if not city_name:
        print("City name is required for shipping rate calculation")
        return JsonResponse({'error': 'City name required'}, status=400)
    
    try:
        shipping = Shipping()
        # Call the Shipping method
        result = shipping.get_shipping_rate(dropoff_city=city_name)
        
        # Parse the result based on structure in shipping.py
        # It returns either a dict (API response) or raises Error
        price = 0
        if isinstance(result, dict):
            data = result.get('data', {})
            # Try to find price in common locations
            price = data.get('priceAfterVat', data.get('rate', 0))
        
        return JsonResponse({
            'success': True,
            'shipping_rate': float(price),
            'currency': 'EGP'
        })
    except ShipmentError as e:
        print(f"ShipmentError: {str(e)}")
        return JsonResponse({'error': str(e), 'success': False}, status=400)
    except Exception as e:
        print(f"Exception: {str(e)}")
        return JsonResponse({'error': f'Failed: {str(e)}', 'success': False}, status=400)