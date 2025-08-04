
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from authentication.models import User
from sms.models import BalanceLog, SingleSms, SmsAPI
from django.db.models import Count, Sum, F, FloatField, ExpressionWrapper, Func, Value
from django.db.models.functions import TruncDate


from sms.utils.report_utils import export_to_pdf, export_history_report_to_excel, export_api_report_to_excel
from commons.utils import is_ajax



@login_required
def sms_summary_report(request):
    prefix_data = [
        {'operator': 'Grameenphone', 'prefixes': ['+88013', '88013', '+88017', '88017', '013', '017']},
        {'operator': 'Banglalink', 'prefixes': ['+88014', '88014', '+88019', '88019', '014', '019']},
        {'operator': 'Teletalk', 'prefixes': ['+88015', '88015', '015']},
        {'operator': 'Airtel', 'prefixes': ['+88016', '88016', '016']},
        {'operator': 'Robi', 'prefixes': ['+88018', '88018', '018']},
    ]

    # Get filter inputs
    filter_receiver = request.GET.get('receiver')
    filter_status = request.GET.get('status')
    filter_sender = request.GET.get('sender')
    filter_sms_type = request.GET.get('sms_type')
    filter_date_from = request.GET.get('date_from')
    filter_date_to = request.GET.get('date_to')
    filter_user_group = request.GET.get('user_group')

    # Initial SMS list
    sms_list = SingleSms.objects.all().order_by('-created_at').exclude(Q(sms_api__isnull=False) & Q(status='failed'))
    if request.user.role.name == 'CLIENT':
        sms_list = sms_list.filter(sender=request.user)
    elif request.user.role.name == 'RESELLER':
        user_list = User.objects.filter(owner_user=request.user).values_list('id', flat=True)
        sms_list = sms_list.filter(sender__in=user_list)
    
    user_list = sms_list.values_list('sender', flat=True)

    # Context variables
    users = User.objects.filter(id__in=user_list).distinct()
    senders = users.values_list('username', flat=True)
    user_groups = users.values_list('user_group__name', flat=True)

    # Apply filters
    if filter_receiver and filter_receiver != 'None':
        sms_list = sms_list.filter(receiver__icontains=filter_receiver)
    if filter_status and filter_status != '':
        sms_list = sms_list.filter(status=filter_status)
    if filter_sender and filter_sender != 'None':
        sms_list = sms_list.filter(sender__username__iexact=filter_sender)
    if filter_sms_type and filter_sms_type != '':
        sms_list = sms_list.filter(sms_type=filter_sms_type)
    if filter_date_from and filter_date_from!='None':
        date_from = datetime.strptime(filter_date_from, "%d-%m-%Y").strftime("%Y-%m-%d")
        sms_list = sms_list.filter(sent_at__date__gte=date_from)
    if filter_date_to and filter_date_to!='None':
        date_to = datetime.strptime(filter_date_to, "%d-%m-%Y").strftime("%Y-%m-%d")
        sms_list = sms_list.filter(sent_at__date__lte=date_to)
    
    # if filter_operator and filter_operator != '':
    #     print("sms list", sms_list)
    #     prefixes = next((data['prefixes'] for data in prefix_data if data['operator'] == filter_operator), [])
    #     if prefixes:
    #         sms_list = sms_list.filter(Q(receiver__startswith=prefixes[0]) | Q(receiver__startswith=prefixes[1]))
    #         print("sms list in filter", sms_list)
    if filter_user_group and filter_user_group != 'None':
        sms_list = sms_list.filter(sender__user_group__name__icontains=filter_user_group)

    sms_summary = []
    total_delivered = 0
    total_undelivered = 0
    total_pending = 0
    total_sms = 0

    for data in prefix_data:
        operator = data['operator']
        prefixes = data['prefixes']
        
        query = Q()
        for prefix in prefixes:
            query |= Q(receiver__startswith=prefix)
        
        # Filter the `sms_list` for each status and sum the `msg_part_count`
        delivered_count = sms_list.filter(query, status='sent').aggregate(Sum('msg_part_count'))['msg_part_count__sum'] or 0
        undelivered_count = sms_list.filter(query, status='failed').aggregate(Sum('msg_part_count'))['msg_part_count__sum'] or 0
        pending_count = sms_list.filter(query, status='pending').aggregate(Sum('msg_part_count'))['msg_part_count__sum'] or 0

        total_count = delivered_count + undelivered_count + pending_count

        total_delivered += delivered_count
        total_undelivered += undelivered_count
        total_pending += pending_count
        total_sms += total_count

        sms_summary.append({
            'operator': operator,
            'delivered': delivered_count,
            'undelivered': undelivered_count,
            'pending': pending_count,
            'total': total_count,
        })


    if not filter_receiver and not filter_status and not filter_sender and not filter_sms_type and not filter_date_from and not filter_date_to and not filter_user_group:
        sms_summary = []
        total_delivered = 0
        total_undelivered = 0
        total_pending = 0
        total_sms = 0

    context = {
        'SingleSms': SingleSms,
        'senders': senders,
        'user_groups': user_groups,
        'sms_summary': sms_summary,
        'total_delivered': total_delivered,
        'total_undelivered': total_undelivered,
        'total_pending': total_pending,
        'total_sms': total_sms,
        'filter_receiver': filter_receiver,
        'filter_status': filter_status,
        'filter_sender': filter_sender,
        'filter_sms_type': filter_sms_type,
        'filter_date_from': filter_date_from,
        'filter_date_to': filter_date_to,
        # 'filter_operator': filter_operator,
        'filter_user_group': filter_user_group,
        'prefix_data': prefix_data,
    }
    return render(request, 'sms/sms/report/summary.html', context)


@login_required
def sms_api_summary_report(request):
    filter_date_from = request.GET.get('date_from')
    filter_date_to = request.GET.get('date_to')
    # Aggregate the data by sms_api
    sms_list = SingleSms.objects.all().order_by('-created_at')
    if request.user.role.name == 'CLIENT':
        sms_list = sms_list.filter(sender=request.user)
    elif request.user.role.name == 'RESELLER':
        user_list = User.objects.filter(owner_user=request.user).values_list('id', flat=True)
        sms_list = sms_list.filter(sender__in=user_list)

    if filter_date_from and filter_date_from!='None':
        date_from = datetime.strptime(filter_date_from, "%d-%m-%Y").strftime("%Y-%m-%d")
        sms_list = sms_list.filter(sent_at__date__gte=date_from)
    if filter_date_to and filter_date_to!='None':
        date_to = datetime.strptime(filter_date_to, "%d-%m-%Y").strftime("%Y-%m-%d")
        sms_list = sms_list.filter(sent_at__date__lte=date_to)

    api_summary_report = sms_list.values('sms_api__name').annotate(
        total_sms=Sum('msg_part_count'),
        total_sent=Sum('msg_part_count', filter=Q(status='sent')),
        total_failed=Sum('msg_part_count', filter=Q(status='failed')),
        total_pending=Sum('msg_part_count', filter=Q(status='pending'))
    ).order_by('sms_api__priority') 


    if not filter_date_from and not filter_date_to:
        api_summary_report = []

    context = {
        'api_summary_report': api_summary_report,
        'filter_date_from': filter_date_from,
        'filter_date_to': filter_date_to,
    }
    return render(request, 'sms/sms/report/sms_api_summary.html', context)


@login_required
def sms_history_report(request):
    # Get filter inputs
    filter_search_input = request.GET.get('search_input', None)
    filter_receiver = request.GET.get('receiver', None)
    filter_message = request.GET.get('message', None)
    filter_status = request.GET.get('status', None)
    filter_gateway = request.GET.get('gateway', None)
    filter_route_api = request.GET.get('route_api', None)
    filter_sender = request.GET.get('sender', None)
    filter_date_from = request.GET.get('date_from')
    filter_date_to = request.GET.get('date_to')
    filter_user_group = request.GET.get('user_group', None)
    filter_search_value = request.GET.get('search', None)
    export_format = request.GET.get('export_format', None)

    print("filter_message", filter_message)

    # Initial SMS list
    sms_list = SingleSms.objects.exclude(Q(sms_api__isnull=False) & Q(status='failed')).order_by('-created_at')
    
    if request.user.role.name == 'CLIENT':
        sms_list = sms_list.filter(sender=request.user)
    elif request.user.role.name == 'RESELLER':
        user_list = User.objects.filter(owner_user=request.user).values_list('id', flat=True)
        sms_list = sms_list.filter(sender__in=user_list)

    # Apply filters
    if filter_receiver and filter_receiver!='None':
        sms_list = sms_list.filter(receiver__icontains=filter_receiver)
    if filter_status and filter_status!='None':
        sms_list = sms_list.filter(status=filter_status)
    if filter_gateway and filter_gateway!='None':
        sms_list = sms_list.filter(gateway_type=filter_gateway)
    if filter_route_api and filter_route_api!='None':
        sms_list = sms_list.filter(sms_api__name=filter_route_api)
    if filter_sender and filter_sender!='None':
        sms_list = sms_list.filter(sender__username__iexact=filter_sender)
    if filter_date_from and filter_date_from!='None':
        date_from = datetime.strptime(filter_date_from, "%d-%m-%Y").strftime("%Y-%m-%d")
        if filter_status == 'sent':
            sms_list = sms_list.filter(sent_at__date__gte=date_from)
        else:
            sms_list = sms_list.filter(created_at__date__gte=date_from)
    if filter_date_to and filter_date_to!='None':
        date_to = datetime.strptime(filter_date_to, "%d-%m-%Y").strftime("%Y-%m-%d")
        if filter_status == 'sent':
            sms_list = sms_list.filter(sent_at__date__lte=date_to)
        else:
            sms_list = sms_list.filter(created_at__date__lte=date_to)
    if filter_user_group and filter_user_group!='None':
        sms_list = sms_list.filter(sender__user_group__name__icontains=filter_user_group)
    if filter_search_value and filter_search_value!='None':
        sms_list = sms_list.filter(Q(receiver__icontains=filter_search_value))
    if filter_search_input and filter_search_input!='None':
        sms_list = sms_list.filter(Q(receiver__icontains=filter_search_input) | Q(message__icontains=filter_search_input))
    
    # Pagination
    paginator = Paginator(sms_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # For the normal page load
    user_list = sms_list.values_list('sender', flat=True)
    users = User.objects.filter(id__in=user_list).distinct()
    senders = users.values_list('username', flat=True)
    user_groups = users.values_list('user_group__name', flat=True)
    route_apis = SmsAPI.objects.all()

    if export_format == 'pdf':
        return export_to_pdf(request, sms_list, 'sms/sms/report/history_pdf_template.html')
    elif export_format == 'excel':
        return export_api_report_to_excel(request, sms_list)

    context = {
        'sms_list': page_obj,
        'filter_search_input': filter_search_input,
        'SingleSms': SingleSms,
        'senders': senders,
        'user_groups': user_groups,
        'route_apis': route_apis,
        'filter_receiver': filter_receiver,
        'filter_status': filter_status,
        'filter_gateway': filter_gateway,
        'filter_sender': filter_sender,
        'filter_date_from': filter_date_from,
        'filter_date_to': filter_date_to,
        'filter_user_group': filter_user_group,
        'filter_route_api': filter_route_api,
    }
    
    # Return the full page if not an AJAX request
    if not is_ajax(request):
        return render(request, 'sms/sms/report/history.html', context)

    # For AJAX requests, return only the necessary parts (table + pagination)
    return render(request, 'sms/sms/report/history_ajax.html', context)


@login_required
def api_history_report(request):
    # Get filter inputs
    filter_search_input = request.GET.get('search_input', None)
    filter_receiver = request.GET.get('receiver', None)
    filter_status = request.GET.get('status', None)
    filter_gateway = request.GET.get('gateway', None)
    filter_route_api = request.GET.get('route_api', None)
    filter_sender = request.GET.get('sender', None)
    filter_sms_type = request.GET.get('sms_type')
    filter_date_from = request.GET.get('date_from')
    filter_date_to = request.GET.get('date_to')
    filter_user_group = request.GET.get('user_group', None)
    filter_search_value = request.GET.get('search', None)
    export_format = request.GET.get('export_format', None)


    # Initial SMS list
    sms_list = SingleSms.objects.order_by('-created_at')
    
    if request.user.role.name == 'CLIENT':
        sms_list = sms_list.filter(sender=request.user)
    elif request.user.role.name == 'RESELLER':
        user_list = User.objects.filter(owner_user=request.user).values_list('id', flat=True)
        sms_list = sms_list.filter(sender__in=user_list)

    # Apply filters
    if filter_receiver and filter_receiver!='None':
        sms_list = sms_list.filter(receiver__icontains=filter_receiver)
    if filter_status and filter_status!='None':
        sms_list = sms_list.filter(status__icontains=filter_status)
    if filter_gateway and filter_gateway!='None':
        sms_list = sms_list.filter(gateway_type=filter_gateway)
    if filter_route_api and filter_route_api!='None':
        sms_list = sms_list.filter(sms_api__name=filter_route_api)
    if filter_sender and filter_sender!='None':
        sms_list = sms_list.filter(sender__username__iexact=filter_sender)
    if filter_sms_type and filter_sms_type != '':
        sms_list = sms_list.filter(sms_type=filter_sms_type)
    if filter_date_from and filter_date_from!='None':
        date_from = datetime.strptime(filter_date_from, "%d-%m-%Y").strftime("%Y-%m-%d")
        if filter_status == 'sent':
            sms_list = sms_list.filter(sent_at__date__gte=date_from)
        else:
            sms_list = sms_list.filter(created_at__date__gte=date_from)
    if filter_date_to and filter_date_to!='None':
        date_to = datetime.strptime(filter_date_to, "%d-%m-%Y").strftime("%Y-%m-%d")
        if filter_status == 'sent':
            sms_list = sms_list.filter(sent_at__date__lte=date_to)
        else:
            sms_list = sms_list.filter(created_at__date__lte=date_to)
    if filter_user_group and filter_user_group!='None':
        sms_list = sms_list.filter(sender__user_group__name__icontains=filter_user_group)
    if filter_search_value and filter_search_value!='None':
        sms_list = sms_list.filter(Q(receiver__icontains=filter_search_value))
    if filter_search_input and filter_search_input!='None':
        sms_list = sms_list.filter(Q(receiver__icontains=filter_search_input) | Q(message__icontains=filter_search_input))
    
    # Pagination
    paginator = Paginator(sms_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # For the normal page load
    user_list = sms_list.values_list('sender', flat=True)
    users = User.objects.filter(id__in=user_list).distinct()
    senders = users.values_list('username', flat=True)
    user_groups = users.values_list('user_group__name', flat=True)
    route_apis = SmsAPI.objects.all()

    if export_format == 'pdf':
        return export_to_pdf(request, sms_list, 'sms/sms/report/api_history_pdf_template.html')
    elif export_format == 'excel':
        return export_api_report_to_excel(request, sms_list)

    context = {
        'sms_list': page_obj,
        'filter_search_input': filter_search_input,
        'SingleSms': SingleSms,
        'senders': senders,
        'user_groups': user_groups,
        'route_apis': route_apis,
        'filter_receiver': filter_receiver,
        'filter_status': filter_status,
        'filter_gateway': filter_gateway,
        'filter_sender': filter_sender,
        'filter_date_from': filter_date_from,
        'filter_date_to': filter_date_to,
        'filter_user_group': filter_user_group,
        'filter_route_api': filter_route_api,
    }
    
    # Return the full page if not an AJAX request
    if not is_ajax(request):
        return render(request, 'sms/sms/report/api_history.html', context)

    # For AJAX requests, return only the necessary parts (table + pagination)
    return render(request, 'sms/sms/report/api_history_ajax.html', context)


@login_required
def get_dashboard_data(request):
    today = timezone.now()
    start_date = today - timezone.timedelta(days=15)

    sms_list = SingleSms.objects.all().order_by('-created_at')
    if request.user.role.name == 'CLIENT':
        sms_list = sms_list.filter(sender=request.user)
    elif request.user.role.name == 'RESELLER':
        user_list = User.objects.filter(owner_user=request.user).values_list('id', flat=True)
        sms_list = sms_list.filter(sender__in=user_list)

    data = sms_list.filter(
        created_at__range=[start_date, today]
    ).values(
        'created_at__date'
    ).annotate(
        received_count=Sum('msg_part_count', filter=Q(status='sent')),
        pending_count=Sum('msg_part_count', filter=Q(status='pending')),
        failed_count=Sum('msg_part_count', filter=(Q(status='failed') & (Q(sms_api__isnull=True)))),
        api_failed_count=Sum('msg_part_count', filter=(Q(status='failed') & (Q(sms_api__isnull=False)))),
    ).order_by('created_at__date')

    response = {
        'dates': [],
        'received': [],
        'pending': [],
        'failed': [],
    }

    if request.user.role.name == 'ADMIN':
        response['api_failed'] = []

    for entry in data:
        response['dates'].append(entry['created_at__date'].strftime('%Y-%m-%d'))
        response['received'].append(entry.get('received_count', 0))  # Use get to handle cases with no value
        response['pending'].append(entry.get('pending_count', 0))
        response['failed'].append(entry.get('failed_count', 0))
        if request.user.role.name == 'ADMIN':
            response['api_failed'].append(entry.get('api_failed_count', 0))

    return JsonResponse(response)


@login_required
def balance_log_report(request):
    # Get filter inputs
    filter_search_input = request.GET.get('search_input', None)
    filter_receiver = request.GET.get('receiver', None)
    filter_status = request.GET.get('status', None)
    filter_gateway = request.GET.get('gateway', None)
    filter_sender = request.GET.get('sender', None)
    filter_date_from = request.GET.get('date_from')
    filter_date_to = request.GET.get('date_to')
    filter_user_group = request.GET.get('user_group', None)
    filter_search_value = request.GET.get('search', None)

    # Initial SMS list
    balance_logs = BalanceLog.objects.all().order_by('-created_at')
    
    if request.user.role.name == 'CLIENT':
        balance_logs = balance_logs.filter(sender=request.user)
    elif request.user.role.name == 'RESELLER':
        user_list = User.objects.filter(owner_user=request.user).values_list('id', flat=True)
        balance_logs = balance_logs.filter(sender__in=user_list)

    # Apply filters
    # if filter_receiver and filter_receiver!='None':
    #     balance_logs = balance_logs.filter(receiver__icontains=filter_receiver)
    # if filter_status and filter_status!='None':
    #     balance_logs = balance_logs.filter(status=filter_status)
    # if filter_gateway and filter_gateway!='None':
    #     balance_logs = balance_logs.filter(gateway_type=filter_gateway)
    if filter_sender and filter_sender!='None':
        balance_logs = balance_logs.filter(sender__username__iexact=filter_sender)
    if filter_date_from and filter_date_from!='None':
        date_from = datetime.strptime(filter_date_from, "%d-%m-%Y").strftime("%Y-%m-%d")
        balance_logs = balance_logs.filter(created_at__date__gte=date_from)
    if filter_date_to and filter_date_to!='None':
        date_to = datetime.strptime(filter_date_to, "%d-%m-%Y").strftime("%Y-%m-%d")
        balance_logs = balance_logs.filter(created_at__date__lte=date_to)
    # if filter_user_group and filter_user_group!='None':
    #     balance_logs = balance_logs.filter(sender__user_group__name__icontains=filter_user_group)
    # if filter_search_value and filter_search_value!='None':
    #     balance_logs = balance_logs.filter(Q(receiver__icontains=filter_search_value))
    # if filter_search_input and filter_search_input!='None':
    #     balance_logs = balance_logs.filter(Q(receiver__icontains=filter_search_input) | Q(message__icontains=filter_search_input))
    
    # Pagination
    paginator = Paginator(balance_logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # For the normal page load
    user_list = balance_logs.values_list('sender', flat=True)
    users = User.objects.filter(id__in=user_list).distinct()
    senders = users.values_list('username', flat=True)
    user_groups = users.values_list('user_group__name', flat=True).distinct()

    context = {
        'balance_logs': page_obj,
        'filter_search_input': filter_search_input,
        'SingleSms': SingleSms,
        'senders': senders,
        'user_groups': user_groups,
        'filter_receiver': filter_receiver,
        'filter_status': filter_status,
        'filter_gateway': filter_gateway,
        'filter_sender': filter_sender,
        'filter_date_from': filter_date_from,
        'filter_date_to': filter_date_to,
        'filter_user_group': filter_user_group,
    }
    
    # Return the full page if not an AJAX request
    if not is_ajax(request):
        return render(request, 'sms/sms/report/balance_log.html', context)

    # For AJAX requests, return only the necessary parts (table + pagination)
    return render(request, 'sms/sms/report/balance_log_ajax.html', context)


@login_required
def sms_group_report(request):
    filter_sender = request.GET.get('sender', None)
    filter_sms_type = request.GET.get('sms_type')
    filter_date_from = request.GET.get('date_from')
    filter_date_to = request.GET.get('date_to')

    if not filter_date_from and not filter_date_to:
        filter_date_from = (timezone.now() - timezone.timedelta(days=1)).strftime("%d-%m-%Y")
        filter_date_to = timezone.now().strftime("%d-%m-%Y")


    # Group SingleSms by 'message' and calculate counts
    sms_list = SingleSms.objects.filter(is_sent=True)
    if request.user.role.name == 'CLIENT':
        sms_list = sms_list.filter(sender=request.user)

    
    if filter_sender and filter_sender!='None':
        sms_list = sms_list.filter(sender__username__iexact=filter_sender)
    if filter_sms_type and filter_sms_type != '':
        sms_list = sms_list.filter(sms_type=filter_sms_type)
    if filter_date_from and filter_date_from!='None':
        date_from = datetime.strptime(filter_date_from, "%d-%m-%Y").strftime("%Y-%m-%d")
        sms_list = sms_list.filter(sent_at__date__gte=date_from)
    if filter_date_to and filter_date_to!='None':
        date_to = datetime.strptime(filter_date_to, "%d-%m-%Y").strftime("%Y-%m-%d")
        sms_list = sms_list.filter(sent_at__date__lte=date_to)
        
    report_data = sms_list.annotate(
            sent_date=TruncDate('sent_at')
        ).values('message', 'sent_date').annotate(
            total_sms=Count('id'),
            total_number_of_messages=Sum('msg_part_count')
        ).order_by('-sent_date')
    
    total_sms = report_data.aggregate(Sum('total_sms'))['total_sms__sum'] or 0
    total_number_of_messages = report_data.aggregate(Sum('total_number_of_messages'))['total_number_of_messages__sum'] or 0
    
    report_data = list(report_data)

    # Build a map: (message, sent_date) -> list of numbers
    receiver_map = {}
    for sms in sms_list:
        key = (sms.message, sms.sent_at.date())
        receiver_map.setdefault(key, []).append(sms.receiver)

    # Attach the numbers to each group
    for row in report_data:
        key = (row['message'], row['sent_date'])
        row['receiver'] = list(receiver_map.get(key, []))

    senders = User.objects.filter(role__name='CLIENT').distinct()
    
    # Set up pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(report_data, 50)  # Show 50 items per page
    sms_list = paginator.get_page(page)


    context = {
        'sms_list': sms_list,
        'senders': senders,
        'filter_sender': filter_sender,
        'filter_date_from': filter_date_from,
        'filter_date_to': filter_date_to,
        'total_sms': total_sms,
        'total_number_of_messages': total_number_of_messages,
    }



    # Return the full page if not an AJAX request
    if not is_ajax(request):
        return render(request, 'sms/sms/report/sms_group_report.html', context)

    # For AJAX requests, return only the necessary parts (table + pagination)
    return render(request, 'sms/sms/report/sms_group_report_ajax.html', context)
