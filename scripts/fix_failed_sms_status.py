import os
import sys
import django
from decimal import Decimal

# Set up Django environment
sys.path.append('/home/bluebays/sms.bluebayit.com/')
# sys.path.append('/home/aljaber/projects/SMS-Server/')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()


from sms.models import SingleSms
from django.utils.timezone import make_aware
from datetime import datetime


try:
    # Fetch the failed SMS records
    sms_list = SingleSms.objects.filter(created_at__date='2025-03-20', status='pending', is_sent=False)

    # Update each SMS record
    for sms in sms_list:
        print("sms", sms)
        sms.status = 'success'
        sms.is_sent = True
        sms.sent_at = sms.created_at  # If sent_at is a DateTimeField, this will work. If not, convert accordingly.
        sms.save()

    print(f"Updated {sms_list.count()} records successfully!")
except Exception as e:
    print(f"An error occurred: {e}")