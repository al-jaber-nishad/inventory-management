from django.db import models
# from product.models import Product
from django.utils import timezone
from utils.base_model import BaseModel
# Create your models here.


class InventoryTransaction(BaseModel):
    class TransactionType(models.TextChoices):
        PURCHASE = 'purchase', 'Purchase'
        SALE = 'sale', 'Sale'
        PURCHASE_RETURN = 'purchase_return', 'Purchase Return'
        SALE_RETURN = 'sale_return', 'Sale Return'
        ADJUSTMENT = 'adjustment', 'Stock Adjustment'
        TRANSFER_IN = 'transfer_in', 'Transfer In'
        TRANSFER_OUT = 'transfer_out', 'Transfer Out'
        INITIAL_STOCK = 'initial_stock', 'Initial Stock'

    date = models.DateTimeField(default=timezone.now)
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)

    # TODO tract previous and present stock quantity
    quantity = models.IntegerField()
    note = models.TextField(blank=True, null=True)
    reference_code = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.transaction_type} | {self.product.name} | {self.quantity}"



class InventoryAdjustment(BaseModel):
    class AdjustmentType(models.TextChoices):
        INCREASE = "increase", "Increase"
        DECREASE = "decrease", "Decrease"

    product = models.ForeignKey(
        'product.Product',
        on_delete=models.CASCADE,
        related_name='inventory_adjustments'
    )
    adjustment_type = models.CharField(max_length=10, choices=AdjustmentType.choices)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255, blank=True, help_text="Reason for adjustment (e.g., Damaged, Stock count correction, Lost, Extra stock found)")
    date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.product} - {self.adjustment_type} ({self.quantity}) on {self.date.date()}"