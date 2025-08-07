from django.contrib import admin
from .models import PurchaseReturn, PurchaseReturnItem


class PurchaseReturnItemInline(admin.TabularInline):
    model = PurchaseReturnItem
    extra = 0


@admin.register(PurchaseReturn)
class PurchaseReturnAdmin(admin.ModelAdmin):
    list_display = ('return_number', 'supplier', 'return_date', 'total', 'status', 'created_at')
    list_filter = ('status', 'return_date', 'created_at')
    search_fields = ('return_number', 'supplier__name')
    inlines = [PurchaseReturnItemInline]
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')


@admin.register(PurchaseReturnItem)
class PurchaseReturnItemAdmin(admin.ModelAdmin):
    list_display = ('purchase_return', 'product', 'quantity', 'unit_price', 'total_price')
    list_filter = ('purchase_return__status', 'created_at')
    search_fields = ('product__name', 'purchase_return__return_number')