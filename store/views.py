from django.shortcuts import get_object_or_404, render, redirect
from django.http import Http404

from .cursor_pagination import cursor_pagination
from django.contrib.postgres.aggregates import ArrayAgg

from .models import Category, Product
from .recommendation import recommendation
from taggit.models import Tag, TaggedItem
from .search import search_helper
from .filters import ProductFilter



def product_list_tags(request):
    
    categories = Category.objects.all()
    
    tags = Product.tags.most_common().annotate(
        product_id_list = ArrayAgg('taggit_taggeditem_items__object_id')
    )
    all_top4_ids = set()
    for tag in tags:
        tag.product_id_list = tag.product_id_list[:10]
        all_top4_ids.update(tag.product_id_list)

    all_products = Product.active_base.prefetch_related('images').in_bulk(list(all_top4_ids))
    tag_list = []
    for tag in tags:
        tag.products = [all_products[pid] for pid in tag.product_id_list if pid in all_products]
        if tag.products:
            tag_list.append(tag)

    return render(request, "store/category_list.html", {"category_list": categories, "tags": tag_list})



def search(request):
    query = request.GET.get('query', '')[:100]
    if not query:
        return redirect('store:product_list')
    
    # try:
    #     page = int(request.GET.get('page', 1))
    # except (ValueError, TypeError):
    #     page = 1

    last_cursor = request.GET.get('cursor', None)
    list_only = str(request.GET.get('list_only', '')).lower() == 'true'
    product_per_page = 8

    product_list = Product.active_base.all().prefetch_related('images')
    # search_query = SearchQuery(query)
    # search_vector = SearchVector("name", weight="A") + SearchVector("description", weight="B")
    
    new_product_list = search_helper(product_list, query) 
    product_filter = ProductFilter(request.GET, queryset=new_product_list)
    # products_page, page= offset_pagination(new_product_list, page, product_per_page)
    products, last_cursor, has_next = cursor_pagination(product_filter.qs, last_cursor, product_per_page, "rank")

    if list_only:
        return render(request, "store/product_list_only.html", 
                      {"products": products,
                        "query": query,
                        "has_next": has_next,
                        "last_cursor": last_cursor,
                        "filter": product_filter
                    })

    return render(request, "store/product_list.html", 
                  {"products": products,
                    "query": query,
                    "has_next": has_next,
                    "last_cursor": last_cursor,
                    "filter": product_filter
                })


def product_list(request, category_slug=None, tag_slug=None):
    # intialize
    
    category = None
    tags = None

    list_only = str(request.GET.get('list_only', '')).lower() == 'true'
    last_cursor = request.GET.get('cursor', None)
    
    product_per_page = 8
    
    # quering database
    product_list = Product.active_base.all().order_by('-created', '-id').prefetch_related('images')
    
    # Apply ProductFilter which handles category and tags from query parameters
    product_filter = ProductFilter(request.GET, queryset=product_list)
    products, last_cursor, has_next = cursor_pagination(product_filter.qs, last_cursor, product_per_page)

    if list_only:
        return render(request, "store/product_list_only.html", 
                      {"products": products,
                        "category": category,
                        "tags": tags,
                        "has_next": has_next,
                        "last_cursor": last_cursor,
                        "filter": product_filter
                    })

    return render(request, "store/product_list.html", 
                  {"products": products,
                   "category": category,
                   "tags": tags,
                    "has_next": has_next,
                    "last_cursor": last_cursor,
                    "filter": product_filter
                })


    
# product/category_slug/product_slug
def product_detail(request, product_id):
    product = get_object_or_404(Product.active.select_related('variant_group').prefetch_related('images'), id=product_id)

    r = recommendation()
    similarproduct = r.recommendations_for([product], 4)
    return render(request, "store/product_detail.html", {"product": product, "similarproduct": similarproduct})