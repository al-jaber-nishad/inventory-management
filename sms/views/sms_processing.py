import math
from celery import shared_task, chain
from sms.models import BalanceLog, SingleSms, AssignSmsAPI, SmsAPI
from authentication.models import User
from sms.utils.balance_utils import increase_user_balance
from sms.views.sms_views import decrease_user_balance
from utils.send_balance_alert_message import send_balance_alert_message
from sms.tasks import is_english, send_sms_task
from django.db.models import Q, Sum
from decimal import Decimal
from time import sleep


def process_single_sms(user_id, sms, sms_api_list):
    for api in sms_api_list:
        sms_api_obj = api['sms_api'] if hasattr(api, 'sms_api') else api
        # if hasattr(api, 'is_shared') and not api.is_eligible():
        #     continue
        
        #* This actually sends the message
        is_success = send_sms_task.delay(
            sms['receiver'], sms['message'], sms['id'], sms_api_obj['url'], sms_api_obj['id']
        )

        if is_success:
            break


@shared_task
def send_sms_processing(user_id=None, sms_list=None, msg_part_count=None):
    try:
        #send_balance_alert_message.delay()
        user = User.objects.get(id=user_id)
        assigned_sms_api = AssignSmsAPI.objects.filter(user=user.owner_user, is_active=True).order_by('priority')
        if not assigned_sms_api.exists():
            sms_api_list = SmsAPI.objects.all().order_by('priority')
        else:
            assigned_api_list = assigned_sms_api.values_list('sms_api', flat=True).order_by('priority')
            sms_api_list = SmsAPI.objects.filter(id__in=assigned_api_list)

        sms_api_dict = [
            {
                'id': sms_api.id,
                'url': sms_api.url,
                'priority': sms_api.priority,
            }
            for sms_api in sms_api_list
        ]
        
        for sms in sms_list:
            process_single_sms(user_id, sms, sms_api_dict)
        
        return True, 'Success'
            
    except Exception as e:
        return False, str(e)


@shared_task
def process_sms_sending(user_id=None, sms_list=None, msg_part_count=None):
    try:
        chain(
            send_sms_processing.s(user_id, sms_list, msg_part_count),
            process_sms_completion.s(user_id, sms_list)
        ).apply_async()
    
    except Exception as e:
        return False, str(e)


@shared_task
def process_sms_completion(_, user_id, sms_list):
    sleep(30)
    sms_ids = [sms['id'] for sms in sms_list]
    failed_sms_data = SingleSms.objects.filter(
        id__in=sms_ids, 
        sms_api__isnull=True, 
        is_sent=False
    ).aggregate(total_message_parts=Sum('msg_part_count'))

    failed_message_part_count = failed_sms_data['total_message_parts'] or 0

    print("failed_sms_count", failed_message_part_count)

    if failed_message_part_count>0:
        print(f"Increasing balance of user id {user_id}. failed sms count is {failed_message_part_count}")
        increase_user_balance(user_id, failed_message_part_count)
        return False
    
    return True


@shared_task
def batch_mode_message_processing(user_id, data, ip_address):
    user = User.objects.get(id=user_id)

    for each_data in data:
        message_part_length = 160 if is_english(each_data[1]) else 70
        msg_part_count = math.ceil(len(each_data[1])/message_part_length)

        message = each_data[1]
        receivers = [each_data[0]]

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
        process_sms_sending.delay(user.id, sms_list, msg_part_count)


    user = User.objects.get(id=user_id)
    is_prefix_based = user.package.prefix_based

    # Balance log 
    BalanceLog.objects.create(
        sender=user,
        current_balance=user.local_non_masking_message_amount,
        after_operation_balance=Decimal(user.local_non_masking_message_amount+msg_part_count),
        number_of_sms_count=msg_part_count,
        note="increasing balance"
    )

    print("before: ", user.local_non_masking_message_amount)
    if is_prefix_based:
        if user.region_type == 'local':
            user.local_non_masking_balance += Decimal(msg_part_count * user.package.non_masking_national_msg_charge)
            user.owner_user.local_non_masking_balance += Decimal(msg_part_count * user.package.non_masking_national_msg_charge)
        elif user.region_type == 'international':
            user.internation_non_masking_balance += Decimal(msg_part_count * user.package.non_masking_international_msg_charge)
            user.owner_user.internation_non_masking_balance += Decimal(msg_part_count * user.package.non_masking_international_msg_charge)
    else:
        if user.region_type == 'local':
            user.local_non_masking_message_amount += Decimal(msg_part_count)
            user.owner_user.local_non_masking_message_amount += Decimal(msg_part_count)
        elif user.region_type == 'international':
            user.internation_non_masking_message_amount += Decimal(msg_part_count)
            user.owner_user.internation_non_masking_message_amount += Decimal(msg_part_count)

    user.save()
    user.owner_user.save()
    print("after: ", user.local_non_masking_message_amount)