import os
import sys
import django
from decimal import Decimal

# Set up Django environment
sys.path.append('/home/bluebays/sms.bluebayit.com/')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils import timezone

from authentication.models import Country, User, Role
from sms.models import BalanceLog, SingleSms, AssignSmsAPI, SmsAPI
from sms.tasks import send_sms_task



def process_sms():
    user = User.objects.get(id=32)
    is_prefix_based = user.package.prefix_based

    sms_object_list = SingleSms.objects.filter(sender=user, status="pending")

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

    try:
        assigned_sms_api = AssignSmsAPI.objects.filter(user=user.owner_user, is_active=True).order_by('priority')
        if not assigned_sms_api.exists():
            sms_api_list = SmsAPI.objects.all().order_by('priority')
        else:
            sms_api_list = assigned_sms_api.select_related('sms_api').order_by('priority')
        
        print("sms_api_list", sms_api_list)
        is_message_sending_successful = False

        # Balance log 
        balance_log_instance = BalanceLog.objects.create(
            sender=user,
            current_balance=user.local_non_masking_message_amount,
        )
        number_of_sms, number_of_sms_count = 0, 0
        for sms in sms_list:
            print("-------------------", number_of_sms)
            print(sms)
            for api in sms_api_list:
                sms_api_obj = api.sms_api if assigned_sms_api.exists() else api
                
                if hasattr(api, 'is_shared') and api.is_shared:
                    if not api.is_eligible():
                        continue

                print("Finally used api", api)
                is_low_balance = False
                if is_prefix_based:
                    if user.region_type == 'local':
                        user.local_non_masking_balance -= Decimal(sms['msg_part_count'] * user.package.non_masking_national_msg_charge)
                        user.owner_user.local_non_masking_balance -= Decimal(sms['msg_part_count'] * user.package.non_masking_national_msg_charge)
                        if user.local_non_masking_balance<0 or user.owner_user.local_non_masking_balance<0:
                            is_low_balance = True
                    elif user.region_type == 'international':
                        user.internation_non_masking_balance -= Decimal(sms['msg_part_count'] * user.package.non_masking_international_msg_charge)
                        user.owner_user.internation_non_masking_balance -= Decimal(sms['msg_part_count'] * user.package.non_masking_international_msg_charge)
                        if user.internation_non_masking_balance<0 or user.owner_user.internation_non_masking_balance<0:
                            is_low_balance=True
                else:
                    if user.region_type == 'local':
                        user.local_non_masking_message_amount -= sms['msg_part_count']
                        user.owner_user.local_non_masking_message_amount -= sms['msg_part_count']
                        if user.local_non_masking_message_amount<0 or user.owner_user.local_non_masking_message_amount<0:
                            is_low_balance=True
                    elif user.region_type == 'international':
                        user.internation_non_masking_message_amount -= sms['msg_part_count']
                        user.owner_user.internation_non_masking_message_amount -= sms['msg_part_count']
                        if user.internation_non_masking_message_amount<0 or user.owner_user.internation_non_masking_message_amount<0:
                            is_low_balance=True

                if is_low_balance:
                    return False, "You do not have enough balance."
                
                message_sending_process = send_sms_task(sms['receiver'], sms['message'], sms['id'], sms_api_obj.url, sms_api_obj.id)
                # message_sending_process = True
                print("message_sending_process", message_sending_process)
                if message_sending_process:
                    # Cut the Balance or Amount from the Client and Reseller.
                    user.save()
                    user.owner_user.save()
                    is_message_sending_successful=True
                    number_of_sms+=1
                    number_of_sms_count+=sms['msg_part_count']
                    break 
        
        # Update the related counting after the operation.
        balance_log_instance.number_of_sms = number_of_sms
        balance_log_instance.number_of_sms_count = number_of_sms_count
        balance_log_instance.after_operation_balance = user.local_non_masking_message_amount
        balance_log_instance.save()

        if is_message_sending_successful:
            return True, 'Success'
        else:
            return False, 'Failed'
            
    except Exception as e:
        return False, str(e)

process_sms()
