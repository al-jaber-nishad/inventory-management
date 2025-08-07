from django.db.models import Sum
from inventory.models import InventoryTransaction



def get_current_stock(product_id):
    transactions = InventoryTransaction.objects.filter(product_id=product_id)

    additions = transactions.filter(transaction_type__in=[
        InventoryTransaction.TransactionType.PURCHASE,
        InventoryTransaction.TransactionType.SALE_RETURN,
        InventoryTransaction.TransactionType.TRANSFER_IN
    ]).aggregate(total=Sum('quantity'))['total'] or 0

    subtractions = transactions.filter(transaction_type__in=[
        InventoryTransaction.TransactionType.SALE,
        InventoryTransaction.TransactionType.PURCHASE_RETURN,
        InventoryTransaction.TransactionType.TRANSFER_OUT
    ]).aggregate(total=Sum('quantity'))['total'] or 0

    return additions - subtractions
