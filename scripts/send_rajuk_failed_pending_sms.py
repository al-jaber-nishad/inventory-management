import os
import sys
import django
from decimal import Decimal

# Set up Django environment
sys.path.append('/home/bluebays/sms.bluebayit.com/')
# sys.path.append('/home/aljaber/projects/SMS-Server/')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils import timezone
from django.utils.timezone import make_aware
from datetime import datetime
from authentication.models import User
from sms.models import SingleSms


from sms.tasks import send_sms_task
from celery import shared_task
from sms.views.sms_views import decrease_user_balance, process_sms_sending
from sms.views.sms_processing import send_sms_processing


@shared_task
def process_failed_sms_task(user_id, sms_list):
    user = User.objects.get(id=user_id)
    for item in sms_list:
        print("item", item)
        is_low_balance = decrease_user_balance(user.id, item['msg_part_count'])
        if is_low_balance:
            print("Balance is low=======================================>")
        process_sms_sending(user.id, sms_list, item['msg_part_count'])

def send_failed_sms_rajuk():
    user = User.objects.get(id=32)
    created_at = make_aware(datetime.strptime("2025-06-25 2:00 AM", "%Y-%m-%d %I:%M %p"))

    sms_object_list = SingleSms.objects.filter(sender=user, is_sent=False, created_at__gte=created_at, status='pending').distinct('receiver', 'message', 'created_at')
    print("sms_object_list", sms_object_list)

    sms_list = []
    for sms in sms_object_list:
        # failed_sms = SingleSms.objects.filter(sender=sms.sender, receiver=sms.receiver, message=sms.message, status='failed', created_at__gte=created_at)
        # if failed_sms.exists() and failed_sms.count() > 1:
        #     continue
        # else:
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

    print("sms list is sent to the processor method")
    # Send to Celery task for processing in the background
    print("sms_list", len(sms_list))
    # process_failed_sms_task(user.id, sms_list)

    send_sms_processing(user.id, sms_list, msg_part_count=None),

    print("failed sms sending done")
    # return JsonResponse({"message": "Failed SMS processing started in background."}, status=202)

send_failed_sms_rajuk()
