from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from .models import InventoryAdjustment, InventoryTransaction


@receiver(post_save, sender=InventoryAdjustment)
def create_inventory_transaction(sender, instance, created, **kwargs):
    """
    Creates or updates the corresponding InventoryTransaction
    whenever an InventoryAdjustment is created or updated.
    """

    # Calculate quantity change (positive or negative based on type)
    quantity_change = instance.quantity if instance.adjustment_type == InventoryAdjustment.AdjustmentType.INCREASE else -instance.quantity

    # Create or update the transaction
    transaction, _ = InventoryTransaction.objects.update_or_create(
        reference_code=instance.id,
        transaction_type=InventoryTransaction.TransactionType.ADJUSTMENT,
        product=instance.product,
        defaults={
            "quantity": quantity_change,
            "note": f"Stock Adjustment: {instance.reason}",
            "created_by": getattr(instance, "created_by", None),  # optional
            "date": instance.date or now(),
        }
    )

    # Store link back to transaction if you have a FK field (optional)
    if hasattr(instance, "inventory_transaction") and instance.inventory_transaction != transaction:
        instance.inventory_transaction = transaction
        instance.save(update_fields=["inventory_transaction"])

    
    # Delete the related inventorytransactions
    if instance.deleted_at:
        # fallback: delete by reference number
        InventoryTransaction.objects.filter(
            reference_code=instance.id,
            transaction_type=InventoryTransaction.TransactionType.ADJUSTMENT
        ).delete()
