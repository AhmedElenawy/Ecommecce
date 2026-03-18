from celery import shared_task
from django.core.mail import EmailMessage, EmailMultiAlternatives
from smtplib import SMTPException

from django.core.files.base import ContentFile
from order.models import Order
from store.models import Product
from store.recommendation import recommendation

import weasyprint
from django.contrib.staticfiles import finders

from django.template.loader import render_to_string

from django.shortcuts import get_object_or_404

@shared_task(bind=True,
    autoretry_for=(SMTPException, ConnectionError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True)
def send_invoice(self, order_id ):
    order = get_object_or_404(Order.objects.select_related('user', 'shipping_address'), id=order_id)
    html = render_to_string("order/invoice.html", {'order': order})
    pdf =  weasyprint.HTML(string=html).write_pdf()

    try:
        email = EmailMultiAlternatives(
            subject = f"Invoice #{order.id}",
            body = "This is your invoice",
            from_email = None,
            to = [order.user.email],
        )
        email.attach(f"invoice_{order.id}.pdf", pdf, "application/pdf")
        email.send()
    except Exception as e:
        raise


@shared_task
def after_payment(client_reference_id, payment_intent):
    order = get_object_or_404(Order, id=client_reference_id)
    order.paid = True
    order.status = Order.Status.PAID
    # stripe id
    order.payment_id = payment_intent
    order.save()

    # products = order.order_items.values_list('item', flat=True)
    # base_products = [product.variant_group.get_all_variant_products() if product.variant_group else product for product in Product.active.filter(id__in=products)]
    products = Product.active.filter(
        id__in=order.order_items.values_list('item_id', flat=True) 
    )
    
    r = recommendation()
    r.bought_together(products)

    send_invoice.delay(order.id)