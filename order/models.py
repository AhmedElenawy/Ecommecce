from django.db import models

from phonenumber_field.modelfields import PhoneNumberField
# Create your models here.
from django.conf import settings
from store.models import Product
from coupon.models import Coupon
from django.core.validators import MaxValueValidator, MinValueValidator
from decimal import Decimal
from django.utils.translation import gettext_lazy as _

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending'
        PAID = 'paid'
        SHIPPED = 'shipped'
        DELIVERED = 'delivered'
        CANCELLED = 'cancelled'
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='orders', null=True)

    
    status = models.CharField(_('status') ,choices=Status, default=Status.PENDING, max_length=250)
    paid = models.BooleanField(_('paid'), default=False)
    created = models.DateTimeField(_('created'), auto_now_add=True)
    updated = models.DateTimeField(_('updated'), auto_now=True)
    payment_id = models.CharField(_('payment ID'), max_length=250, null=True)
    session_id = models.CharField(_('session ID'), max_length=250, null=True, blank=True)
    payment_method = models.CharField(_('payment method'), max_length=250, null=True, blank=True)


    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.IntegerField(_('discount amount'), default=0, validators=[MinValueValidator(0), MaxValueValidator(1000)])

    shipping_price = models.DecimalField(_('shipping price'), max_digits=8, decimal_places=2, default=0)
    shipping_status = models.BooleanField(_('shipping status'), default=False)
    class Meta:
        verbose_name = _('order')
        verbose_name_plural = _('orders')
        ordering = ["-created"]
        indexes = [models.Index(fields=["-created"])]

    def __str__(self):
        return self.user.first_name
    
    
    def discount(self):
        # if self.discount_amount > 0:
        #     return (self.discount_amount / Decimal(100)) * self.get_total_price()
        return self.discount_amount

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.order_items.all() )
    
    def get_total_price_after_discount_shipping(self):
        return self.get_total_price() - self.discount_amount + self.shipping_price
    
    def get_payment_url(self):
        if self.payment_id:
            if "pi_" in self.payment_id:
                if '_test_' in settings.STRIPE_SECRET_KEY:
                    return f"https://dashboard.stripe.com/test/payments/{self.payment_id}"
                return f"https://dashboard.stripe.com/payments/{self.payment_id}"
            else:
                return f"https://eg.dashboard.paymob.com/transaction/{self.payment_id}"
        return ""



class OrderItems(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    item = models.ForeignKey(Product, on_delete=models.SET_NULL, related_name="product_orders", null=True)
    quantity = models.PositiveIntegerField(_('quantity'), default=1)
    price = models.DecimalField(_('price'), max_digits=8, decimal_places=2)
    
    class Meta:
        verbose_name = _('order item')
        verbose_name_plural = _('order items')

    def get_total_price(self):
        return self.quantity * self.price
    


class OrderAddress(models.Model):
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='shipping_address')
    mobile = PhoneNumberField(_('mobile'), unique=False, region="EG", blank=False, null=True)
    address = models.CharField(_('address'), max_length=250)
    city = models.CharField(_('city'), max_length=250, blank=True, null=True)
    city_id = models.CharField(_('city ID'), max_length=200, blank=True, null=True)
    zone = models.CharField(_('zone'), max_length=250, blank=True, null=True)
    zone_id = models.CharField(_('zone ID'), max_length=200, blank=True, null=True)
    distinct = models.CharField(_('district'), max_length=250, blank=True, null=True)
    district_id = models.CharField(_('district ID'), max_length=200, blank=True, null=True)
    secondLine = models.CharField(_('second line'), max_length=500, blank=True, null=True)
    buildingNumber = models.CharField(_('building number'), max_length=250, blank=False, null=True)
    floor = models.CharField(_('floor'), max_length=250, blank=False, null=True)
    apartment = models.CharField(_('apartment'), max_length=250, blank=True, null=True)


class PdfFile(models.Model):
    class Status(models.TextChoices):
            PENDING = "pending", _('Pending')
            COMPELETED = "COMPLETED", _('Completed')
    name = models.CharField(_('name'), max_length=255)
    status = status = models.CharField(
         _('status'),
         choices=Status,
         default=Status.PENDING
    )
    file = models.FileField(_('file'), upload_to='pdf_files/')

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('PDF file')
        verbose_name_plural = _('PDF files')