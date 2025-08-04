from django.contrib import admin
from django.contrib.auth.models import Group

from .models import *


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = [field.name for field in Product._meta.fields]


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
	list_display = [field.name for field in ProductCategory._meta.fields]


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
	list_display = [field.name for field in Brand._meta.fields]

