from django.views.decorators.http import require_POST
from .models import Coupon
from .forms import CouponForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.utils.translation import gettext as _

@require_POST
def apply_coupon(request):
    form = CouponForm(request.POST)
    if form.is_valid():
        code = form.cleaned_data["code"]
        try:
            coupon = Coupon.objects.get(code=code)
            if coupon.is_valid(request):
                request.session['coupon_id'] = coupon.id
                messages.success(request, _("Coupon applied successfully"))
        except Coupon.DoesNotExist:
            messages.error(request, _("Coupon does not exist"))
        except Exception as e:
            request.session['coupon_id'] = None
            messages.error(request, str(e))
    return redirect("cart:cart_detail")


def remove_coupon(request):
    request.session['coupon_id'] = None
    return redirect("cart:cart_detail")
