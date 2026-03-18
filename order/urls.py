from django.urls import path
from django.utils.translation import gettext_lazy as _
from . import views

app_name = 'order'

urlpatterns = [
    path(_('checkout/'), views.checkout, name='checkout'),
    path(_('order_list/'), views.order_list, name='order_list'),
    path(_('order_detail/<int:order_id>/'), views.order_detail, name='order_detail'),
    path(_('generate_invoice/<int:order_id>/'), views.generate_invoice, name='generate_invoice'),
    
    # API Endpoints
    path('api/cities/', views.get_shipping_cities, name='get_cities'),
    path('api/zones/', views.get_shipping_zones, name='get_zones'),
    path('api/districts/', views.get_shipping_districts, name='get_districts'),
    path('api/shipping-rate/', views.get_shipping_rate, name='get_shipping_rate'),
    
    # REMOVED: path('api/test-shipping/', views.test_shipping_api, name='test_shipping'),
]