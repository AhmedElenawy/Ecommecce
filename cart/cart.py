from store.models import Product
from coupon.models import Coupon
from django.conf import settings
from decimal import Decimal
from django.contrib import messages
from django.utils.translation import gettext as _

class Cart:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}

        self.cart = cart
        self.coupon_id = self.session.get('coupon_id')
        self.coupon_object = self.coupon
        # self.shipping_price = 5


    def __iter__(self):
        item_ids = list(int(id) for id in self.cart)
        # if item_ids:
        items = Product.active.filter(id__in=item_ids).select_related("category").defer('description', 'description_ar', 'description_en', 'created', 'updated')
        cart = self.cart.copy()

        for item in items:
            cart[str(item.id)]['item'] = item
            
        for item in cart.values():
            stock = item['item'].stock
            if stock <= 0:
                messages.warning(self.request, _('sorry %(product)s is out of stock, we have removed it from your cart') % {'product': item['item'].name})
                self.remove_item(item['item'])
                continue
            elif item['quantity'] > stock:
                messages.warning(self.request, _('only %(stock)d %(product)s available, we have updated the quantity from %(quantity)d to %(stock)d') % {'product': item['item'].name, 'quantity': item['quantity'], 'stock': stock})
                item['quantity'] = stock
            item['price'] = Decimal(item["price"])
            item["total_price"] = item['quantity'] * item['price']
            yield item
        


    # calc total items
    def __len__(self):
        return sum(int(item["quantity"]) for item in self.cart.values())
    
    @property
    def coupon(self):
        try:
            if self.coupon_id:
                return Coupon.objects.get(id=self.coupon_id)
        except:
            return None
        return None
    
    def discount(self):
        coupon = self.coupon_object
        if coupon:
            discount = (coupon.discount / Decimal(100)) * self.get_total_price()
            if discount > coupon.max_discount:
                discount = Decimal(coupon.max_discount)
            return discount
        return 0
    
    def get_total_price(self):
        return sum(Decimal(item["price"] * item["quantity"]) for item in self.cart.values())
    
    def get_total_price_after_discount_shipping(self):
        return self.get_total_price() - self.discount()
        

    def save(self):
        self.session.modified = True


    def clear(self):
        
        
        # del self.cart. >>> they are reference to the same object but when we delete we delete the label not the object in memory
        # this remove the key not the reference dict
        del self.session[settings.CART_SESSION_ID]
        self.save()

    def remove_item(self, item):
        item_id = str(item.id)
        if item_id and self.cart:
            del self.cart[item_id]
            self.save()



        # [ {id : {"quantity": 0, "price": str(item.price)}} ]>>>str
    def add_or_update(self, item, quantity, replace=False):
        item_id = str(item.id)
        if item_id not in self.cart:
            self.cart[item_id] = {"quantity": 0, "price": str(item.price)}

        if replace:
            #in case of first add
            self.cart[item_id]["quantity"] = quantity
        else:
            self.cart[item_id]["quantity"] += quantity

        self.save()
        
    

        