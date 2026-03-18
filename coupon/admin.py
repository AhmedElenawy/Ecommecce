from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Coupon
# Register your models here.

@admin.register(Coupon)
class CouponAdmin(ModelAdmin):
    pass
