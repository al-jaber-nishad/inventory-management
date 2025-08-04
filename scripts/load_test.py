import os
import sys
import django
from decimal import Decimal

# Set up Django environment
# sys.path.append('/home/bluebays/sms.bluebayit.com/')
sys.path.append('/home/aljaber/projects/SMS-Server/')
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



def main():
    user = User.objects.get(id=26)
    count = 10000

    messages = []
    for i in range(count):
        messages.append(SingleSms(
            sender=user,
            message=f"Load Test #{i+1}",
            receiver=f"0160000{i%10000:04d}",
            status=SingleSms.Status.PENDING,
            sms_type=SingleSms.SmsType.OUTGOING,
            msg_part_count=1,
            gateway_type=SingleSms.GatewayType.PANEL,
            sender_ip_address="127.0.0.1"
        ))

    created = SingleSms.objects.bulk_create(messages, batch_size=1000)
    sms_list = [{
        "id": sms.id,
        "sender": sms.sender_id,
        "receiver": sms.receiver,
        "message": sms.message,
        "msg_part_count": sms.msg_part_count,
        "status": sms.status,
        "sms_type": sms.sms_type,
        "gateway_type": sms.gateway_type,
        "sender_ip_address": sms.sender_ip_address
    } for sms in created]

    print("sms_list", len(sms_list))
    process_sms_sending.delay(user.id, sms_list, count)

main()