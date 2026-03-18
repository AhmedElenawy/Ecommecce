from django.urls import path, include
from django.utils.translation import gettext_lazy as _

from . import views
app_name = 'coupon'

urlpatterns = [
    path(_('apply_coupon/'), views.apply_coupon, name='apply_coupon'),
    path(_('remove_coupon/'), views.remove_coupon, name='remove_coupon'),
]