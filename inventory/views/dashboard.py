from django.shortcuts import render
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from authentication.models import Customer, Supplier
from product.models import Product
from sales.models import Sale, SaleItem
from purchase.models import Purchase, PurchaseItem
from inventory.models import InventoryTransaction


def dashboard_view(request):
    """
    Dashboard view with aggregated data for inventory management system
    """
    
    # Get date range for filtering (current month)
    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    
    # Purchase metrics
    purchase_due_total = Purchase.objects.filter(
        status__in=['confirmed', 'received']
    ).aggregate(total_due=Sum('due'))['total_due'] or Decimal('0')
    
    # Sales metrics
    sales_due_total = Sale.objects.filter(
        status__in=['confirmed', 'delivered']
    ).aggregate(total_due=Sum('due'))['total_due'] or Decimal('0')
    
    # Total sales amount (all time)
    total_sales_amount = Sale.objects.filter(
        status__in=['confirmed', 'delivered']
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    # Count metrics
    total_customers = Customer.objects.filter(is_active=True).count()
    total_suppliers = Supplier.objects.filter(is_active=True).count()
    total_purchase_invoices = Purchase.objects.filter(status__in=['confirmed', 'received']).count()
    total_sales_invoices = Sale.objects.filter(status__in=['confirmed', 'delivered']).count()
    
    # Recently added products (last 10)
    recent_products = Product.objects.filter(is_active=True).order_by('-created_at')[:10]
    
    # Chart data - Monthly sales and purchase data for current year
    current_year = today.year
    monthly_data = []
    
    for month in range(1, 13):
        month_start = datetime(current_year, month, 1).date()
        if month == 12:
            month_end = datetime(current_year + 1, 1, 1).date()
        else:
            month_end = datetime(current_year, month + 1, 1).date()
        
        # Monthly sales
        monthly_sales = Sale.objects.filter(
            sale_date__gte=month_start,
            sale_date__lt=month_end,
            status__in=['confirmed', 'delivered']
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        # Monthly purchases
        monthly_purchases = Purchase.objects.filter(
            purchase_date__gte=month_start,
            purchase_date__lt=month_end,
            status__in=['confirmed', 'received']
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        monthly_data.append({
            'month': month_start.strftime('%b'),
            'sales': float(monthly_sales),
            'purchases': float(monthly_purchases)
        })
    
    # Low stock products (products with stock <= 10)
    low_stock_products = []
    for product in Product.objects.filter(is_active=True):
        if product.stock <= 10:
            low_stock_products.append({
                'product': product,
                'stock': product.stock
            })
    
    # Sort by stock level (lowest first)
    low_stock_products.sort(key=lambda x: x['stock'])
    
    context = {
        'purchase_due_total': purchase_due_total,
        'sales_due_total': sales_due_total,
        'total_sales_amount': total_sales_amount,
        'total_customers': total_customers,
        'total_suppliers': total_suppliers,
        'total_purchase_invoices': total_purchase_invoices,
        'total_sales_invoices': total_sales_invoices,
        'recent_products': recent_products,
        'monthly_data': monthly_data,
        'low_stock_products': low_stock_products[:10],  # Show top 10 low stock items
        'current_year': current_year,
    }
    
    return render(request, 'inventory/index.html', context)