from django.urls import path, include
from django.utils.translation import gettext_lazy as _

from . import views
app_name = 'authenticate'

urlpatterns = [
    path(_('login/'), views.login_view, name='login'),
    path(_('register/'), views.register, name='register'),
    path(_('logout/'), views.logout_view, name='logout'),
    path(_('password-reset/'), views.password_reset, name='password_reset'),
    path(_('confirm-otp/'), views.confirm_otp, name='confirm_otp'),
    path(_('new-password/'), views.new_password, name='new_password'),
    path(_('resend-otp/'), views.resend_otp, name='resend_otp'),

    
]
