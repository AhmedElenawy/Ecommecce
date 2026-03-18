from django.contrib import admin
from unfold.admin import ModelAdmin
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

from .admin_helper import exp_csv, total_price, payment_link, generate_invoice, generate_orders_invoices


@admin.register(PdfFile)
class PdfFileAdmin(ModelAdmin):
    list_display = ["name", "status", "file"]



class OrderItemsInline(admin.TabularInline):
    model = OrderItems
    extra = 1
    fields = ['item', 'quantity', 'price']
    readonly_fields = ['item', 'quantity', 'price']

class OrderAddressInline(admin.TabularInline):
    model = OrderAddress
    extra = 1

    

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ['id', 'user',
                    'paid','shipping_status',
                    'created', 'updated', 'status',
                    total_price, payment_link, generate_invoice]
    list_filter = ['paid', 'status', 'shipping_status', 'created', 'updated']
    search_fields = ['user__email', 'mobile', 'address', 'id']
    ordering = ['-created', 'updated']
    inlines = [OrderItemsInline, OrderAddressInline]
    actions = [exp_csv, generate_orders_invoices]
