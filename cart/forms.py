from django import forms
from django.utils.translation import gettext_lazy as _

PRODUCT_QUANTITY_CHOICES = [(i, str(i)) for i in range(1, 21)]
# add if the user add it from product detail increment 
# replace if user increment from carrt detail
class add_or_replace_quantity(forms.Form):
    quantity = forms.TypedChoiceField(
        label=_('quantity'),  # Add 'label=' keyword
        choices=PRODUCT_QUANTITY_CHOICES, 
        coerce=int
    )
    replace = forms.BooleanField(label=_('replace'), widget=forms.HiddenInput, initial=False, required=False)
