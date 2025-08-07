from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from accounts.models import AccountLog, LedgerAccount, SubLedgerAccount
from inventory.models import InventoryTransaction
from sales_return.models import SaleReturn, SaleReturnItem
from django.utils.timezone import now

@receiver(post_save, sender=SaleReturn)
def create_or_update_account_logs_for_sale_return(sender, instance, created, **kwargs):
    customer_ledger = LedgerAccount.objects.filter(reference_id=instance.customer.id).first()
    payment_ledger = instance.payment_ledger
    reference_no = instance.return_number
    total = instance.total
    refunded = instance.refunded
    sub_ledger, _ = SubLedgerAccount.objects.get_or_create(name='Sale Return')

    # Handle Customer Ledger (CREDIT - reverse of sale)
    customer_log, _ = AccountLog.objects.update_or_create(
        reference_no=reference_no,
        log_type='sale_return_customer',
        ledger=customer_ledger,
        defaults={
            'date': now(),
            'sub_ledger': sub_ledger,
            'debit_amount': total,
            'credit_amount': 0,
            'details': f'Sale return from customer: {customer_ledger.name}',
        }
    )

    # Handle Payment Ledger (DEBIT - cash/bank out for refund)
    if refunded > 0 and payment_ledger:
        payment_log, _ = AccountLog.objects.update_or_create(
            reference_no=reference_no,
            log_type='sale_return_payment',
            ledger=payment_ledger,
            defaults={
                'date': now(),
                'sub_ledger': sub_ledger,
                'debit_amount': 0,
                'credit_amount': refunded,
                'details': f'Refund made for sale return: {customer_ledger.name}',
            }
        )
    else:
        # If no refund or ledger, remove any old payment logs
        AccountLog.objects.filter(reference_no=reference_no, log_type='sale_return_payment').delete()


@receiver(post_delete, sender=SaleReturn)
def delete_account_log_of_sale_return(sender, instance, **kwargs):
    AccountLog.objects.filter(reference_id=instance.return_number, log_type='sale_return_payment').delete()




@receiver(post_save, sender=SaleReturnItem)
def create_inventory_transaction(sender, instance, **kwargs):
    sale_return = instance.sale_return
    product = instance.product
    reference_code = sale_return.return_number
    quantity = instance.quantity

    # Handle inventory return (stock going OUT of warehouse)
    InventoryTransaction.objects.update_or_create(
        product=product,
        transaction_type=InventoryTransaction.TransactionType.SALE_RETURN,
        reference_code=reference_code,
        defaults={
            'quantity': abs(quantity),  # Negative quantity = stock out
            'date': now(),
            'note': f"Returned to supplier via sale return #{reference_code}",
        }
    )


@receiver(post_delete, sender=SaleReturnItem)
def delete_inventory_transaction_on_return_delete(sender, instance, **kwargs):
    InventoryTransaction.objects.filter(
        product=instance.product,
        warehouse=instance.sale_return.warehouse,
        transaction_type=InventoryTransaction.TransactionType.SALE_RETURN,
        reference_code=instance.sale_return.return_number
    ).delete()
