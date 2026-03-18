
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.shortcuts import redirect
# Register your models here.
from .models import Order, OrderItems, PdfFile, OrderAddress
from .tasks import orders_invoices
import csv
import datetime
from django.http import HttpResponse

from django.utils.translation import gettext_lazy as _




def generate_orders_invoices(modeladmin, request, queryset):
    id_list = list(queryset.values_list("id", flat=True))
    pdf = PdfFile.objects.create(name="orders_%(datetime)s.pdf" % {'datetime': datetime.datetime.now()})
    orders_invoices.delay(id_list, pdf.id)
    return redirect(reverse("admin:order_pdffile_change", args= [pdf.id]))
    
generate_orders_invoices.short_description = _("Generate Invoices")



#  its general we can add it to any admin model
# current admin orderadmin
# queryset of selected item
def exp_csv(modeladmin, request, queryset):
    #  get model data
    # returns id, user, name, mobile, address, city, paid, created, updated, items
    model_data = modeladmin.model._meta
    model_name = model_data.verbose_name
    # content_desposition is htttp header tell browser what to do whith this
    # attachment means to download it
    content_desposition = f"attachment; filename={model_name}.csv"
    #  initialise http respond
    respond = HttpResponse(content_type="text/csv")
    respond["Content-Disposition"] = f"attachment; filename={model_name}.csv"
    # intialiaz csv writer that write directly to respond
    writer = csv.writer(respond)
    # dynimacilly get field
    # filter to many relationship
    fields = [field
            for field in model_data.get_fields()
            if not field.many_to_many and not field.one_to_many and not field.one_to_one]
    #  write title
    writer.writerow([field.verbose_name for field in fields])
    # write data
    for obj in queryset:
        obj_data =[]
        for field in fields:
            value = getattr(obj, field.name)
            # check if the data i spesific data type
            # reformatt it
            if isinstance(value, datetime.datetime):
                value = value.strftime('%d/%m/%Y')
            obj_data.append(value)
        writer.writerow(obj_data)

    return respond
# desplayed name in admin
exp_csv.short_description = _('Export CSV')

def generate_invoice(obj):
    url = reverse("order:generate_invoice", args=[obj.id])
    return mark_safe('<a href="%(url)s">%(text)s</a>' % {'url': url, 'text': _('Generate Invoice')})
generate_invoice.short_description = _('Invoice')

def payment_link(obj):
    if obj.payment_id:
        url = obj.get_payment_url()
        return mark_safe('<a href="%(url)s" target="_blank">%(payment_id)s</a>' % {'url': url, 'payment_id': obj.payment_id})
    return '-'
payment_link.short_description = _('Payment ID')



def total_price(obj):
    return str(obj.get_total_price_after_discount_shipping())
total_price.short_description = _('Total Price')

