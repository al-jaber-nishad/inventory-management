from django.contrib import admin
from django.contrib.auth.models import Group

from .models import *


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
	list_display = [field.name for field in Purchase._meta.fields]



@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
	list_display = [field.name for field in PurchaseItem._meta.fields]

