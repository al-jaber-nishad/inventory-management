from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
import weasyprint
from django.conf import settings
import os

from sales.models import Sale
from authentication.models import Customer
from commons.utils import is_ajax


@login_required
def customer_due_report(request):
    # Get filter inputs
    filter_search = request.GET.get('search_input', '').strip()
    filter_date_from = request.GET.get('date_from', '').strip()
    filter_date_to = request.GET.get('date_to', '').strip()
    export_format = request.GET.get('export_format', None)

    # Base queryset - get sales with due amounts
    sales_qs = Sale.objects.select_related('customer').filter(due__gt=0)

    # Apply user filter for non-admin users
    user = request.user
    if not getattr(user, 'role', None) or getattr(user.role, 'name', '').upper() != 'ADMIN':
        sales_qs = sales_qs.filter(created_by=user)

    # Apply search filter
    if filter_search:
        sales_qs = sales_qs.filter(
            Q(customer__name__icontains=filter_search) | 
            Q(customer__phone__icontains=filter_search) |
            Q(invoice_number__icontains=filter_search)
        )

    # Apply date filters
    if filter_date_from:
        try:
            date_from = datetime.strptime(filter_date_from, '%Y-%m-%d').date()
            sales_qs = sales_qs.filter(sale_date__gte=date_from)
        except ValueError:
            pass

    if filter_date_to:
        try:
            date_to = datetime.strptime(filter_date_to, '%Y-%m-%d').date()
            sales_qs = sales_qs.filter(sale_date__lte=date_to)
        except ValueError:
            pass

    # Group by customer and calculate totals
    customer_due_data = {}
    total_due_amount = 0
    overdue_count = 0
    
    for sale in sales_qs.order_by('customer', 'sale_date'):
        customer = sale.customer
        customer_key = customer.id if customer else 0
        
        if customer_key not in customer_due_data:
            customer_due_data[customer_key] = {
                'customer': customer,
                'total_due': 0,
                'sales_count': 0,
                'sales': [],
                'oldest_due_date': None,
                'is_overdue': False
            }
        
        # Check if overdue
        is_overdue = False
        if sale.due_date and sale.due_date < timezone.now().date():
            is_overdue = True
            overdue_count += 1
        
        customer_due_data[customer_key]['total_due'] += sale.due
        customer_due_data[customer_key]['sales_count'] += 1
        customer_due_data[customer_key]['sales'].append({
            'sale': sale,
            'is_overdue': is_overdue
        })
        
        # Track oldest due date
        if sale.due_date:
            if (not customer_due_data[customer_key]['oldest_due_date'] or 
                sale.due_date < customer_due_data[customer_key]['oldest_due_date']):
                customer_due_data[customer_key]['oldest_due_date'] = sale.due_date
        
        # Mark customer as overdue if any sale is overdue
        if is_overdue:
            customer_due_data[customer_key]['is_overdue'] = True
        
        total_due_amount += sale.due

    # Convert to list and sort by total due amount (descending)
    due_data = list(customer_due_data.values())
    due_data.sort(key=lambda x: x['total_due'], reverse=True)

    # Calculate summary statistics
    total_customers_with_due = len(due_data)
    customers_overdue = sum(1 for item in due_data if item['is_overdue'])

    if export_format == 'pdf':
        return export_customer_due_report_to_pdf(request, {
            'due_data': due_data,
            'total_customers_with_due': total_customers_with_due,
            'total_due_amount': total_due_amount,
            'customers_overdue': customers_overdue,
            'overdue_count': overdue_count,
            'filter_search': filter_search,
            'filter_date_from': filter_date_from,
            'filter_date_to': filter_date_to,
        })

    # Pagination
    paginator = Paginator(due_data, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'due_data': page_obj,
        'total_customers_with_due': total_customers_with_due,
        'total_due_amount': total_due_amount,
        'customers_overdue': customers_overdue,
        'overdue_count': overdue_count,
        'filter_search': filter_search,
        'filter_date_from': filter_date_from,
        'filter_date_to': filter_date_to,
    }

    # Return the full page if not an AJAX request
    if not is_ajax(request):
        return render(request, 'customer_due_report/list.html', context)

    # For AJAX requests, return only the table
    return render(request, 'customer_due_report/_table_fragment.html', context)


def export_customer_due_report_to_pdf(request, context):
    # Render HTML template
    html_string = render_to_string('customer_due_report/pdf_template.html', context, request=request)
    
    # Create PDF
    html = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf_file = html.write_pdf(stylesheets=[
        weasyprint.CSS(os.path.join(settings.STATIC_ROOT, 'css/bootstrap.min.css')),
    ])
    
    # Create HTTP response
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="customer_due_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    return response