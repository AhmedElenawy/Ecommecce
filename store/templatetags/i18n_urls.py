from django import template
from django.urls import reverse, resolve
from django.utils.translation import override
import re

register = template.Library()


@register.simple_tag(takes_context=True)
def get_translated_url(context, lang):
    """
    Generate a translated URL for the given language.
    
    This template tag:
    1. Resolves the current request URL to get the view name and kwargs
    2. Swaps category slugs with their translated versions
    3. Keeps tag slugs as-is (tags don't have translations)
    4. Uses django.utils.translation.override to translate URL patterns
    5. Preserves all GET parameters
    
    Usage:
        {% get_translated_url 'ar' as ar_url %}
        {% get_translated_url 'en' as en_url %}
    """
    request = context['request']
    path = request.path_info
    query_string = request.GET.urlencode()
    
    try:
        # Remove language prefix from path to get the clean path
        # This is necessary because resolve() needs a path without the i18n prefix
        path_without_lang = re.sub(r'^/(en|ar)(?=/|$)', '', path)
        if not path_without_lang:
            path_without_lang = '/'
        
        # Resolve the clean path to get view name and kwargs
        resolved = resolve(path_without_lang)
        view_name = resolved.namespace + ':' + resolved.url_name if resolved.namespace else resolved.url_name
        kwargs = dict(resolved.kwargs)
        
        # Get context objects if they exist
        category = context.get('category')
        tags = context.get('tags')
        
        # Swap slugs for the target language only for categories
        if category and 'category_slug' in kwargs:
            # Get the translated slug for the category
            if lang == 'ar':
                kwargs['category_slug'] = category.slug_ar if hasattr(category, 'slug_ar') and category.slug_ar else category.slug
            else:
                kwargs['category_slug'] = category.slug_en if hasattr(category, 'slug_en') and category.slug_en else category.slug
        
        # For tags: keep the slug as-is (django-taggit tags don't have language variants)
        if tags and 'tag_slug' in kwargs:
            kwargs['tag_slug'] = tags.slug
        
        # Use translation.override to ensure the URL path patterns are translated
        # e.g., "tag/" becomes "وسم/" when overriding to Arabic
        with override(lang):
            # Reverse the view without language prefix
            new_url = reverse(view_name, kwargs=kwargs)
        
        # Add the language prefix
        new_url = f'/{lang}{new_url}'
        
        # Append query parameters if they exist
        if query_string:
            new_url = f"{new_url}?{query_string}"
        
        return new_url
        
    except Exception as e:
        # Fallback: simple language prefix swap
        try:
            new_path = re.sub(r'^/(en|ar)(?=/|$)', '', path)
            if not new_path or new_path == '/':
                new_path = '/'
            new_url = f'/{lang}{new_path}'
            if query_string:
                return f"{new_url}?{query_string}"
            return new_url
        except:
            # Final fallback
            return path


