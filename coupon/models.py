from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from django.conf import settings
from django.utils.translation import gettext_lazy as _



        
class Coupon(models.Model):
    code = models.CharField(_('code'), max_length=50, unique=True)
    discount = models.IntegerField(_('discount'), validators=[MinValueValidator(0), MaxValueValidator(100)])
    valid_from = models.DateTimeField(_('valid from'))
    valid_to = models.DateTimeField(_('valid to'))
    active = models.BooleanField(_('active'))
    usage_limit = models.IntegerField(_('usage limit'), default=1)
    max_discount = models.IntegerField(_('max discount'), default=0)

    

    def __str__(self):
        return self.code
    
    def is_valid(self, request):
        now = timezone.now()
        if not request.user.is_authenticated:
            raise Exception(_("User is not authenticated"))
        user_usage = self.coupon_usages.filter(user=request.user).count()
        if now < self.valid_from:
            raise Exception(_("Coupon is not active yet"))
        elif now > self.valid_to:
            raise Exception(_("Coupon is expired"))
        elif not self.active:
            raise Exception(_("Coupon is not active"))
        elif user_usage >= self.usage_limit:
            raise Exception(_("Coupon usage limit reached"))
        return True
    
    class Meta:
        verbose_name = _('coupon')
        verbose_name_plural = _('coupons')

class CouponUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_coupons')
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, related_name='coupon_usages')
    used_at = models.DateTimeField(_('used at'), default=timezone.now)
    
    class Meta:
        verbose_name = _('coupon usage')
        verbose_name_plural = _('coupon usages')

