import django_filters
from django import forms
from .models import Product, Category
from taggit.models import Tag, TaggedItem # Import TaggedItem

class ProductFilter(django_filters.FilterSet):
    max_price = django_filters.NumberFilter(field_name='base_price', lookup_expr='lte')
    low_price = django_filters.NumberFilter(field_name='base_price', lookup_expr='gte')
    category = django_filters.ModelMultipleChoiceFilter(
        queryset=Category.objects.all(),
        field_name='category',
        conjoined=False,
        widget=forms.CheckboxSelectMultiple()
    )
    
    # 1. Add method='filter_by_tags' to override the default JOIN behavior
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        method='filter_by_tags', 
        widget=forms.CheckboxSelectMultiple()
    )
    
    in_stock = django_filters.BooleanFilter(
        field_name='stock', 
        lookup_expr='gt',
        method='filter_in_stock'
    )
    
    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset

    # 2. Define the custom tag filtering logic
    def filter_by_tags(self, queryset, name, value):
        if not value:
            return queryset
        
        # 'value' is a list of Tag instances selected in the form
        tag_ids = [tag.id for tag in value]
        
        # Create a subquery to fetch IDs directly from the taggit table
        # This completely avoids the slow INNER JOIN and DISTINCT operations
        tagged_product_ids = TaggedItem.objects.filter(
            content_type__model='product',
            tag_id__in=tag_ids
        ).values_list('object_id', flat=True)
        
        return queryset.filter(id__in=tagged_product_ids)
    
    class Meta:
        model = Product
        fields = ['max_price', 'low_price', 'category', 'tags', 'in_stock']