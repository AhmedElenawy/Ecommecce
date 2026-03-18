from django.contrib.postgres.search import TrigramSimilarity
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
import re


def search_helper(queryset, query):
    lang = 'ar' if bool(re.search('[\u0600-\u06FF]', query)) else 'en'
    name_field = f"name_{lang}"
    description_field = f"description_{lang}"
    queryset = queryset.annotate(
            rank=TrigramSimilarity(name_field, query)*3 
            + TrigramSimilarity(description_field, query)

        ).filter(rank__gte=0.3).order_by("-rank", "-id")
    return queryset

def offset_pagination(queryset, page, per_page):
    paginator = Paginator(queryset, per_page)
    try:
        queryset_page = paginator.page(page)
    except PageNotAnInteger:
        queryset_page = paginator.page(1)
        page = 1
    except EmptyPage:
        queryset_page = paginator.page(paginator.num_pages)
        page = paginator.num_pages

    return queryset_page, page