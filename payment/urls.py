from django.urls import path, include
from django.utils.translation import gettext_lazy as _

from . import views, webhooks

app_name = 'payment'

urlpatterns = [
    path(_('proccess'), views.payment_proccess, name='proccess'),
    path(_('completed'), views.payment_completed, name='completed'),
    path(_('canceled'), views.payment_canceled, name='canceled'),

]