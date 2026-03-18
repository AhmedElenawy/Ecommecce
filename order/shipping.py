import requests
from django.conf import settings
from .models import Order
from django.shortcuts import get_object_or_404, render, redirect
from django.core.cache import cache

class ShipmentError(Exception):
    pass


class Shipping:
    def __init__(self):
        self.token = settings.BOSTA_TOKEN
        self.base_url = settings.BOSTA_BASE_URL
        self.headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        self.country_id = settings.BOSTA_COUNTRY_ID
        
    def get_shipping_cities(self):
        cities = cache.get('shipping_cities')
        if cities:
            return cities

        url = f"{self.base_url}/cities"
        querystring = {"country_id": self.country_id}
        response = requests.request("GET", url, headers=self.headers, params=querystring)
        
        if response.status_code != 200:
            raise ShipmentError("Failed to get shipping cities", response.status_code)
        
        # 1. Cities JSON structure is: { data: { list: [...] } }
        data = response.json().get('data', {}).get('list', [])
        
        cities = {city['_id']: city['name'] for city in data}
        
        cache.set('shipping_cities', cities, None)
        return cities
    
    def get_shipping_zones(self, city_id):
        zone_list_keys = f"zone_list:{city_id}"
        zones = cache.get(zone_list_keys)
        if zones:
            return zones

        url = f"{self.base_url}/cities/{city_id}/zones"
        response = requests.request("GET", url, headers=self.headers)
        
        if response.status_code != 200:
            raise ShipmentError("Failed to get shipping zones", response.status_code)
        
        # 2. Zones JSON structure is: { data: [...] } (Direct list, no 'list' key)
        data = response.json().get('data', [])
        
        zones = {zone['_id']: zone['name'] for zone in data}
        
        cache.set(zone_list_keys, zones, None)
        return zones
    
    def get_shipping_districts(self, city_id, zone_id):
        district_list_keys = f"district_list:{city_id}:{zone_id}"
        districts = cache.get(district_list_keys)
        if districts:
            return districts

        # 3. Fixed URL (Added slash before cities)
        url = f"{self.base_url}/cities/{city_id}/districts"
        response = requests.request("GET", url, headers=self.headers)
        
        if response.status_code != 200:
            raise ShipmentError(f"Failed to get shipping zones. Code: {response.status_code}, Body: {response.text}")
        
        # 4. Districts JSON structure is: { data: [...] } (Direct list)
        try:
            data = response.json().get('data', [])
        except requests.exceptions.JSONDecodeError:
            # Print the raw text so you can see exactly what Bosta returned in your terminal
            print(f"BOSTA API DEBUG - URL: {url}")
            print(f"BOSTA API DEBUG - Raw response body: '{response.text}'")
            raise ShipmentError("Invalid JSON response from Bosta API")
        
        # 5. Fixed Keys: JSON uses 'districtName' and 'districtId', not 'name'
        districts = {
            district['districtId']: district['districtName']
            for district in data 
            if district.get('zoneId') == zone_id
        }
        
        cache.set(district_list_keys, districts, None)
        return districts
        
    
    def get_shipping_rate(self, dropoff_city, pickup_city="Cairo", size="Normal", type="SEND", cod="0"):
        # Ensure base_url includes /api/v2 if not already part of self.base_url
        url = f"{self.base_url}/pricing/shipment/calculator"
        
        querystring = {
            "dropOffCity": dropoff_city,
            "pickupCity": pickup_city,
            "cod": cod,
            "type": type, # Docs use "SEND"
            "size": size  # Docs use "Normal"
        }
        
        response = requests.request("GET", url, headers=self.headers, params=querystring)
        
        if response.status_code == 200:
            return response.json()
            
        raise ShipmentError("Failed to get shipping rate", response.status_code)
    
    def create_shipping_order(self, order_id, type=10, size="medium", cod="0", notes=None):
        try:
            order = Order.objects.get(id=order_id).select_related('user', 'shipping_address').prefetch_related('order_items')
        except Order.DoesNotExist:
            raise ShipmentError("Order not found")
        
        url = f"{self.base_url}/deliveries"
        querystring = {"apiVersion":"1"}
        payload = {
            "type": type,
            "specs": {
                "packageType": "Parcel",
                "size": size,
                "packageDetails": {
                    "itemsCount": sum(item.quantity for item in order.order_items.all()),
                    "description": "Desc."
                }
            },
            "notes": notes,
            "cod": cod,
            "dropOffAddress": {
                "city": order.shipping_address.city,
                "zoneId": order.shipping_address.zone_id,
                "districtId": order.shipping_address.district_id,
                "firstLine": order.shipping_address.address,
                "secondLine": order.second_line,
                "buildingNumber": order.shipping_address.building_number,
                "floor": order.shipping_address.floor,
                "apartment": order.shipping_address.apartment
            },
            "pickupAddress": {
                "city": "Helwan",
                "zoneId": "NQz5sDOeG",
                "districtId": "aiJudRHeOt",
                "firstLine": "Helwan street x",
                "secondLine": "Near to Bosta school",
                "buildingNumber": "123",
                "floor": "4",
                "apartment": "2"
            },
            "returnAddress": {
                "city": "Helwan",
                "zoneId": "NQz5sDOeG",
                "districtId": "aiJudRHeOt",
                "firstLine": "Maadi",
                "secondLine": "Nasr  City",
                "buildingNumber": "123",
                "floor": "4",
                "apartment": "2"
            },
            "businessReference": "43535252",
            "receiver": {
                "firstName": order.user.first_name,
                "lastName": order.user.last_name,
                "phone": order.shipping_address.mobile,
                "email": order.user.email
            },
            "webhookUrl": "https://www.google.com/"
        }
            
    


