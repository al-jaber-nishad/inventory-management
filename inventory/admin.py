from django.contrib import admin
from django.contrib.auth.models import Group

from .models import *


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
	list_display = [field.name for field in InventoryTransaction._meta.fields]


@admin.register(InventoryAdjustment)
class InventoryAdjustmentAdmin(admin.ModelAdmin):
	list_display = [field.name for field in InventoryAdjustment._meta.fields]

