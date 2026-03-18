from ecommerce.redis_client import r
from .models import Product
import uuid



class recommendation:

    def get_list_key(self, product_id):
        return f"recommendation_for:{product_id}"
    
    def bought_together(self, products):
        ids_list = [p.id for p in products]

        pipe = r.pipeline()

        for id in ids_list:
            for with_id in ids_list:
                if id != with_id:
                    r.zincrby(self.get_list_key(id), 1, str(with_id))

        pipe.execute()


    def recommendations_for(self, products, max_results=4):
        ids_list = [p.id for p in products]
        if not ids_list:
            return []
        if len(ids_list) == 1:
            recommendation_ids_str = r.zrange(self.get_list_key(ids_list[0]), 0, -1, desc=True)[:max_results]
        else:
            unique_suffix = uuid.uuid4().hex
            temp_key = f"temp_key:{unique_suffix}"
            keys = [self.get_list_key(id) for id in ids_list]
            try:
                r.zunionstore(temp_key, keys)
                r.zrem(temp_key, *ids_list)
                recommendation_ids_str = r.zrange(temp_key, 0, -1, desc=True)[:max_results]
            finally:
                r.delete(temp_key)

        recommendation_ids = [int(id) for id in recommendation_ids_str]
        recommended_products = list(Product.active.prefetch_related('images').filter(id__in= recommendation_ids))
        hash_map = {pid:id for id, pid in enumerate(recommendation_ids)}
        recommended_products.sort(key= lambda x : hash_map[x.id])
        return recommended_products