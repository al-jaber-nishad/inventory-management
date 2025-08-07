from django.db import models

from accounts.models import LedgerAccount
from authentication.models import Customer
from product.models import Product
from sales.models import Sale, SaleItem
from utils.base_model import BaseModel


class SaleReturn(BaseModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        CONFIRMED = 'confirmed', 'Confirmed'
        PROCESSED = 'processed', 'Processed'
        CANCELLED = 'cancelled', 'Cancelled'

    payment_ledger = models.ForeignKey(LedgerAccount, on_delete=models.RESTRICT, null=True, blank=True, related_name='sale_returns_payment')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name='customer_sale_returns')
    original_sale = models.ForeignKey(Sale, on_delete=models.PROTECT, null=True, blank=True, related_name='returns')
    return_number = models.CharField(max_length=100)
    return_date = models.DateField()
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    refunded = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    due = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    reason = models.TextField(blank=True, null=True, help_text="Reason for return")
    note = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    is_active = models.BooleanField(default=True)

    unique_fields = ['return_number']

    def __str__(self):
        return f"Return #{self.return_number} - {self.customer.name}"

    class Meta:
        ordering = ['-return_date', '-id']
        verbose_name_plural = 'Sale Returns'


class SaleReturnItem(BaseModel):
    sale_return = models.ForeignKey(SaleReturn, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sale_return_items')
    original_sale_item = models.ForeignKey(SaleItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='return_items')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} x {self.unit_price}"

    class Meta:
        verbose_name_plural = 'Sale Return Items'