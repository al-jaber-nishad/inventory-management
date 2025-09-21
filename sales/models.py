from django.db import models

from accounts.models import LedgerAccount
from authentication.models import Customer
from inventory.models import InventoryTransaction
from product.models import Product
from utils.base_model import BaseModel

# Create your models here.


class Sale(BaseModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        CONFIRMED = 'confirmed', 'Confirmed'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'

    payment_ledger = models.ForeignKey(LedgerAccount, on_delete=models.RESTRICT, null=True, blank=True, related_name='sales_payment')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name='customer_sales')
    invoice_number = models.CharField(max_length=100)
    sale_date = models.DateField()
    due_date = models.DateField(blank=True, null=True)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    due = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    note = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    # is_active = models.BooleanField(default=True)

    unique_fields = ['invoice_number']

    def __str__(self):
        return f"Sale #{self.invoice_number} - {self.customer.name}"

    class Meta:
        ordering = ['-sale_date', '-id']
        verbose_name_plural = 'Sales'


class SaleItem(BaseModel):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sale_items')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Discount percentage (0-100)")
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Calculated discount amount")
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} x {self.unit_price}"

    class Meta:
        verbose_name_plural = 'Sale Items'
