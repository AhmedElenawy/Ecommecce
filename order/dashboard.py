from django.shortcuts import render
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.urls import reverse
from django.utils.translation import gettext_lazy as _, get_language
from django.utils.timezone import timedelta
from django.utils import timezone

from .models import Order, OrderItems
from store.models import Product
from django.utils.encoding import force_str
import json


def _admin_changelist_url(app_label, model_name, **query_params):
    """Build admin changelist URL with optional filter query params."""
    url = reverse(f"admin:{app_label}_{model_name}_changelist")
    if query_params:
        from urllib.parse import urlencode
        url += "?" + urlencode(query_params)
    return url


@staff_member_required
def dashboard_index(request):
    """
    Custom admin dashboard view rendered with Unfold and a rich index template.
    """
    # Aggregate orders data (Python-level for computed total)
    paid_orders_qs = Order.objects.filter(paid=True).prefetch_related("order_items")
    orders_count = paid_orders_qs.count()
    total_revenue = sum(
        order.get_total_price_after_discount_shipping() for order in paid_orders_qs
    )
    average_order_value = total_revenue / orders_count if orders_count > 0 else 0

    # Pending orders
    pending_orders_count = Order.objects.filter(status=Order.Status.PENDING, paid=False).count()

    # Order status breakdown for chart (translated labels)
    _status_labels = {
        Order.Status.PENDING: _("Pending"),
        Order.Status.PAID: _("Paid"),
        Order.Status.SHIPPED: _("Shipped"),
        Order.Status.DELIVERED: _("Delivered"),
        Order.Status.CANCELLED: _("Cancelled"),
    }
    order_status_data = (
        Order.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    order_status_labels = [
        force_str(_status_labels.get(s["status"], s["status"])) 
        for s in order_status_data
    ]
    order_status_counts = [s["count"] for s in order_status_data]

    # Aggregate active product stock
    active_products = Product.active.aggregate(
        count=Count("id"),
        total_stock=Sum("stock"),
    )
    active_products_count = active_products.get("count") or 0
    total_stock = active_products.get("total_stock") or 0
    average_stock = total_stock / active_products_count if active_products_count > 0 else 0

    # Top selling products for charts / tables (include stock for display)
    top_selling_products = list(
        Product.objects.all()
        .order_by("-sales")[:10]
        .values("id", "name", "slug", "sales", "stock")
    )
    top_products_labels = [p["name"] for p in top_selling_products]
    top_products_sales = [p["sales"] for p in top_selling_products]

    low_stock_products = list(
        Product.objects.filter(stock__lt=7)
        .order_by("stock")
        .values("id", "name", "slug", "stock")[:10]
    )

    # Revenue and orders per day (last 7 days, oldest first for chart)
    today = timezone.now().date()
    revenue_per_day = {today - timedelta(days=x): 0 for x in range(7)}
    orders_count_per_day = {today - timedelta(days=x): 0 for x in range(7)}
    orders_of_the_week = Order.objects.filter(
        paid=True, created__date__gte=today - timedelta(days=6)
    ).prefetch_related("order_items")
    for order in orders_of_the_week:
        created_date = order.created.date()
        if created_date in revenue_per_day:
            revenue_per_day[created_date] += float(order.get_total_price_after_discount_shipping())
            orders_count_per_day[created_date] += 1

    sorted_dates = sorted(revenue_per_day.keys())
    revenue_dates = [d.strftime("%Y-%m-%d") for d in sorted_dates]
    revenue_values = [revenue_per_day[d] for d in sorted_dates]
    orders_per_day_values = [orders_count_per_day[d] for d in sorted_dates]

    # Admin URLs with filters for quick navigation
    admin_urls = {
        "orders_all": _admin_changelist_url("order", "order"),
        "orders_paid": _admin_changelist_url("order", "order", paid__exact=1),
        "orders_pending": _admin_changelist_url(
            "order", "order", status__exact=Order.Status.PENDING
        ),
        "products_all": _admin_changelist_url("store", "product"),
        "products_low_stock": _admin_changelist_url("store", "product", stock__lt=7),
    }

    language_code = get_language() or "en"
    is_rtl = language_code.startswith("ar")

    context = admin.site.each_context(request)
    context.update(
        {
            "is_rtl": is_rtl,
            "locale": language_code.replace("-", "_"),
            "orders_count": orders_count,
            "total_revenue": total_revenue,
            "average_order_value": average_order_value,
            "pending_orders_count": pending_orders_count,
            "active_products_count": active_products_count,
            "total_stock": total_stock,
            "average_stock": average_stock,
            "top_selling_products": top_selling_products,
            "low_stock_products": low_stock_products,
            "top_products_labels_json": json.dumps(top_products_labels, ensure_ascii=False),
            "top_products_sales_json": json.dumps(top_products_sales),
            "revenue_dates_json": json.dumps(revenue_dates),
            "revenue_values_json": json.dumps(revenue_values),
            "orders_per_day_json": json.dumps(orders_per_day_values),
            "order_status_labels_json": json.dumps(order_status_labels, ensure_ascii=False),
            "order_status_counts_json": json.dumps(order_status_counts),
            "admin_urls": admin_urls,
        }
    )

    return render(request, "admin/index.html", context)
    

    