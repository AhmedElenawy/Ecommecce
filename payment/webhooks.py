import stripe
from django.conf import settings
from django.http import HttpResponse ,HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from order.models import Order
from store.models import Product
from django.shortcuts import get_object_or_404, redirect, render
import json
from .tasks import send_invoice, after_payment
from store.recommendation import recommendation
import hmac
import hashlib
# dont check csrf
# request is from stripe server
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']

    # define event out of scope
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        #  invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # invalid signnature
        return HttpResponse(status=400)
    
    if event.type == 'checkout.session.completed':
        #  this is the session i sent
        session = event.data.object
        if session.mode == 'payment' and session.payment_status == 'paid':
            after_payment.delay(session.client_reference_id, session.payment_intent)
    return HttpResponse(status=200)
    


def get_HMAC_signature(payload, hmac_secret):
    obj = payload.get("obj", {})
    type = payload.get('type')
    if  not obj or type != "TRANSACTION":
        return None
    
    def to_str(value):
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return ""
        return str(value)
    
    concatenated_str = (
            to_str(obj.get('amount_cents')) +
            to_str(obj.get('created_at')) +
            to_str(obj.get('currency')) +
            to_str(obj.get('error_occured')) +
            to_str(obj.get('has_parent_transaction')) +
            to_str(obj.get('id')) +
            to_str(obj.get('integration_id')) +
            to_str(obj.get('is_3d_secure')) +
            to_str(obj.get('is_auth')) +
            to_str(obj.get('is_capture')) +
            to_str(obj.get('is_refunded')) +
            to_str(obj.get('is_standalone_payment')) +
            to_str(obj.get('is_voided')) +
            to_str(obj.get('order', {}).get('id')) +
            to_str(obj.get('owner')) +
            to_str(obj.get('pending')) +
            to_str(obj.get('source_data', {}).get('pan')) +
            to_str(obj.get('source_data', {}).get('sub_type')) +
            to_str(obj.get('source_data', {}).get('type')) +
            to_str(obj.get('success'))
        )
    return hmac.new(
        hmac_secret.encode('utf-8'),
        concatenated_str.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()





@csrf_exempt
def paymob_webhook(request):
    received_hmac = request.GET.get('hmac')
    if not received_hmac:
        return HttpResponseForbidden("Missing HMAC signature")

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)
    
    calculated_hmac = get_HMAC_signature(payload, settings.PAYMOB_HMAC)
    if not calculated_hmac:
        return HttpResponse(status=200)

    if not hmac.compare_digest(calculated_hmac, received_hmac):
        return HttpResponseForbidden("Invalid HMAC signature")

    if not payload["obj"]["success"]:
        return HttpResponse(status=400)

    # code here
    obj = payload.get('obj', {})
    order_id = obj.get("order", {}).get("merchant_order_id")
    payment_id = obj.get("id")
    if not order_id:
        return HttpResponseForbidden("Missing order ID")
    after_payment.delay(order_id, payment_id)
    return HttpResponse(status=200)
