from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.product_list_tags, name='product_list_category'),
    path(_('products/'), views.product_list, name='product_list'),
    path(_('search/'), views.search, name='product_search'),
    path(_('product/<int:product_id>/'), views.product_detail, name='product_detail'),
    
]