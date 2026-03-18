from django.urls import path, include
from django.utils.translation import gettext_lazy as _

from . import views
app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),
    path(_('add/<int:product_id>'), views.add_or_update, name='add_or_update'),
    path(_('remove/<int:product_id>'), views.remove_item, name='remove_item'),
    path(_('dropdown'), views.cart_dropdown_partial, name='cart_dropdown_partial'),
]