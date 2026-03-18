from django import forms
from django.utils.translation import gettext_lazy as _
from .models import OrderAddress

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = OrderAddress
        # Include all fields required by the model, including the ID fields
        # Note: 'distinct' is used because that is the field name in your models.py
        fields = [
            'mobile', 
            'city', 'city_id', 
            'zone', 'zone_id', 
            'distinct', 'district_id', 
            'address', 'secondLine', 'buildingNumber', 'floor', 'apartment'
        ]
        
        widgets = {
            'mobile': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent',
                'type': 'tel',
                'placeholder': '+20 1XX XXX XXXX'
            }),
            # Hidden fields for Names and IDs (Populated by JS)
            'city': forms.HiddenInput(),
            'city_id': forms.HiddenInput(),
            'zone': forms.HiddenInput(),
            'zone_id': forms.HiddenInput(),
            'distinct': forms.HiddenInput(), # This maps to the district name
            'district_id': forms.HiddenInput(),
            
            'address': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent',
                'placeholder': 'Street address'
            }),
            'secondLine': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent',
                'placeholder': 'Landmark (Optional)',
            }),
            'buildingNumber': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent',
                'placeholder': 'Building number'
            }),
            'floor': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent',
                'placeholder': 'Floor'
            }),
            'apartment': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent',
                'placeholder': 'Apartment'
            }),
        }
        
        labels = {
            'distinct': _('District'),
            'secondLine': _('Second Line'),
            'buildingNumber': _('Building Number')
        }