import re
import math
import pandas as pd
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from celery import shared_task
from authentication.models import Contact, ContactGroup, DeveloperApi, User
from sms.utils.balance_utils import decrease_user_balance
from sms.views.sms_processing import batch_mode_message_processing, process_sms_sending
from sms.models import SingleSms


def is_english(text):
    return bool(re.match(r'^[\x00-\x7F]*$', text))

def normalize_message(msg):
    return msg.replace('\r\n', '\n').replace('\r', '\n').strip()

def calculate_msg_parts(message):
    if is_english(message):
        return 153 if len(message) > 160 else 160
    else:
        return 67 if len(message) > 70 else 70

def split_receivers(receiver_string):
    return re.split(r'[\s,]+', receiver_string)

def handle_sms_submission(request, user, ip_address):
    """Process user-submitted SMS sending form"""
    receivers_input = request.POST.get('receivers', '').strip()
    message_input = request.POST.get('message', '').strip()

    # Normalize and analyze message
    message = normalize_message(message_input)
    message_part_length = calculate_msg_parts(message)
    msg_part_count = math.ceil(len(message) / message_part_length)

    # Parse and validate receivers
    receivers = split_receivers(receivers_input)
    total_msg_part_count = msg_part_count * len(receivers)

    # Check user balance
    if decrease_user_balance(user.id, total_msg_part_count):
        messages.error(request, f"Insufficient balance to send {total_msg_part_count} message parts.")
        return redirect('send_sms')

    # Create SMS objects in bulk
    sms_objects = [
        SingleSms(
            sender=user,
            sender_ip_address=ip_address,
            msg_part_count=msg_part_count,
            message=message,
            receiver=receiver,
            sms_type=SingleSms.SmsType.OUTGOING,
            status=SingleSms.Status.PENDING,
            gateway_type=SingleSms.GatewayType.PANEL
        )
        for receiver in receivers
    ]
    saved_sms_objects = SingleSms.objects.bulk_create(sms_objects)

    # Prepare payload for Celery task
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
        for sms in saved_sms_objects
    ]

    # Trigger async task
    process_sms_sending.delay(user.id, sms_list, total_msg_part_count)

    # Return feedback context
    return {
        'form_submit': True,
        'receiver_count': len(receivers),
        'number_of_message': msg_part_count,
        'status': True
    }


@login_required 
def send_sms(request):
    if not request.user.role.name == "CLIENT":
        return redirect('home')

    user = request.user

    # Get the sender's IP address
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR')

    if request.method == 'POST':
        mode = request.POST.get('mode')

        if mode == 'generalMode':
            receivers = request.POST.get('receivers', '')
            message = request.POST.get('message', '')
            message = message.replace('\r\n', '\n').replace('\r', '\n')
            message = message.strip()

            # message_part_length = 160 if is_english(message) else 70
            if is_english(message):
                if len(message) > 160:
                    message_part_length = 153
                else:
                    message_part_length = 160
            else:
                if len(message) > 70:
                    message_part_length = 67
                else:
                    message_part_length = 70
            msg_part_count = math.ceil(len(message)/message_part_length)

            receivers = re.split(r'[\s,]+', receivers.strip())
            print("receivers", receivers)

            # Update the balance of user before sending the sms
            total_msg_part_count = msg_part_count * len(receivers)
            is_low_balance = decrease_user_balance(user.id, total_msg_part_count)

            if is_low_balance:
                # Combine all errors into a single list
                messages.error(request, f"You do not have enough balance to send {total_msg_part_count} messages.")
                return redirect('send_sms')

            # Create the SMS list
            sms_objects = [
                SingleSms(
                    sender=user,
                    sender_ip_address=ip_address,
                    msg_part_count=msg_part_count,
                    message=message, 
                    receiver=receiver, 
                    sms_type=SingleSms.SmsType.OUTGOING, 
                    status=SingleSms.Status.PENDING,
                    gateway_type=SingleSms.GatewayType.PANEL
                )
                for receiver in receivers
            ]
            sms_object_list = SingleSms.objects.bulk_create(sms_objects)

            # Serialize the created objects into a list of dictionaries
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
                for sms in sms_object_list
            ]
                
            # Process sending SMS
            process_sms_sending.delay(user.id, sms_list, total_msg_part_count)

        elif mode == 'batchMode':
            batch_type = request.POST.get('batch_type')

            if 'file' in request.FILES:
                file = request.FILES['file']

                if batch_type == "batch":
                    df = pd.read_excel(file)
                    df = df.dropna()

                    numbers = df['numbers'].tolist()
                    message_list = df['message_list'].tolist()

                    data = list(zip(numbers, message_list))

                    batch_mode_message_processing.delay(user.id, data, ip_address)

                elif batch_type == "broadcast":
                    df = pd.read_excel(file)
                    df = df.dropna(subset=['numbers'])

                    df['message'] = df['message'].fillna(method='ffill')

                    numbers = df['numbers'].tolist()
                    message_list = df['message'].tolist()

                    data = list(zip(numbers, message_list))

                    batch_mode_message_processing.delay(user.id, data, ip_address)

        return render(request, 'sms/sms/send_sms.html', {'form_submit': True, 'receiver_count': len(receivers), 'number_of_message': msg_part_count, 'status': True})
    
    contact_groups = ContactGroup.objects.filter(owner_user=request.user, is_deleted=False)
    contacts = Contact.objects.filter(owner_user=request.user, is_deleted=False)

    return render(request, 'sms/sms/send_sms.html', {'form_submit': False, 'contact_groups': contact_groups, 'contacts': contacts})


@shared_task
def process_failed_sms_task(user_id, sms_list):
    user = User.objects.get(id=user_id)
    for item in sms_list:
        print("item", item)
        is_low_balance = decrease_user_balance(user.id, item['msg_part_count'])
        if is_low_balance:
            print("Balance is low=======================================>")
            break
        process_sms_sending.delay(user.id, sms_list, item['msg_part_count'])


@login_required
def send_group_sms(request):
    if not request.user.role.name == "CLIENT":
        return redirect('home')

    # Get the sender's IP address
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR')

    user = request.user
    contact_groups = ContactGroup.objects.filter(owner_user=user, is_deleted=False)
    contacts = Contact.objects.filter(owner_user=user, is_deleted=False)

    if request.method == 'POST':
        contact_group_id = request.POST.get('contact_group') or None
        contact_id = request.POST.get('contact') or None
        message = request.POST.get('message', '')

        if contact_group_id:
            try:
                contact_group = ContactGroup.objects.get(id=contact_group_id, owner_user=user, is_deleted=False)
            except ContactGroup.DoesNotExist:
                messages.error(request, "Invalid contact group selected.")
                return redirect('send_sms')

            contacts = Contact.objects.filter(contact_group=contact_group, is_deleted=False)
        elif contact_id:
            contacts = Contact.objects.filter(id=contact_id)
        else:
            messages.error(request, "Select contact or contact group.")
            return redirect('send_sms')

        receivers = [contact.contact_no for contact in contacts]

        # message_part_length = 160 if is_english(message) else 70
        if is_english(message):
            if len(message) > 160:
                message_part_length = 153
            else:
                message_part_length = 160
        else:
            if len(message) > 70:
                message_part_length = 67
            else:
                message_part_length = 70
        msg_part_count = math.ceil(len(message)/message_part_length)


        # Update the balance of user before sending the sms
        total_msg_part_count = msg_part_count * len(receivers)
        is_low_balance = decrease_user_balance(user.id, total_msg_part_count)

        if is_low_balance:
            # Combine all errors into a single list
            messages.error(request, f"You do not have enough balance to send {total_msg_part_count} messages.")
            return redirect('send_sms')


        # Create the SMS list
        sms_objects = [
            SingleSms(
                sender=user,
                sender_ip_address=ip_address,
                msg_part_count=msg_part_count,
                message=message, 
                receiver=receiver, 
                sms_type=SingleSms.SmsType.OUTGOING, 
                status=SingleSms.Status.PENDING,
                gateway_type=SingleSms.GatewayType.PANEL
            )
            for receiver in receivers
        ]
        sms_object_list = SingleSms.objects.bulk_create(sms_objects)

        # Serialize the created objects into a list of dictionaries
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
            for sms in sms_object_list
        ]

        # Process sending SMS
        process_sms_sending.delay(user.id, sms_list, total_msg_part_count)

        return render(request, 'sms/sms/send_sms.html', {'form_submit': True, 'receiver_count': len(receivers), 'number_of_message': msg_part_count})

    return render(request, 'sms/sms/send_sms.html', {'form_submit': False, 'contact_groups': contact_groups, 'contacts': contacts})


@csrf_exempt
def send_sms_api(request):
    if request.method == 'POST' or request.method == 'GET':
        api_key = request.GET.get('api_key') if request.method == 'GET' else request.POST.get('api_key')
        message_type = request.GET.get('type') if request.method == 'GET' else request.POST.get('type')
        phone = request.GET.get('phone') if request.method == 'GET' else request.POST.get('phone')
        message = request.GET.get('message') if request.method == 'GET' else request.POST.get('message')

        # message_part_length = 160 if is_english(message) else 70
        if is_english(message):
            if len(message) > 160:
                message_part_length = 153
            else:
                message_part_length = 160
        else:
            if len(message) > 70:
                message_part_length = 67
            else:
                message_part_length = 70
        msg_part_count = math.ceil(len(message)/message_part_length)


        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        # Validate API key
        try:
            developer_api = DeveloperApi.objects.get(api_key=api_key)
            user = developer_api.user
        except DeveloperApi.DoesNotExist:
            return JsonResponse({'success': False, 'error_code': 1001, 'message': 'Wrong API Key'}, status=400)

        if not all([message_type, phone, message]):
            return JsonResponse({'success': False, 'error_code': 400, 'message': 'Missing parameters.'}, status=400)

        if message_type not in ['text', 'unicode']:
            return JsonResponse({'success': False, 'error_code': 1003, 'message': 'Type must be text or unicode'}, status=400)

        receivers = re.split(r'[\s,]+', phone.strip())
        print("receivers", receivers)

        # Update the balance of user before sending the sms
        total_msg_part_count = msg_part_count * len(receivers)
        is_low_balance = decrease_user_balance(user.id, total_msg_part_count)

        if is_low_balance:
            return JsonResponse({'success': False, 'error_code': 1006, 'message': f"You do not have enough balance to send {total_msg_part_count} messages."}, status=400)

        # Create the SMS list
        sms_objects = [
            SingleSms(
                sender=user,
                sender_ip_address=ip_address,
                msg_part_count=msg_part_count,
                message=message, 
                receiver=receiver, 
                sms_type=SingleSms.SmsType.OUTGOING, 
                status=SingleSms.Status.PENDING,
                gateway_type=SingleSms.GatewayType.HTTPS
            )
            for receiver in receivers
        ]
        sms_object_list = SingleSms.objects.bulk_create(sms_objects)

        # Serialize the created objects into a list of dictionaries
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
            for sms in sms_object_list
        ]

        # for receiver in receivers:
        #     single_sms = SingleSms.objects.create(
        #         sender=user,
        #         sender_ip_address=ip_address,
        #         msg_part_count=msg_part_count,
        #         message=message, 
        #         receiver=receiver, 
        #         sms_type=SingleSms.SmsType.OUTGOING, 
        #         status=SingleSms.Status.PENDING,
        #         gateway_type=SingleSms.GatewayType.HTTPS
        #     )
            
        #     # Serialize the SingleSms object
        #     sms_list.append({
        #         'id': single_sms.id,
        #         'sender': single_sms.sender.id,
        #         'receiver': single_sms.receiver,
        #         'message': single_sms.message,
        #         'msg_part_count': single_sms.msg_part_count,
        #         'status': single_sms.status,
        #         'sms_type': single_sms.sms_type,
        #         'gateway_type': single_sms.gateway_type,
        #         'sender_ip_address': single_sms.sender_ip_address,
        #     })

        # Process sending SMS
        process_sms_sending.delay(user.id, sms_list, total_msg_part_count)
        is_message_sending_successful, message_sending_message = True, "Success"
        # is_message_sending_successful, message_sending_message = async_result.get()
        print("is_message_sending_successful, message_sending_message", is_message_sending_successful, message_sending_message)

        return JsonResponse({'is_success': is_message_sending_successful, 'message': message_sending_message})

    return JsonResponse({'is_success': False, 'error_code': 1004, 'message': 'Only GET and POST Methods Allow'}, status=405)
