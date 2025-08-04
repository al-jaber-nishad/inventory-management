from dataclasses import field
from django.core.mail import send_mail
from django.conf import settings

from .models import User

from sequences import get_next_value

import random
import requests



def get_unique_username(name: str) -> str:
    _name = "".join(name.split(' '))
    username =  str(_name) + str(get_next_value('sequential_user'))
    print('unique username: ', username)
    return username




def get_username(name):
    username = "".join(name.split(' ')).lower()
    if not User.objects.filter(username=username).exists():
        return username
    else:
        random_username = username + str(random.randint(0, 1000))
        return get_unique_username(random_username)




def send_phone_otp(primary_phone, otp):
    primary_phone = str(primary_phone)[-11:]
    print("sms phone: ", primary_phone)

    msg = f"From,\ncashconnectbd.com\nYour OTP is {otp}"
    url = f"https://*server*/httpapi/sendsms?userId=ID&password=password&smsText={msg}&commaSeperatedReceiverNumbers={primary_phone}&nameToShowAsSender=03590002174"
    res = requests.get(url)

    print('res: ', res)
    print('res.json(): ', res.json())

    return res.json()




def send_verification_email(to_email, auth_token):
    sub  = f"Account Verification Email"
    msg = f"Please click the link to verify your account: {str(settings.BACKEND_DOMAIN)+'/verify/'+str(auth_token)}"
    sender = settings.EMAIL_HOST_USER
    try:
       mail_res = send_mail(sub, msg, sender, [to_email,], fail_silently=False)
       print('mail_res: ', mail_res)
    except Exception as e:
        print('mail exception: ', e)
        pass




def pop_user_secretdata(dictt: dict) -> None:
    fields = ['email_token', 'phone_otp', 'user_type', 'auth_provider', 'is_email_verified', 'is_primary_phone_verified', 'is_active', 'is_admin']
    for field in fields:
        try:
            dictt.pop(field)
        except KeyError:
            pass



