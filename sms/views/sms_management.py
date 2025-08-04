from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from authentication.models import User
from sms.models import SingleSms, Sms
from commons.utils import is_ajax
from sms.views.sms_processing import send_sms_processing
from sms.views.sms_views import process_failed_sms_task


@login_required
def all_sms_list(request):
    sms_list = SingleSms.objects.exclude(Q(sms_api__isnull=False) & Q(status='failed')).order_by('-created_at')
    if request.user.role.name == 'CLIENT':
        sms_list = sms_list.filter(sender=request.user)
    elif request.user.role.name == 'RESELLER':
        user_list = User.objects.filter(owner_user=request.user).values_list('id', flat=True)
        sms_list = sms_list.filter(sender__in=user_list)
    
    filter_search_input = request.GET.get('search_input', None)
    if filter_search_input:
        sms_list = sms_list.filter(Q(receiver__icontains=filter_search_input) | Q(message__icontains=filter_search_input))
    
    # Pagination
    paginator = Paginator(sms_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'sms_list': page_obj,
        'filter_search_input': filter_search_input    
    }
    
    # Return the full page if not an AJAX request
    if not is_ajax(request):
        return render(request, 'sms/sms/all_sms_list.html', context)

    # For AJAX requests, return only the necessary parts (table + pagination)
    return render(request, 'sms/sms/all_sms_list_ajax.html', context)


@login_required
def sent_sms_list(request):
    sms_list = SingleSms.objects.filter(status=SingleSms.Status.SENT).order_by('-created_at').exclude(Q(sms_api__isnull=False) & Q(status='failed'))
    if request.user.role.name == 'CLIENT':
        sms_list = sms_list.filter(sender=request.user)
    elif request.user.role.name == 'RESELLER':
        user_list = User.objects.filter(owner_user=request.user).values_list('id', flat=True)
        sms_list = sms_list.filter(sender__in=user_list)
    
    filter_search_input = request.GET.get('search_input', None)
    if filter_search_input:
        sms_list = sms_list.filter(Q(contact_no__icontains=filter_search_input) | Q(name__icontains=filter_search_input))
    
    # Pagination
    paginator = Paginator(sms_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'sms_list': page_obj,
        'filter_search_input': filter_search_input    
    }
    
    # Return the full page if not an AJAX request
    if not is_ajax(request):
        return render(request, 'sms/sms/all_sms_list.html', context)

    # For AJAX requests, return only the necessary parts (table + pagination)
    return render(request, 'sms/sms/all_sms_list_ajax.html', context)


@login_required
def inbox_sms_list(request):
    sms_list = Sms.objects.filter(created_at__lte='2024-01-01')
    context = {'sms_list': sms_list}
    return render(request, 'sms/sms/all_sms_list.html', context)


@login_required
def queued_sms_list(request):
    sms_obj_list = SingleSms.objects.filter(status=SingleSms.Status.PENDING).order_by('-created_at').exclude(Q(sms_api__isnull=False) & Q(status='failed'))
    if request.user.role.name == 'CLIENT':
        sms_obj_list = sms_obj_list.filter(sender=request.user)
    elif request.user.role.name == 'RESELLER':
        user_list = User.objects.filter(owner_user=request.user).values_list('id', flat=True)
        sms_obj_list = sms_obj_list.filter(sender__in=user_list)
    
    filter_search_input = request.GET.get('search_input', None)
    filter_sender = request.GET.get('sender', None)
    filter_date_from = request.GET.get('date_from', None)
    filter_date_to = request.GET.get('date_to', None)
    send_pending_sms_button = request.GET.get('send_pending_sms_button', None)
    print("send_pending_sms_button", send_pending_sms_button)
    

    if filter_search_input:
        sms_obj_list = sms_obj_list.filter(Q(contact_no__icontains=filter_search_input) | Q(name__icontains=filter_search_input))
    if filter_sender and filter_sender!='None':
        sms_obj_list = sms_obj_list.filter(sender__username__iexact=filter_sender)
    if filter_date_from and filter_date_from!='None':
        date_from = datetime.strptime(filter_date_from, "%d-%m-%Y").strftime("%Y-%m-%d")
        sms_obj_list = sms_obj_list.filter(created_at__date__gte=date_from)
    if filter_date_to and filter_date_to!='None':
        date_to = datetime.strptime(filter_date_to, "%d-%m-%Y").strftime("%Y-%m-%d")
        sms_obj_list = sms_obj_list.filter(created_at__date__lte=date_to)

    print("sms_obj_list", sms_obj_list)
    # Send Pending SMS
    if 'send_pending_sms_button' in request.GET:
        print("send_pending_sms_button is clicked. Pending SMS sending starts now.")
        sms_list = [
            {
                'id': sms.id,
                'sender': sms.sender_id,
                'receiver': sms.receiver,
                'message': sms.message,
                'msg_part_count': sms.msg_part_count,
                'status': sms.status,
                'sms_type': sms.sms_type,
                'gateway_type': sms.gateway_type,
                'sender_ip_address': sms.sender_ip_address
            }
            for sms in sms_obj_list
        ]
        print("sms_list", sms_list)
        # for item in sms_list:
        #     process_sms_sending.delay(item['sender'], sms_list, msg_part_count)
    else:
        print("normal search button is clicked.")

    users = User.objects.filter(role__name='CLIENT').distinct()
    senders = users.values_list('username', flat=True)
    
    # Pagination
    paginator = Paginator(sms_obj_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'senders': senders,
        'filter_sender': filter_sender,
        'filter_date_from': filter_date_from,
        'filter_date_to': filter_date_to,
        'sms_list': page_obj,
        'filter_search_input': filter_search_input    
    }
    
    # Return the full page if not an AJAX request
    if not is_ajax(request):
        return render(request, 'sms/sms/all_sms_list.html', context)

    # For AJAX requests, return only the necessary parts (table + pagination)
    return render(request, 'sms/sms/all_sms_list_ajax.html', context)


@login_required
def get_queued_sms_number(request):
    one_hour_ago = timezone.now() - timedelta(hours=1)
    
    sms_obj_list = SingleSms.objects.filter(
        status=SingleSms.Status.PENDING,
        sender=request.user  
    ).exclude(status='failed')

    return JsonResponse({'count': sms_obj_list.count()})


@login_required
def failed_sms_list(request):
    sms_list = SingleSms.objects.filter(status=SingleSms.Status.FAILED).exclude(Q(sms_api__isnull=False) & Q(status='failed')).order_by('-created_at')
    if not request.user.role.name == 'ADMIN':
        sms_list = sms_list.filter(sms_api__isnull=True)
    if request.user.role.name == 'CLIENT':
        sms_list = sms_list.filter(sender=request.user)
    elif request.user.role.name == 'RESELLER':
        user_list = User.objects.filter(owner_user=request.user).values_list('id', flat=True)
        sms_list = sms_list.filter(sender__in=user_list)
    
    filter_search_input = request.GET.get('search_input', None)
    if filter_search_input:
        sms_list = sms_list.filter(Q(contact_no__icontains=filter_search_input) | Q(name__icontains=filter_search_input))
    
    # Pagination
    paginator = Paginator(sms_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'sms_list': page_obj,
        'filter_search_input': filter_search_input    
    }
    
    # Return the full page if not an AJAX request
    if not is_ajax(request):
        return render(request, 'sms/sms/all_sms_list.html', context)

    # For AJAX requests, return only the necessary parts (table + pagination)
    return render(request, 'sms/sms/all_sms_list_ajax.html', context)


@login_required
def failed_and_pending_sms_list(request):
    if request.user.role.name != 'ADMIN':
        return redirect('home')

    # Get filtering values from request
    filter_search_input = request.GET.get('search_input', '').strip()
    filter_sender = request.GET.get('sender', '').strip()
    filter_status = request.GET.get('status', '').strip()
    filter_date_from = request.GET.get('date_from', '').strip()
    filter_date_to = request.GET.get('date_to', '').strip()
    send_pending_sms_button = request.GET.get('send_pending_sms_button', None)

    print("filter_sender", filter_sender)

    # Base QuerySet (filter unsent SMS excluding those with `sms_api=None`)
    # sms_obj_list = SingleSms.objects.filter(is_sent=False).exclude(Q(sms_api__isnull=False) & Q(status='failed'))
    sms_obj_list = SingleSms.objects.filter(is_sent=False, status='pending').distinct('receiver', 'message', 'created_at')

    # Apply filters dynamically
    filters = Q()
    
    if filter_search_input:
        filters &= Q(receiver__icontains=filter_search_input)

    if filter_sender:
        filters &= Q(sender__username__iexact=filter_sender)
    
    if filter_status:
        filters &= Q(status__iexact=filter_status)

    if filter_date_from:
        try:
            date_from = datetime.strptime(filter_date_from, "%d-%m-%Y").strftime("%Y-%m-%d")
            filters &= Q(created_at__date__gte=date_from)
        except ValueError:
            pass  # Ignore invalid date format

    if filter_date_to:
        try:
            date_to = datetime.strptime(filter_date_to, "%d-%m-%Y").strftime("%Y-%m-%d")
            filters &= Q(created_at__date__lte=date_to)
        except ValueError:
            pass  # Ignore invalid date format
    
    # Apply all filters at once
    sms_obj_list = sms_obj_list.filter(filters).order_by('-created_at')

    # Handle sending pending SMS
    if send_pending_sms_button:
        print("send_pending_sms_button is clicked. Pending SMS sending starts now.")
        if not filter_sender:
            messages.error(request, "Sender is required.")
            return redirect('failed_and_pending_sms_list')
        
        sms_list = []
        for sms in sms_obj_list:
            print("sms", sms)
            sms_list.append(
                {
                    'id': sms.id,
                    'sender': sms.sender.id,
                    'receiver': sms.receiver,
                    'message': sms.message,
                    'msg_part_count': sms.msg_part_count,
                    'status': sms.status,
                    'sms_type': sms.sms_type,
                    'gateway_type': sms.gateway_type,
                    'sender_ip_address': sms.sender_ip_address
                })

        print("sms_list", len(sms_list))

        # send_sms_processing(filter_sender, sms_list, msg_part_count=None),

        return redirect('all_sms_list')

    # Get list of senders
    senders = User.objects.filter(role__name='CLIENT').values_list('username', flat=True).distinct()

    # Pagination
    paginator = Paginator(sms_obj_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'SingleSms': SingleSms,
        'senders': senders,
        'filter_sender': filter_sender,
        'filter_date_from': filter_date_from,
        'filter_date_to': filter_date_to,
        'filter_status': filter_status,
        'sms_list': page_obj,
        'filter_search_input': filter_search_input
    }

    # Return the full page if not an AJAX request
    if not is_ajax(request):
        return render(request, 'sms/sms/failed_pending_sms_list.html', context)

    # For AJAX requests, return only the necessary parts (table + pagination)
    return render(request, 'sms/sms/all_sms_list_ajax.html', context)


@login_required
def sms_detail(request, pk):
    sms = get_object_or_404(Sms, pk=pk)  # Get specific sms history
    single_sms = SingleSms.objects.filter(sms=sms)
    context = {'sms': sms, 'single_sms': single_sms}
    return render(request, 'sms/sms/detail.html', context)

