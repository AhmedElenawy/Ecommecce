from django.contrib import admin

from .forms import BulkDiscountForm

from django.contrib import messages

from django.shortcuts import get_object_or_404, render, redirect

from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _




class LowStockFilter(SimpleListFilter):
    title = _('stock')
    parameter_name = 'stock__lt'

    def lookups(self, request, model_admin):
        return (('7', _('Low stock (< 7)')),)

    def queryset(self, request, queryset):
        if self.value() == '7':
            return queryset.filter(stock__lt=7)
        return queryset
    

def add_discount(modeladmin, request, queryset):
    """Action to add bulk discount to selected products"""
    
    # Check if the form was submitted via the 'apply' button
    if 'apply' in request.POST:
        form = BulkDiscountForm(request.POST)
        if form.is_valid():
            discount = form.save(commit=False)
            discount.active = True
            discount.save()
            
            # Django remembers the selected items, so we can update them directly!
            updated_count = queryset.update(discount=discount)
            
            messages.success(request, f"Bulk discount applied to {updated_count} products successfully.")
            return redirect('admin:store_product_changelist')
            
    else:
        # Initial GET/POST from the changelist
        form = BulkDiscountForm()
    context = admin.site.each_context(request)
    context.update(
        {
            'form': form,
            'queryset': queryset,  # We must pass the queryset to the template
            'selected_count': queryset.count(),
            'title': 'Add Bulk Discount'
        }
    )
    return render(request, 'store/admin/add_bulk_discount.html', context)

add_discount.short_description = "Add bulk discount"