from celery import shared_task
from django.core.files.base import ContentFile
from .models import Order, PdfFile
import stripe

from django.db.models import OuterRef, Subquery, Prefetch
from store.models import Product
import weasyprint
from django.contrib.staticfiles import finders

from django.template.loader import render_to_string

@shared_task
def orders_invoices(id_list, pdf_id):
    orders = Order.objects.filter(id__in=id_list).select_related('coupon', 'user', 'shipping_address').prefetch_related('order_items', 
                                                                 Prefetch('order_items__item', queryset=Product.active.all().select_related('category')))
    
    html = render_to_string('order/invoices.html', {'orders': orders})
    pdf = weasyprint.HTML(string=html).write_pdf()
    
    pdf_file = PdfFile.objects.get(id=pdf_id)
    pdf_file.file.save(pdf_file.name, ContentFile(pdf))
    pdf_file.status = PdfFile.Status.COMPELETED
    pdf_file.save()


@shared_task
def release_stock(order_id):
    try:
        order = Order.objects.get(id=order_id)
        
        if order.status == Order.Status.PENDING:
            if order.session_id:
                stripe.checkout.Session.expire(order.session_id)
            order.status = Order.Status.CANCELLED
            order.save()
            for item in order.order_items.all():
                item.item.stock += item.quantity
                item.item.sales -= item.quantity
                item.item.save()
        
    except Order.DoesNotExist:
        pass