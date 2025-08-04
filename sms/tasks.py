import requests
import re
from celery import shared_task
from sms.models import SingleSms, SmsAPI
from time import sleep
from django.core.cache import cache
from django.utils import timezone
import urllib.parse
from commons.constants import (
    elitbuzz_api_name,
    jamanit_api_name,
    durbarsms_api_name,
    revesms_api_name,
    rtcom_api_name
)



# Define the error code mapping
ELITBUZZ_ERROR_CODES = {
    "1002": "Sender Id/Masking Not Found",
    "1003": "API Not Found",
    "1004": "SPAM Detected",
    "1005": "Internal Error",
    "1006": "Internal Error",
    "1007": "Balance Insufficient",
    "1008": "Message is empty",
    "1009": "Message Type Not Set (text/unicode)",
    "1010": "Invalid User & Password",
    "1011": "Invalid User Id",
    "1012": "Invalid Number",
    "1013": "API limit error",
    "1014": "No matching template",
    "1015": "SMS Content Validation Fails",
    "1016": "IP address not allowed!!",
    "1019": "Sms Purpose Missing",
}

JAMANIT_ERROR_CODES = {
    "1001": "Wrong Api Key",
    "1002": "Wrong Sender ID",
    "1003": "Type must be text or unicode",
    "1004": "Only GET and POST Methods Allow",
    "1005": "You can't send sms to this prefix because of prefix inactivity.",
    "1006": "Insufficient Balance",
    "1007": "Please use country code (88)",
}

def is_english(text):
    return bool(re.match(r'^[\x00-\x7F]*$', text))


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def send_sms_task(self, phone_number, message, single_sms_id, sms_api, sms_api_id):
    single_sms = SingleSms.objects.get(id=single_sms_id)

    # Fetch sms api from cache or get the object
    sms_api_id_obj = f'sms_api_{sms_api_id}'
    sms_api_obj = cache.get(sms_api_id_obj)
    
    if sms_api_obj is None:
        sms_api_obj = SmsAPI.objects.get(id=sms_api_id)
        cache.set(sms_api_id_obj, sms_api_obj, timeout=1200)
        print("Queryset fetched from DB and cached.")

    unicode_message = urllib.parse.quote_plus(message)
    
    # Change the text_type of message if the sms_api is from RT Communications
    if sms_api_obj.vendor_name == rtcom_api_name:
        if not is_english(message):
            sms_api = sms_api.replace("{text_type}", "unicode")
        else:
            sms_api = sms_api.replace("{text_type}", "text")
    
    # api_url = f"http://45.120.38.242/api/sendsms?api_key=01816255499.AdT5bzRqBnMdsvfi5g&type=text&phone=880{phone_number}&senderid=8809604903051&message={message}"

    sms_api = sms_api.replace("{phone_number}", str(phone_number))
    sms_api = sms_api.replace("{message}", str(unicode_message))
    
    now = timezone.localtime(timezone.now())
    failure_reason = ''
    failure_text = None
    response_json = None
    is_message_sent = False

    try:
        response = requests.get(sms_api)
        response_text = response.text
        response_json = response.json()
    except requests.RequestException as e:
        status = SingleSms.Status.FAILED
        failure_text = str(e)
        failure_reason = str(e)

    if sms_api_obj.vendor_name == rtcom_api_name and response_json:
        response_code = response_json.get("response", {}).get("code")
        response_message = response_json.get("response", {}).get("message", "Unknown Error")

        if response_code == 200 and response_message == "Success":
            single_sms.status = SingleSms.Status.SENT
            single_sms.failure_reason = ''
            single_sms.is_sent = True
            single_sms.sent_at = now
            single_sms.sms_api=sms_api_obj
            single_sms.save()

            is_message_sent = True 
        else:
            single_sms.status = SingleSms.Status.FAILED
            single_sms.failure_reason = response_message
            single_sms.save()

            is_message_sent = False
            failure_text = response_message

    elif sms_api_obj.vendor_name == elitbuzz_api_name:
        # Check if the response contains a success message
        if "SMS SUBMITTED" in response_text:
            single_sms.status = SingleSms.Status.SENT
            single_sms.failure_reason = ''
            single_sms.is_sent = True
            single_sms.sent_at = now
            single_sms.sms_api=sms_api_obj
            single_sms.save()

            is_message_sent = True            
        else:
            # If not, find the error code in the response text
            for error_code, error_message in ELITBUZZ_ERROR_CODES.items():
                if error_code in response_text:
                    # Update the SingleSms object with the failure reason
                    single_sms.status = SingleSms.Status.FAILED
                    single_sms.failure_reason = error_message
                    single_sms.save()

                    is_message_sent = False
                    failure_text = error_message
    
    elif sms_api_obj.vendor_name == jamanit_api_name:
        if response.status_code == 200 and '"status_code":200' in response_text:
            single_sms.status = SingleSms.Status.SENT
            single_sms.failure_reason = ''
            single_sms.is_sent = True
            single_sms.sent_at = now
            single_sms.sms_api=sms_api_obj
            single_sms.save()

            is_message_sent = True 
        else:
            for error_code, error_message in JAMANIT_ERROR_CODES.items():
                if error_code in response_text:
                    single_sms.status = SingleSms.Status.FAILED
                    single_sms.failure_reason = error_message
                    single_sms.save()

                    is_message_sent = False
                    failure_text = error_message

            single_sms.status = SingleSms.Status.FAILED
            single_sms.save()

            is_message_sent = False
            failure_text = failure_reason
    
    elif sms_api_obj.vendor_name == durbarsms_api_name and response_json:
        if not response_json.get("isError") and response_json.get("message") == "Success!":
            single_sms.status = SingleSms.Status.SENT
            single_sms.failure_reason = ''
            single_sms.is_sent = True
            single_sms.sent_at = now
            single_sms.sms_api=sms_api_obj
            single_sms.save()

            is_message_sent = True 
        else:
            single_sms.status = SingleSms.Status.FAILED
            single_sms.failure_reason = response_json.get("message")
            single_sms.save()

            is_message_sent = False
            failure_text = response_json.get("message")
        
    elif sms_api_obj.vendor_name == revesms_api_name and response_json:
        response_status = response_json.get("Status")
        response_text = response_json.get("Text", "Unknown Error")

        if response_status == "0":
            single_sms.status = SingleSms.Status.SENT
            single_sms.failure_reason = ''
            single_sms.is_sent = True
            single_sms.sent_at = now
            single_sms.sms_api=sms_api_obj
            single_sms.save()

            is_message_sent = True 
        else:
            single_sms.status = SingleSms.Status.FAILED
            single_sms.failure_reason = response_text
            single_sms.save()

            is_message_sent = False
            failure_text = response_text
        
    print(f"is_message_sent: {is_message_sent}")
    
    if not is_message_sent:
        # Create the failed SingleSMS that will be shown to Reseller and Admin to show the failure reason properly
        SingleSms.objects.create(
            sender=single_sms.sender,
            sender_ip_address=single_sms.sender_ip_address,
            message=single_sms.message,
            msg_part_count=single_sms.msg_part_count,
            receiver=single_sms.receiver,
            sms_api=sms_api_obj,
            sms_type=SingleSms.SmsType.OUTGOING,
            status=SingleSms.Status.FAILED,
            gateway_type=single_sms.gateway_type,
            is_sent=False,
            failure_reason=failure_text
        )

        # Retry logic
        raise self.retry(
            countdown=10 * (self.request.retries + 1),
            exc=Exception(f"SMS sending failed for {phone_number}")
        )

    return is_message_sent
    
    # print("single_sms", single_sms, single_sms.is_sent, single_sms.sms_api, single_sms.status)
