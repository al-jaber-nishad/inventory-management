from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Case, When, IntegerField
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
import weasyprint
from django.conf import settings
import os

from product.models import Product, ProductCategory, Brand
from inventory.models import InventoryTransaction
from inventory.utils.stock_quantity import get_current_stock
from commons.utils import is_ajax


@login_required
def stock_report(request):
    # Get filter inputs
    filter_search = request.GET.get('search_input', '').strip()
    filter_category = request.GET.get('category', '').strip()
    filter_brand = request.GET.get('brand', '').strip()
    filter_stock_status = request.GET.get('stock_status', '').strip()
    export_format = request.GET.get('export_format', None)

    # Get all products with related data
    products = Product.objects.select_related('category', 'brand', 'unit').filter(is_active=True)

    # Apply search filter
    if filter_search:
        products = products.filter(
            Q(name__icontains=filter_search) | 
            Q(sku__icontains=filter_search)
        )

    # Apply category filter
    if filter_category:
        products = products.filter(category_id=filter_category)

    # Apply brand filter
    if filter_brand:
        products = products.filter(brand_id=filter_brand)

    # Build stock report data
    stock_data = []
    total_products = 0
    total_stock_value = 0
    low_stock_count = 0
    out_of_stock_count = 0

    for product in products:
        current_stock = get_current_stock(product.id)
        stock_value = current_stock * product.price
        
        # Determine stock status
        if current_stock <= 0:
            stock_status = 'out_of_stock'
            out_of_stock_count += 1
        elif current_stock <= 10:  # Assuming low stock threshold is 10
            stock_status = 'low_stock'
            low_stock_count += 1
        else:
            stock_status = 'in_stock'

        # Apply stock status filter
        if filter_stock_status:
            if filter_stock_status != stock_status:
                continue

        # Get recent transactions
        recent_transactions = InventoryTransaction.objects.filter(
            product=product
        ).select_related('created_by')[:5]

        stock_item = {
            'product': product,
            'current_stock': current_stock,
            'stock_value': stock_value,
            'stock_status': stock_status,
            'recent_transactions': recent_transactions
        }
        stock_data.append(stock_item)
        total_products += 1
        total_stock_value += stock_value

    # Sort by stock quantity (ascending for low stock first)
    stock_data.sort(key=lambda x: x['current_stock'])

    # Get filter options
    categories = ProductCategory.objects.filter(is_active=True).order_by('name')
    brands = Brand.objects.order_by('name')

    if export_format == 'pdf':
        return export_stock_report_to_pdf(request, {
            'stock_data': stock_data,
            'total_products': total_products,
            'total_stock_value': total_stock_value,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'filter_search': filter_search,
            'filter_category': filter_category,
            'filter_brand': filter_brand,
            'filter_stock_status': filter_stock_status,
        })

    # Pagination
    paginator = Paginator(stock_data, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'stock_data': page_obj,
        'categories': categories,
        'brands': brands,
        'total_products': total_products,
        'total_stock_value': total_stock_value,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'filter_search': filter_search,
        'filter_category': filter_category,
        'filter_brand': filter_brand,
        'filter_stock_status': filter_stock_status,
        'selected_category': int(filter_category) if filter_category else None,
        'selected_brand': int(filter_brand) if filter_brand else None,
    }

    # Return the full page if not an AJAX request
    if not is_ajax(request):
        return render(request, 'stock_report/list.html', context)

    # For AJAX requests, return only the table
    return render(request, 'stock_report/_table_fragment.html', context)


def export_stock_report_to_pdf(request, context):
    # Render HTML template
    html_string = render_to_string('stock_report/pdf_template.html', context, request=request)
    
    # Create PDF
    html = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf_file = html.write_pdf(stylesheets=[
        weasyprint.CSS(os.path.join(settings.STATIC_ROOT, 'css/bootstrap.min.css')),
    ])
    
    # Create HTTP response
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="stock_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    return response