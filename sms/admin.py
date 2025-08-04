from django.contrib import admin
from sms.models import *


# Register your models here.
@admin.register(SmsAPI)
class SmsAPIAdmin(admin.ModelAdmin):
    list_display = [field.name for field in SmsAPI._meta.fields]
    search_fields = ['name']


@admin.register(AssignSmsAPI)
class AssignSmsAPIAdmin(admin.ModelAdmin):
    list_display = [field.name for field in AssignSmsAPI._meta.fields]
    search_fields = ['user', 'sms_api']


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Package._meta.fields]
    search_fields = ['name']


@admin.register(Sms)
class SmsAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Sms._meta.fields]
    search_fields = ['owner', 'sender']


@admin.register(SingleSms)
class SingleSmsAdmin(admin.ModelAdmin):
    list_display = [field.name for field in SingleSms._meta.fields]
    search_fields = ['sender_ip_address', 'sender__username', 'sender__email', 'gateway_type', 'receiver', 'message']


@admin.register(BalanceLog)
class BalanceLogAdmin(admin.ModelAdmin):
    list_display = [field.name for field in BalanceLog._meta.fields]
    search_fields = ['sender__username', 'sender__email']
