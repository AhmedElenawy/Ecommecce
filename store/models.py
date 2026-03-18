from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from taggit.managers import TaggableManager
from django.contrib.postgres.indexes import GinIndex
from django.utils.translation import gettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator
from decimal import Decimal
from django.utils import timezone
from django.http import JsonResponse

class Discount(models.Model):
    discount = models.IntegerField(_('discount'), validators=[MinValueValidator(0), MaxValueValidator(100)])
    valid_from = models.DateTimeField(_('valid from'))
    valid_to = models.DateTimeField(_('valid to'))
    active = models.BooleanField(_('active'))

    def is_valid(self):
        now = timezone.now()
        if now < self.valid_from or now > self.valid_to or not self.active:
            return False
        return True         
    
    def __str__(self):
        return f"{self.discount}% from {self.valid_from} to {self.valid_to}"
    class Meta:
        verbose_name = _('discount')
        verbose_name_plural = _('discounts')


class Category(models.Model):
    name = models.CharField(_('name'), max_length=250)
    slug = models.SlugField(_('slug'), max_length=250, unique=True, allow_unicode=True)
    image = models.ImageField(_('image'), upload_to='category_images/', blank=True, null=True)


    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
    def save(self, *args, **kwargs):
        if not self.slug_ar and self.name_ar:
            self.slug_ar = slugify(self.name_ar, allow_unicode=True)
    
        if not self.slug_en and self.name_en:
            self.slug_en = slugify(self.name_en)
            
        super().save(*args, **kwargs)

class ProductVariantGroup(models.Model):
    name = models.CharField(_('name'), max_length=250)

    def __str__(self):
        return self.name

    def get_all_variant_products(self):
        return self.variants.filter(is_active=True).select_related('discount')

    def get_base_variant(self):
        return self.variants.filter(is_base_variant=True, is_active=True).first()

    def get_all_specifications_dict(self):
        variants = self.get_all_variant_products()
        specs = {}
        for variant in variants:
            for key, value in variant.variant_specifications.items():
                specs.setdefault(key, set()).add(value)
        specs = {key: list(values) for key, values in specs.items()}
        return specs
    
    def get_product_url(self, specs):
        if specs and isinstance(specs, dict):
            variant = self.get_all_variant_products().filter(variant_specifications__contains=specs).first()
            if variant.exists():
                return variant.get_absolute_url()
        return None

    def get_total_sales(self):
        return sum(variant.sales for variant in self.get_all_variant_products())

    class Meta:
        verbose_name = _('product variant group')
        verbose_name_plural = _('product variant groups')


class Product(models.Model):

    # 1. Create a BaseManager that applies select_related
    class BaseManager(models.Manager):
        def get_queryset(self):
            return super().get_queryset().select_related('discount')

    # 2. Inherit from BaseManager instead of models.Manager
    class ActiveManager(BaseManager):
        def get_queryset(self):
            return super().get_queryset().filter(is_active=True)

    class ActiveBaseManager(BaseManager):
        def get_queryset(self):
            return super().get_queryset().filter(is_base_variant=True, is_active=True)


    variant_group = models.ForeignKey(ProductVariantGroup, on_delete=models.SET_NULL, related_name="variants", null=True)
    is_base_variant = models.BooleanField(_('base variant'), default=True)
    variant_specifications = models.JSONField(_('variant specifications'), blank=True, null=True)

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name="products", null=True, blank=True)
    tags = TaggableManager()

    name = models.CharField(_('name'), max_length=250)
    slug = models.SlugField(_('slug'), max_length=250, unique=True, allow_unicode=True)
    description = models.TextField(_('description'))
    
    base_price = models.DecimalField(_('price'), decimal_places=2, max_digits=10)
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, null=True, blank=True)

    stock = models.PositiveIntegerField(_('stock'))
    sales = models.PositiveIntegerField(_('sales'), default=0)
    is_active = models.BooleanField(_('active'), default=True)

    # config setting and urls
    image = models.ImageField(_('image'), upload_to='product_images/')
    
    created = models.DateTimeField(_('created'), auto_now_add=True)
    updated = models.DateTimeField(_('updated'), auto_now=True)


    objects = models.Manager() # The default manager.
    active = ActiveManager()
    active_base = ActiveBaseManager()


    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug_ar and self.name_ar:
            self.slug_ar = slugify(self.name_ar, allow_unicode=True)
    
        if not self.slug_en and self.name_en:
            self.slug_en = slugify(self.name_en)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:product_detail', args=[self.id])

    @property
    def discount_percent(self):
        if self.discount and self.discount.is_valid():
            return self.discount.discount
        return 0
    
    @property
    def price(self):
        if self.discount and self.discount.is_valid():
            price = self.base_price * (1 - (self.discount.discount / Decimal(100)))
            return price.quantize(Decimal('0.01'))
        return self.base_price.quantize(Decimal('0.01'))

    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')
        # ordering = ["-created"]
        indexes = [
            models.Index(fields=['-created']),
            models.Index(fields=['is_active']),

            # FIX: Add 'opclasses' here. 
            # You must provide one opclass for EACH field in the index.
            
 
            GinIndex(
                name='prod_name_ar_gin', 
                fields=['name_ar'], 
                opclasses=['gin_trgm_ops']
            ),
            GinIndex(
                name='prod_desc_ar_gin', 
                fields=['description_ar'], 
                opclasses=['gin_trgm_ops']
            ),

            # --- ENGLISH INDEXES ---
            GinIndex(
                name='prod_name_en_gin', 
                fields=['name_en'], 
                opclasses=['gin_trgm_ops']
            ),
            GinIndex(
                name='prod_desc_en_gin', 
                fields=['description_en'], 
                opclasses=['gin_trgm_ops']
            ),


        ]


class Images(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(_('image'), upload_to='product_images/')





