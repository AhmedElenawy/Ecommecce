"""
URL configuration for ecommerce project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


from django.contrib import admin
from django.urls import path

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.i18n import set_language
from django.utils.translation import gettext_lazy as _
from django.conf.urls.i18n import i18n_patterns
from payment import webhooks
from order import dashboard


urlpatterns = i18n_patterns(
    path('admin/', dashboard.dashboard_index, name='admin_dashboard'),
    path('admin/', admin.site.urls),
    path('i18n/setlang/', set_language, name='set_language'),
    path('', include('store.urls', namespace='store')),
    path(_('cart/'), include('cart.urls', namespace='cart')),
    path(_('order/'), include('order.urls', namespace='order')),
    path(_('payment/'), include('payment.urls', namespace='payment')),
    path(_('coupon/'), include('coupon.urls', namespace='coupon')),
    path(_('authenticate/'), include('authenticate.urls', namespace='authenticate')),
    
    
)

urlpatterns += [
    path('__debug__/', include('debug_toolbar.urls')),
    path('payment/webhook/', webhooks.stripe_webhook, name='stripe-webhook',),
    path('payment/paymob_webhook/', webhooks.paymob_webhook, name='paymob-webhook'),
    path('social-auth/',include('social_django.urls', namespace='social')),
]

#  add media urls to my project in development
if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )


