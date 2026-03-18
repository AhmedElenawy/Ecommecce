import base64
from django.db.models import Q
from datetime import datetime
def encode_cursor(first_indecator, second_indecator):
    if not first_indecator or not second_indecator:
        return None
    payload = f"{first_indecator}|{second_indecator}"
    return base64.b64encode(payload.encode('utf-8')).decode('utf-8')

def decode_cursor(cursor):

    try:
        payload = base64.b64decode(cursor.encode('utf-8')).decode('utf-8')
        first_indecator, second_indecator = payload.split("|")
    except:
        return None, None
    
    return first_indecator, second_indecator
# need to int id

def cursor_pagination(queryset,  last_cursor, query_per_page=4, first_indecator_type='created', second_indecator_type='id'):
    if last_cursor:
        first_indecator, second_indecator = decode_cursor(last_cursor)

        if first_indecator and second_indecator:
            if first_indecator_type == 'created' and second_indecator_type == 'id':
                first_indecator = datetime.fromisoformat(first_indecator)
                second_indecator= int(second_indecator)
                paginated_queryset = queryset.filter(Q(created__lt=first_indecator) | Q(created=first_indecator, id__lt=second_indecator))
            elif first_indecator_type == 'rank' and second_indecator_type == 'id':
                first_indecator = float(first_indecator)
                second_indecator= int(second_indecator)
                paginated_queryset = queryset.filter(Q(rank__lt=first_indecator) | Q(rank=first_indecator, id__lt=second_indecator))
            
        else:
            # no cursor render frist page
            paginated_queryset = queryset

    else:

        # if there is no cursor
        # frist page
        paginated_queryset = queryset

    paginated_queryset = list(paginated_queryset[:query_per_page +1])
    l = len(paginated_queryset) if paginated_queryset else 0
    if l < query_per_page+1:
        has_next = False
        last_cursor = None
    else:
        has_next = True
        paginated_queryset = paginated_queryset[:query_per_page]
        if first_indecator_type == 'created' and second_indecator_type == 'id':
            last_cursor = encode_cursor(paginated_queryset[-1].created, paginated_queryset[-1].id)
        elif first_indecator_type == 'rank' and second_indecator_type == 'id':
            last_cursor = encode_cursor(paginated_queryset[-1].rank, paginated_queryset[-1].id)


    return paginated_queryset, last_cursor, has_next
