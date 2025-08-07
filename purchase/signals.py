from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from accounts.models import AccountLog, LedgerAccount, SubLedgerAccount
from purchase.models import Purchase
from django.utils.timezone import now

@receiver(post_save, sender=Purchase)
def create_or_update_account_logs_for_purchase(sender, instance, created, **kwargs):
    supplier_ledger = instance.supplier
    payment_ledger = instance.payment_ledger
    reference_no = instance.invoice_number
    total = instance.total
    paid = instance.paid
    sub_ledger, _ = SubLedgerAccount.objects.get_or_create(name='Purchase')

    # Handle Supplier Ledger (DEBIT)
    supplier_log, _ = AccountLog.objects.update_or_create(
        reference_no=reference_no,
        log_type='purchase_supplier',
        ledger=supplier_ledger,
        defaults={
            'date': now(),
            'sub_ledger': sub_ledger,
            'debit_amount': total,
            'credit_amount': 0,
            'details': f'Purchase from supplier: {supplier_ledger.name}',
        }
    )

    # Handle Payment Ledger (CREDIT)
    if paid > 0 and payment_ledger:
        payment_log, _ = AccountLog.objects.update_or_create(
            reference_no=reference_no,
            log_type='purchase_payment',
            ledger=payment_ledger,
            defaults={
                'date': now(),
                'sub_ledger': sub_ledger,
                'debit_amount': 0,
                'credit_amount': paid,
                'details': f'Payment made for purchase: {supplier_ledger.name}',
            }
        )
    else:
        # If no payment or ledger, remove any old payment logs
        AccountLog.objects.filter(reference_no=reference_no, log_type='purchase_payment').delete()


@receiver(post_delete, sender=Purchase)
def delete_account_log_of_purchase(sender, instance, **kwargs):
    AccountLog.objects.filter(reference_id=instance.invoice_number, log_type='purchase_payment').delete()
