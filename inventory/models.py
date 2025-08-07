from django.db import models
# from product.models import Product
from django.utils import timezone

# Create your models here.


class InventoryTransaction(models.Model):
    class TransactionType(models.TextChoices):
        PURCHASE = 'purchase', 'Purchase'
        SALE = 'sale', 'Sale'
        PURCHASE_RETURN = 'purchase_return', 'Purchase Return'
        SALE_RETURN = 'sale_return', 'Sale Return'
        ADJUSTMENT = 'adjustment', 'Stock Adjustment'
        TRANSFER_IN = 'transfer_in', 'Transfer In'
        TRANSFER_OUT = 'transfer_out', 'Transfer Out'

    date = models.DateTimeField(default=timezone.now)
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    quantity = models.IntegerField()
    note = models.TextField(blank=True, null=True)
    reference_code = models.CharField(max_length=100, blank=True, null=True)
    created_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.transaction_type} | {self.product.name} | {self.quantity}"
