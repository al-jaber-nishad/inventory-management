from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import AccountLog
from accounts.models import PaymentVoucher
from django.utils.timezone import now

@receiver(post_save, sender=PaymentVoucher)
def create_or_update_account_logs_for_sale(sender, instance, created, **kwargs):
    expense_ledger = instance.expense_ledger
    payment_ledger = instance.payment_ledger
    reference_no = instance.invoice_no
    amount = instance.amount
    sub_ledger = instance.sub_ledger

    # Handle Customer Ledger (DEBIT)
    customer_log, _ = AccountLog.objects.update_or_create(
        reference_no=reference_no,
        log_type='payment_voucher',
        ledger=expense_ledger,
        defaults={
            'date': now(),
            'sub_ledger': sub_ledger,
            'debit_amount': amount,
            'credit_amount': 0,
            'details': f'Payment Voucher for: {expense_ledger.name}',
        }
    )
    # Handle Payment Ledger (CREDIT)
    payment_log, _ = AccountLog.objects.update_or_create(
        reference_no=reference_no,
        log_type='payment_voucher',
        ledger=payment_ledger,
        defaults={
            'date': now(),
            'sub_ledger': sub_ledger,
            'debit_amount': 0,
            'credit_amount': amount,
            'details': f'Payment Voucher for: {expense_ledger.name}',
        }
    )

    # Handle delete functionality
    if instance.deleted_at:
        AccountLog.objects.filter(reference_no=instance.invoice_no, log_type='payment_voucher').delete()

