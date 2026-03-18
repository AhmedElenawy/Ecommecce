from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Discount

class BulkDiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = ['discount', 'valid_from', 'valid_to', 'active']
        
        # Native Tailwind classes applied directly to the inputs
        input_classes = 'w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:focus:border-indigo-500 dark:focus:ring-indigo-500 transition-colors'
        
        widgets = {
            'discount': forms.NumberInput(attrs={
                'class': input_classes,
                'placeholder': 'e.g., 15.00', 
                'step': '0.01'
            }),
            'valid_from': forms.DateTimeInput(attrs={
                'type': 'datetime-local', 
                'class': input_classes
            }),
            'valid_to': forms.DateTimeInput(attrs={
                'type': 'datetime-local', 
                'class': input_classes
            }),
            'active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 dark:border-gray-700 dark:bg-gray-900 cursor-pointer transition-colors'
            })
        }