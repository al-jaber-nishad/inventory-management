from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from accounts.models import AccountLog, LedgerAccount, SubLedgerAccount
from inventory.models import InventoryTransaction
from purchase_return.models import PurchaseReturn, PurchaseReturnItem
from django.utils.timezone import now

@receiver(post_save, sender=PurchaseReturn)
def create_or_update_account_logs_for_purchase_return(sender, instance, created, **kwargs):
    supplier_ledger = LedgerAccount.objects.filter(reference_id=instance.supplier.id).first()
    payment_ledger = instance.payment_ledger
    reference_no = instance.return_number
    total = instance.total
    refunded = instance.refunded
    sub_ledger, _ = SubLedgerAccount.objects.get_or_create(name='Purchase Return')

    # Handle Supplier Ledger (CREDIT - reducing supplier debt)
    supplier_log, _ = AccountLog.objects.update_or_create(
        reference_no=reference_no,
        log_type='purchase_return_supplier',
        ledger=supplier_ledger,
        defaults={
            'date': now(),
            'sub_ledger': sub_ledger,
            'debit_amount': 0,
            'credit_amount': total,
            'details': f'Purchase return to supplier: {supplier_ledger.name}',
        }
    )

    # Handle Payment Ledger (DEBIT - money going out as refund)
    if refunded > 0 and payment_ledger:
        payment_log, _ = AccountLog.objects.update_or_create(
            reference_no=reference_no,
            log_type='purchase_return_payment',
            ledger=payment_ledger,
            defaults={
                'date': now(),
                'sub_ledger': sub_ledger,
                'debit_amount': refunded,
                'credit_amount': 0,
                'details': f'Refund processed for return: {supplier_ledger.name}',
            }
        )
    else:
        # If no refund or ledger, remove any old payment logs
        AccountLog.objects.filter(reference_no=reference_no, log_type='purchase_return_payment').delete()


@receiver(post_delete, sender=PurchaseReturn)
def delete_account_log_of_purchase_return(sender, instance, **kwargs):
    AccountLog.objects.filter(reference_no=instance.return_number, log_type__in=['purchase_return_supplier', 'purchase_return_payment']).delete()


@receiver(post_save, sender=PurchaseReturnItem)
def create_inventory_transaction(sender, instance, **kwargs):
    purchase_return = instance.purchase_return
    product = instance.product
    reference_code = purchase_return.return_number
    quantity = instance.quantity

    # Handle inventory return (stock going OUT of warehouse)
    InventoryTransaction.objects.update_or_create(
        product=product,
        transaction_type=InventoryTransaction.TransactionType.PURCHASE_RETURN,
        reference_code=reference_code,
        defaults={
            'quantity': -abs(quantity),  # Negative quantity = stock out
            'date': now(),
            'details': f"Returned to supplier via purchase return #{reference_code}",
        }
    )


@receiver(post_delete, sender=PurchaseReturnItem)
def delete_inventory_transaction_on_return_delete(sender, instance, **kwargs):
    InventoryTransaction.objects.filter(
        product=instance.product,
        warehouse=instance.purchase_return.warehouse,
        transaction_type=InventoryTransaction.TransactionType.PURCHASE_RETURN,
        reference_code=instance.purchase_return.return_number
    ).delete()
