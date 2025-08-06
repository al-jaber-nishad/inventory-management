from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.db.models.fields.related import ForeignKey
from utils.base_model import BaseModel



class Unit(BaseModel):
	name = models.CharField(max_length=255)

	def __str__(self):
		return self.name

class Brand(BaseModel):
	name = models.CharField(max_length=255)
	image = models.ImageField(upload_to='brand/', null=True, blank=True)

	def __str__(self):
		return self.name

class ProductCategory(BaseModel):
	name = models.CharField(max_length=255)
	description = models.TextField(blank=True, null=True)
	image = models.ImageField(upload_to="category/", blank=True, null=True)
	parent = ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

	is_active = models.BooleanField(default=True)

	def __str__(self):
		return self.name

	class Meta:
		ordering = ['-id',]
		verbose_name_plural = 'Categories'

class Product(BaseModel):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=64, unique=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name='products', null=True, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name='products', null=True, blank=True)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name='products', null=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    slug = models.SlugField(max_length=280, unique=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
        ]

    def save(self, *args, **kwargs):
        # slugify from name if missing
        if not self.slug:
            base = slugify(self.name)
            slug_candidate = base
            counter = 1
            while Product.objects.filter(slug=slug_candidate).exclude(pk=self.pk).exists():
                slug_candidate = f"{base}-{counter}"
                counter += 1
            self.slug = slug_candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.sku})"
