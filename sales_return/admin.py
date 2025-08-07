from django.contrib import admin
from .models import SaleReturn, SaleReturnItem

class SaleReturnItemInline(admin.TabularInline):
    model = SaleReturnItem
    extra = 0

@admin.register(SaleReturn)
class SaleReturnAdmin(admin.ModelAdmin):
    list_display = ['return_number', 'customer', 'return_date', 'total', 'status']
    list_filter = ['status', 'return_date']
    search_fields = ['return_number', 'customer__name']
    inlines = [SaleReturnItemInline]
    readonly_fields = ['subtotal', 'total']
    
    fieldsets = (
        (None, {
            'fields': ('return_number', 'customer', 'original_sale', 'return_date')
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'discount', 'tax', 'total', 'refunded', 'due', 'payment_ledger')
        }),
        ('Additional Information', {
            'fields': ('reason', 'note', 'status', 'is_active')
        }),
    )

@admin.register(SaleReturnItem)
class SaleReturnItemAdmin(admin.ModelAdmin):
    list_display = ['sale_return', 'product', 'quantity', 'unit_price', 'total_price']
    list_filter = ['sale_return__return_date']
    search_fields = ['product__name', 'sale_return__return_number']