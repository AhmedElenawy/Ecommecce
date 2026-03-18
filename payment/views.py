from decimal import Decimal

import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from order.models import Order
from store.models import Product
from django.db.models import OuterRef, Subquery, Prefetch
from django.contrib import messages

from .payment import stripe_payment, paymob_payment
# create the Stripe instance
def payment_proccess(request):
    # retreive order id
    order_id = request.session["order_id"]
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        order = get_object_or_404(Order.objects.prefetch_related('order_items', 'order_items__item').select_related('coupon', 'shipping_address'), id=order_id)
        if order.session_id and order.payment_method == 'paymob':
            return redirect(f"https://accept.paymob.com/unifiedcheckout/?publicKey={settings.PAYMOB_PUBLIC_KEY}&clientSecret={order.session_id}", code=303)

        success_url = request.build_absolute_uri (reverse('payment:completed'))
        cancel_url = request.build_absolute_uri (reverse('payment:canceled'))
        webhook_url = request.build_absolute_uri (reverse('paymob-webhook'))
        if order.status != Order.Status.PENDING:
            return redirect('order:order_detail', order.id)
        # data of strip session
        if payment_method == 'stripe':
            order.payment_method = 'stripe'
            order.save()
            session_url = stripe_payment(order, success_url, cancel_url)
        elif payment_method == 'paymob':
            try:
                order.payment_method = 'paymob'
                order.save()
                session_url = paymob_payment(order, success_url, cancel_url, webhook_url)
            except Exception as e:
                # Handle Paymob payment errors
                messages.error(request, f"Payment processing failed: {str(e)}") 
                return render(request, 'payment/canceled.html', {'error': str(e)})
        else:
            messages.error(request, "Invalid payment method.")
            return render(request, 'payment/canceled.html', {'error': "Invalid payment method."})
        return redirect(session_url, code=303)
    else:
        #  local her contains all decleared var in dict form.
        #  it contains order and order id'order_items__item', 'order_items__item__category'
        order = get_object_or_404(Order.objects.select_related('coupon', 'shipping_address').prefetch_related('order_items', 
                                                                 Prefetch('order_items__item', queryset=Product.active.all().select_related('category'))),
                                                                 id=order_id)

        return render(request, 'payment/process.html', {'order': order})

def payment_completed(request):
    return render(request, 'payment/completed.html')

def payment_canceled(request):
    return render(request, 'payment/canceled.html')