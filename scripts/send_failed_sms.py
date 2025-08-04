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
from sms.models import SingleSms, AssignSmsAPI, SmsAPI
from sms.tasks import send_sms_task



def process_sms():
    user = User.objects.get(id=32)
    is_prefix_based = user.package.prefix_based

    assigned_sms_api = AssignSmsAPI.objects.filter(user=user.owner_user).order_by('priority')
    if not assigned_sms_api.exists():
        sms_api_list = SmsAPI.objects.all().order_by('priority')
    else:
        sms_api_list = assigned_sms_api.select_related('sms_api').order_by('priority')

    print("sms_api_list", sms_api_list)
    is_message_sending_successful = False


    sms_list = SingleSms.objects.filter(sender=user, is_sent=False)
    for sms in sms_list:
        print("sms", sms.id)
        for api in sms_api_list:
            sms_api_obj = api.sms_api if assigned_sms_api.exists() else api
            
            # if hasattr(api, 'is_shared') and api.is_shared:
            #     if not api.is_eligible():
            #         continue

            print("Finally used api", api)
            is_low_balance = False
            # if is_prefix_based:
            #     if user.region_type == 'local':
            #         user.local_non_masking_balance -= Decimal(sms.number_of_message * user.package.non_masking_national_msg_charge)
            #         user.owner_user.local_non_masking_balance -= Decimal(sms.number_of_message * user.package.non_masking_national_msg_charge)
            #         if user.local_non_masking_balance<0 or user.owner_user.local_non_masking_balance<0:
            #             is_low_balance = True
            #     elif user.region_type == 'international':
            #         user.internation_non_masking_balance -= Decimal(sms.number_of_message * user.package.non_masking_international_msg_charge)
            #         user.owner_user.internation_non_masking_balance -= Decimal(sms.number_of_message * user.package.non_masking_international_msg_charge)
            #         if user.internation_non_masking_balance<0 or user.owner_user.internation_non_masking_balance<0:
            #             is_low_balance=True
            # else:
            #     if user.region_type == 'local':
            #         user.local_non_masking_message_amount -= sms.number_of_message
            #         user.owner_user.local_non_masking_message_amount -= sms.number_of_message
            #         if user.local_non_masking_message_amount<0 or user.owner_user.local_non_masking_message_amount<0:
            #             is_low_balance=True
            #     elif user.region_type == 'international':
            #         user.internation_non_masking_message_amount -= sms.number_of_message
            #         user.owner_user.internation_non_masking_message_amount -= sms.number_of_message
            #         if user.internation_non_masking_message_amount<0 or user.owner_user.internation_non_masking_message_amount<0:
            #             is_low_balance=True

            if is_low_balance:
                return False, "You do not have enough balance."
            
            message_sending_process = send_sms_task(sms.receiver, sms.message, sms.id, sms_api_obj.url, sms_api_obj.id)
            print("message_sending_process", message_sending_process)
            if message_sending_process:
                # Cut the Balance or Amount from the Client and Reseller.
                # user.save()
                # user.owner_user.save()
                break 

process_sms()