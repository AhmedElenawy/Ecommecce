import requests
from django.conf import settings
from decimal import Decimal
import stripe


class PaymobError(Exception):
    pass


def paymob_payment(order, success_url, cancel_url, webhook_url):
    api_key = settings.PAYMOB_API_KEY
    secret_key = settings.PAYMOB_SECRET_KEY
    public_key = settings.PAYMOB_PUBLIC_KEY
    base_url = settings.PAYMOB_BASE_URL
    headers = {'Authorization': f'Token {secret_key}', 'Content-Type': 'application/json'}

    payload = {
        "amount": int(order.get_total_price_after_discount_shipping() * Decimal('100')),
        "currency": "EGP",
        "payment_methods": [
            5545466, 5578325, 5578345
        ],
        "items": [],
        "billing_data": {
            "first_name": order.user.first_name,
            "last_name": order.user.last_name,
            "email": order.user.email,
            "phone_number": str(order.shipping_address.mobile),
        },
        "extras": {
            "ee": 22
        },
        "special_reference": order.id,
        "expiration": 800,
        "notification_url": webhook_url,
        "redirection_url": success_url
    }
    for item in order.order_items.all():
        payload['items'].append({
            "name": item.item.name,
            "amount": int(item.price * Decimal('100')),
            "description": item.item.description,
            "quantity": item.quantity
        })

    if order.coupon:
        payload['items'].append({
            "name": f"__Coupon: {order.coupon.code}",
            "amount": int(order.discount_amount * -100),
            "description": 'discount',
            "quantity": 1
        })

    if order.shipping_price:
        payload['items'].append({
            "name": "__Shipping",
            "amount": int(order.shipping_price * Decimal('100')),
            "description": 'shipping',
            "quantity": 1
        })

    

    response = requests.post(f"{base_url}intention/", headers=headers, json=payload)
    if response.status_code not in [201, 200]:
        raise PaymobError(response.text)

    client_token = response.json().get('client_secret', '')
    if not client_token:
        raise PaymobError("No client token received from Paymob")
    order.session_id = client_token
    order.save()
    redirect_url = f"https://accept.paymob.com/unifiedcheckout/?publicKey={public_key}&clientSecret={client_token}"
    return redirect_url


from django.core.cache import cache

def get_egp_to_usd_rate():
    # 1. Check if we already looked this up today
    rate = cache.get('egp_usd_rate')
    if rate:
        return rate

    # 2. If not, ask the free API
    url = "https://open.er-api.com/v6/latest/EGP"
    fallback_rate = Decimal('0.020') # Example: 1 EGP = 0.020 USD (Approx 50 EGP per USD)

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            rate = Decimal(str(data['rates']['USD']))
            
            # Save it in Django's cache for 24 hours (86400 seconds)
            cache.set('egp_usd_rate', rate, 86400)
            return rate
            
    except Exception as e:
        print(f"Warning: Currency API failed ({e}). Using fallback rate.")
    
    # 3. If the API fails, return the safe fallback
    return fallback_rate


def stripe_payment(order, success_url, cancel_url):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe.api_version = settings.STRIPE_API_VERSION

    conversion_rate = get_egp_to_usd_rate()
    session_data = {
        # one time payment mode we have several
        'mode': 'payment',
        # link session with our order . we use in web hook
        'client_reference_id': order.id,
        'success_url': success_url,
        'cancel_url': cancel_url,
        'line_items': [],
    }
    #  add item to session
    for item in order.order_items.all():
        item_price_usd = item.price * conversion_rate
        session_data['line_items'].append(
            {
                'price_data': {
                    'unit_amount' : int(item_price_usd * Decimal('100')),
                    'currency' : 'usd',
                    'product_data': {
                        'name': item.item.name
                    },
                },
                'quantity': item.quantity
            }
        )

    

    if order.coupon:
        stripe_coupon = stripe.Coupon.create(
            name=order.coupon.code,
            amount_off=int(order.discount_amount * 100 * conversion_rate),
            duration='once',
            currency='usd'
        )
        session_data['discounts'] = [{'coupon': stripe_coupon.id}]

    if order.shipping_price > 0:
        session_data['shipping_options'] = [
            {
                'shipping_rate_data': {
                    'type': 'fixed_amount',
                    'fixed_amount': {
                        'amount': int(order.shipping_price * 100 * conversion_rate), # Convert to cents
                        'currency': 'usd',
                    },
                    'display_name': 'Standard Shipping', # Visible to user - Stripe requires English
                    
                    # Optional: Add delivery estimate
                    'delivery_estimate': {
                        'minimum': {'unit': 'business_day', 'value': 3},
                        'maximum': {'unit': 'business_day', 'value': 5},
                    },
                }
            }
        ]


        # create stripe session and intialize it it will send request and return session contain url
    session = stripe.checkout.Session.create(**session_data)
    order.session_id = session.id
    order.save()
    return session.url