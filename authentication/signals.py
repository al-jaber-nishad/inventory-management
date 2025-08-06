from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from authentication.models import Customer, Supplier
from accounts.models import LedgerAccount, Group


# ---------- Customer Signals ----------

@receiver(post_save, sender=Customer)
def create_or_update_ledger_for_customer(sender, instance, created, **kwargs):
    ledger, _ = LedgerAccount.objects.get_or_create(
        reference_id=str(instance.id),
        ledger_type='customer',
        defaults={
            'name': instance.name,
            'details': f"Auto-created ledger for customer: {instance.name}",
            'head_group': Group.objects.filter(name__iexact='Customer').first(),
            'is_deletable': True,
            'is_default': False
        }
    )
    if not created:
        ledger.name = instance.name
        ledger.details = f"Auto-updated ledger for customer: {instance.name}"
        ledger.save()


@receiver(post_delete, sender=Customer)
def delete_ledger_for_customer(sender, instance, **kwargs):
    LedgerAccount.objects.filter(reference_id=str(instance.id), ledger_type='customer').delete()


# ---------- Supplier Signals ----------

@receiver(post_save, sender=Supplier)
def create_or_update_ledger_for_supplier(sender, instance, created, **kwargs):
    ledger, _ = LedgerAccount.objects.get_or_create(
        reference_id=str(instance.id),
        ledger_type='supplier',
        defaults={
            'name': instance.name,
            'details': f"Auto-created ledger for supplier: {instance.name}",
            'head_group': Group.objects.filter(name__iexact='Supplier').first(),
            'is_deletable': True,
            'is_default': False
        }
    )
    if not created:
        ledger.name = instance.name
        ledger.details = f"Auto-updated ledger for supplier: {instance.name}"
        ledger.save()


@receiver(post_delete, sender=Supplier)
def delete_ledger_for_supplier(sender, instance, **kwargs):
    LedgerAccount.objects.filter(reference_id=str(instance.id), ledger_type='supplier').delete()