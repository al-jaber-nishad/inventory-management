from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from accounts.models import AccountLog, LedgerAccount, SubLedgerAccount
from inventory.models import InventoryTransaction
from sales.models import Sale, SaleItem
from django.utils.timezone import now

@receiver(post_save, sender=Sale)
def create_or_update_account_logs_for_sale(sender, instance, created, **kwargs):
    customer_ledger = LedgerAccount.objects.filter(reference_id=instance.customer.id).first()
    payment_ledger = instance.payment_ledger
    reference_no = instance.invoice_number
    total = instance.total
    paid = instance.paid
    sub_ledger, _ = SubLedgerAccount.objects.get_or_create(name='Sale')

    # Handle Customer Ledger (DEBIT)
    customer_log, _ = AccountLog.objects.update_or_create(
        reference_no=reference_no,
        log_type='sale_customer',
        ledger=customer_ledger,
        defaults={
            'date': now(),
            'sub_ledger': sub_ledger,
            'debit_amount': 0,
            'credit_amount': total,
            'details': f'Sale to customer: {customer_ledger.name}',
        }
    )

    # Handle Payment Ledger (CREDIT)
    if paid > 0 and payment_ledger:
        payment_log, _ = AccountLog.objects.update_or_create(
            reference_no=reference_no,
            log_type='sale_payment',
            ledger=payment_ledger,
            defaults={
                'date': now(),
                'sub_ledger': sub_ledger,
                'debit_amount': paid,
                'credit_amount': 0,
                'details': f'Payment received for sale: {customer_ledger.name}',
            }
        )
    else:
        # If no payment or ledger, remove any old payment logs
        AccountLog.objects.filter(reference_no=reference_no, log_type='sale_payment').delete()


@receiver(post_delete, sender=Sale)
def delete_account_log_of_sale(sender, instance, **kwargs):
    AccountLog.objects.filter(reference_id=instance.invoice_number, log_type='sale_payment').delete()



@receiver(post_save, sender=SaleItem)
def create_inventory_transaction(sender, instance, **kwargs):
    sale = instance.sale
    product = instance.product
    reference_code = sale.invoice_number
    quantity = instance.quantity

    # Handle inventory return (stock going OUT of warehouse)
    InventoryTransaction.objects.update_or_create(
        product=product,
        transaction_type=InventoryTransaction.TransactionType.SALE,
        reference_code=reference_code,
        defaults={
            'quantity': -abs(quantity),  # Negative quantity = stock out
            'date': now(),
            'note': f"Sold to customer via sales #{reference_code}",
        }
    )


@receiver(post_delete, sender=SaleItem)
def delete_inventory_transaction_on_sale_delete(sender, instance, **kwargs):
    InventoryTransaction.objects.filter(
        product=instance.product,
        transaction_type=InventoryTransaction.TransactionType.SALE,
        reference_code=instance.sale.invoice_number
    ).delete()
