from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Case, When, DecimalField
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
import weasyprint
from django.conf import settings
import os

from accounts.models import AccountLog, LedgerAccount, Group, PrimaryGroup
from commons.utils import is_ajax


@login_required
def balance_sheet_report(request):
    # Get filter inputs
    filter_date_from = request.GET.get('date_from')
    filter_date_to = request.GET.get('date_to')
    export_format = request.GET.get('export_format', None)

    # Default date range if not provided
    if not filter_date_from:
        filter_date_from = timezone.now().replace(day=1).strftime("%d-%m-%Y")
    if not filter_date_to:
        filter_date_to = timezone.now().strftime("%d-%m-%Y")

    # Parse dates
    date_from = datetime.strptime(filter_date_from, "%d-%m-%Y").date()
    date_to = datetime.strptime(filter_date_to, "%d-%m-%Y").date()

    # Get account logs for the date range
    account_logs = AccountLog.objects.filter(
        date__date__gte=date_from,
        date__date__lte=date_to,
        ledger__isnull=False
    ).select_related('ledger', 'ledger__head_group', 'ledger__head_group__head_primarygroup')

    # Calculate balances for each ledger account
    ledger_balances = {}
    for log in account_logs:
        ledger_id = log.ledger.id
        if ledger_id not in ledger_balances:
            ledger_balances[ledger_id] = {
                'ledger': log.ledger,
                'debit_total': 0,
                'credit_total': 0,
                'balance': 0
            }
        
        debit_amount = log.debit_amount or 0
        credit_amount = log.credit_amount or 0
        
        ledger_balances[ledger_id]['debit_total'] += debit_amount
        ledger_balances[ledger_id]['credit_total'] += credit_amount
        ledger_balances[ledger_id]['balance'] = (
            ledger_balances[ledger_id]['debit_total'] - 
            ledger_balances[ledger_id]['credit_total']
        )

    # Group by primary groups for balance sheet presentation
    assets_data = []
    liabilities_data = []
    total_assets = 0
    total_liabilities = 0

    for balance_data in ledger_balances.values():
        ledger = balance_data['ledger']
        balance = balance_data['balance']
        
        if ledger.head_group and ledger.head_group.head_primarygroup:
            primary_group = ledger.head_group.head_primarygroup
            
            # Assets (PrimaryGroup ID = 1)
            if primary_group.id == 1:
                assets_data.append({
                    'ledger_name': ledger.name,
                    'group_name': ledger.head_group.name,
                    'balance': abs(balance),  # Show absolute value
                    'debit_total': balance_data['debit_total'],
                    'credit_total': balance_data['credit_total']
                })
                total_assets += abs(balance)
            
            # Liabilities (PrimaryGroup ID = 2)
            elif primary_group.id == 2:
                liabilities_data.append({
                    'ledger_name': ledger.name,
                    'group_name': ledger.head_group.name,
                    'balance': abs(balance),  # Show absolute value
                    'debit_total': balance_data['debit_total'],
                    'credit_total': balance_data['credit_total']
                })
                total_liabilities += abs(balance)

    # Sort by group name and then by ledger name
    assets_data.sort(key=lambda x: (x['group_name'], x['ledger_name']))
    liabilities_data.sort(key=lambda x: (x['group_name'], x['ledger_name']))

    # Group assets and liabilities by group name for better presentation
    grouped_assets = {}
    for asset in assets_data:
        group_name = asset['group_name']
        if group_name not in grouped_assets:
            grouped_assets[group_name] = []
        grouped_assets[group_name].append(asset)

    grouped_liabilities = {}
    for liability in liabilities_data:
        group_name = liability['group_name']
        if group_name not in grouped_liabilities:
            grouped_liabilities[group_name] = []
        grouped_liabilities[group_name].append(liability)

    # Calculate group totals
    assets_group_totals = {}
    for group_name, items in grouped_assets.items():
        assets_group_totals[group_name] = sum(item['balance'] for item in items)

    liabilities_group_totals = {}
    for group_name, items in grouped_liabilities.items():
        liabilities_group_totals[group_name] = sum(item['balance'] for item in items)

    if export_format == 'pdf':
        return export_balance_sheet_to_pdf(request, {
            'grouped_assets': grouped_assets,
            'grouped_liabilities': grouped_liabilities,
            'assets_group_totals': assets_group_totals,
            'liabilities_group_totals': liabilities_group_totals,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'filter_date_from': filter_date_from,
            'filter_date_to': filter_date_to,
        })

    context = {
        'grouped_assets': grouped_assets,
        'grouped_liabilities': grouped_liabilities,
        'assets_group_totals': assets_group_totals,
        'liabilities_group_totals': liabilities_group_totals,
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'filter_date_from': filter_date_from,
        'filter_date_to': filter_date_to,
    }

    # Return the full page if not an AJAX request
    if not is_ajax(request):
        return render(request, 'balance_sheet/list.html', context)

    # For AJAX requests, return only the table
    return render(request, 'balance_sheet/_table_fragment.html', context)


def export_balance_sheet_to_pdf(request, context):
    # Render HTML template
    html_string = render_to_string('balance_sheet/pdf_template.html', context, request=request)
    
    # Create PDF
    html = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf_file = html.write_pdf(stylesheets=[
        weasyprint.CSS(os.path.join(settings.STATIC_ROOT, 'css/bootstrap.min.css')),
    ])
    
    # Create HTTP response
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="balance_sheet_{context["filter_date_from"]}_{context["filter_date_to"]}.pdf"'
    return response