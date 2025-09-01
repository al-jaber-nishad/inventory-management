from django.contrib import admin
from django.contrib.auth.models import Group

from .models import *


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
	list_display = [field.name for field in Sale._meta.fields]



@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
	list_display = [field.name for field in SaleItem._meta.fields]

