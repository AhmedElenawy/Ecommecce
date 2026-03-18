from django.contrib import admin
from unfold.admin import ModelAdmin
from modeltranslation.admin import TabbedTranslationAdmin
# Register your models here.
from .models import Product, Category, Discount, Images, ProductVariantGroup
from .forms import BulkDiscountForm
from taggit.models import Tag
from django.contrib import messages

from django.utils.safestring import mark_safe
from django.urls import reverse
from django.shortcuts import get_object_or_404, render, redirect

from django.utils.html import format_html
from django.utils.http import urlencode
from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _
import datetime

from .admin_helper import LowStockFilter, add_discount

class ImagesInline(admin.TabularInline):
    model = Images
    extra = 1
class ProductVariantInline(admin.TabularInline):
    model = Product
    extra = 0
@admin.register(ProductVariantGroup)
class ProductVariantGroupAdmin(ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']
    inlines = [ProductVariantInline]
    readonly_fields = ['add_variant_link']
    @admin.display(description="Add Variant")
    def add_variant_link(self, obj):
        # 1. SAFETY CHECK: If the product isn't saved yet (like on the Add page),
        # return an empty string so it doesn't crash trying to build a URL.
        if not obj or not obj.id:
            return "-"
        pid = Product.active.filter(variant_group_id=obj.id).first().id
        # Generate URL for the standard "Add Product" page
        add_url = reverse("admin:store_product_add")
        
        # Append the current product's ID as a query parameter
        query_string = urlencode({"copy_from_id": pid})
        
        return format_html(
            '<a class="button" style="padding: 5px 10px;" href="{}?{}">+ Variant</a>',
            add_url,
            query_string
        )

@admin.register(Discount)
class DiscountAdmin(ModelAdmin):
    list_display = ['id', 'discount', 'valid_from', 'valid_to', 'active']
    list_editable = ['discount', 'valid_from', 'valid_to', 'active']
    search_fields = ['id', 'discount']

@admin.register(Product)
class ProductAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = ['id','name', 'base_price','discount_percent','price', 'stock', 'is_active', 'created', 'updated']
    list_editable = ['base_price', 'stock', 'is_active']
    list_filter = ['category', 'is_active', LowStockFilter, 'created', 'updated']
    prepopulated_fields = {
        'slug_en': ('name_en',),
        'slug_ar': ('name_ar',)
    }
    search_fields = ['name', 'description', 'category__name']
    actions = [add_discount]
    inlines = [ImagesInline]
    readonly_fields = ['add_variant_link']
    
    
    
    @admin.display(description="Add Variant")
    def add_variant_link(self, obj):
        # 1. SAFETY CHECK: If the product isn't saved yet (like on the Add page),
        # return an empty string so it doesn't crash trying to build a URL.
        if not obj or not obj.id:
            return "-"

        # Generate URL for the standard "Add Product" page
        add_url = reverse("admin:store_product_add")
        
        # Append the current product's ID as a query parameter
        query_string = urlencode({"copy_from_id": obj.id})
        
        return format_html(
            '<a class="button" style="padding: 5px 10px;" href="{}?{}">+ Variant</a>',
            add_url,
            query_string
        )
    
    def get_changeform_initial_data(self, request):
        # Get standard initial data
        initial = super().get_changeform_initial_data(request)
        
        # Check the URL for our custom 'copy_from_id' parameter
        copy_from_id = request.GET.get('copy_from_id')
        
        if copy_from_id:
            # Fetch the source product from the database
            source_product = Product.objects.filter(id=copy_from_id).first()
            
            if source_product:
                # Inject the source product's data into the new form
                initial['variant_group'] = source_product.variant_group_id
                initial['category'] = source_product.category_id
                initial['name'] = source_product.name
                initial['name_en'] = source_product.name_en
                initial['name_ar'] = source_product.name_ar
                initial['slug'] = f"{source_product.slug}{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"  # Ensure slug uniqueness
                initial['slug_en'] = f"{source_product.slug_en}{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"  # Ensure slug uniqueness
                initial['slug_ar'] = f"{source_product.slug_ar}{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"  # Ensure slug uniqueness
                initial['description'] = source_product.description
                initial['description_en'] = source_product.description_en
                initial['description_ar'] = source_product.description_ar
                initial['base_price'] = source_product.base_price
                initial['discount'] = source_product.discount_id
                initial['image'] = source_product.image
                
                # Force the new copy to be a standard variant
                initial['is_base_variant'] = False 

        return initial


@admin.register(Category)
class CategoryAdmin(TabbedTranslationAdmin):
    list_display = ['name', 'slug', 'products_link'] # Added link to list view too
    
    prepopulated_fields = {
        'slug_en': ('name_en',),
        'slug_ar': ('name_ar',)
    }
    search_fields = ['name']

    # 1. FIX: Add the method to readonly_fields so it can be used in 'fields'
    readonly_fields = ['products_link'] 

    fields = ['name', 'slug', 'image', 'products_link']

    @admin.display(description="Related Products")
    def products_link(self, obj):
        if not obj or not obj.id:
            return "-"
        url = (
            reverse("admin:store_product_changelist")
            + "?"
            + urlencode({"category__id__exact": obj.id})
        )
        # Use format_html for safety (better than mark_safe)
        return format_html('<a href="{}" class="button" style="padding:5px 10px;">View Products</a>', url)


admin.site.unregister(Tag)
@admin.register(Tag)
class TagAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name"]
    # Prepopulate slug from name (works for English and Arabic if set up correctly)
    prepopulated_fields = {
        'slug_en': ('name_en',),
        'slug_ar': ('name_ar',)
    }