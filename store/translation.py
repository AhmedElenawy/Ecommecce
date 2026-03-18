from modeltranslation.translator import register, TranslationOptions
from .models import Category, Product
from taggit.models import Tag

@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'slug')


@register(Tag)
class TagTranslationOptions(TranslationOptions):
    fields = ('name', 'slug')

@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'slug', 'description')


    
