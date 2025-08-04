from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from authentication.models import Country, User
from django.db.models import Count

# Create your models here.


class SmsAPI(models.Model):
    name = models.CharField(max_length=255)
    vendor_name = models.CharField(max_length=255, null=True, blank=True)
    url = models.CharField(max_length=255)
    priority = models.IntegerField(default=0)
    is_deletable = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

    class Meta:
        ordering = ('priority', )

    def __str__(self):
        return f"{self.name}"

    def current_usage_percentage(self):
        total_messages = SingleSms.objects.filter(sender=self.user).count()
        if total_messages == 0:
            return 0
        api_messages = SingleSms.objects.filter(sms_api=self.sms_api, sender=self.user).count()
        return (api_messages / total_messages) * 100


class AssignSmsAPI(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sms_api = models.ForeignKey(SmsAPI, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=False)
    is_shared = models.BooleanField(default=False)
    share_percentage = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}: {self.sms_api.name}"

    def is_eligible(self):
        total_messages = SingleSms.objects.filter(sms_api__isnull=False).count()
        if total_messages == 0:
            return True 

        shared_apis = AssignSmsAPI.objects.filter(user=self.user, is_shared=True).annotate(
            sms_count=Count('sms_api__singlesms')
        )

        # Check if current API has the least count among shared ones
        min_count = shared_apis.aggregate(models.Min('sms_count'))['sms_count__min']
        current_api_count = SingleSms.objects.filter(sms_api=self.sms_api).count()

        if current_api_count <= min_count:
            return True

        return False
    
    def current_usage_percentage(self):
        total_messages = SingleSms.objects.filter(sender=self.user).count()
        if total_messages == 0:
            return 0
        api_messages = SingleSms.objects.filter(sms_api=self.sms_api, sender=self.user).count()
        return (api_messages / total_messages) * 100
    

class Package(models.Model):
    class BillType(models.TextChoices):
        PREPAID = 'prepaid', _('Prepaid')
        POSTPAID_LIMITED = 'postpaid_limited', _('Postpaid Limited')
        POSTPAID_UNLIMITED = 'postpaid_unlimited', _('Postpaid Unlimited')
    name = models.CharField(max_length=50)
    owner_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="package_owner_user", null=True, blank=True)
    bill_type = models.CharField(max_length=20, choices=BillType.choices, default=BillType.PREPAID, null=True, blank=True)
    is_deletable = models.BooleanField(default=True)

    masking_national_msg_charge = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    non_masking_national_msg_charge = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    masking_internation_msg_charge = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    non_masking_internation_msg_charge = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    
    prefix_based = models.BooleanField(default=False)
    masking_prefix_013_charge = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    non_masking_prefix_013_charge = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    masking_prefix_014_charge = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    non_masking_prefix_014_charge = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    masking_prefix_015_charge = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    non_masking_prefix_015_charge = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    masking_prefix_016_charge = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    non_masking_prefix_016_charge = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    masking_prefix_017_charge = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    non_masking_prefix_017_charge = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    masking_prefix_018_charge = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    non_masking_prefix_018_charge = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    masking_prefix_019_charge = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    non_masking_prefix_019_charge = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

    class Meta:
        ordering = ('-id', )

    def __str__(self):
        return f"{self.name}"
	

# class PackageHistory(models.Model):
#     assigned_package = models.ForeignKey(AssignedPackage, on_delete=models.CASCADE)
#     package_user = models.ForeignKey(User, on_delete=models.CASCADE)
#     done_on = models.DateTimeField()
#     done_by_user_id = models.BigIntegerField()
#     action_type = models.SmallIntegerField()
#     action_args = models.CharField(max_length=100)

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
#     updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

#     def __str__(self):
#         return f"{self.assigned_package}: {self.package_user}"

    # sender = models.CharField(max_length=20, null=True, blank=True)
    # cateogry = models.SmallIntegerField()
    # channel = models.SmallIntegerField()
    # is_flash = models.BooleanField(null=True, blank=True)


class Sms(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    sender_ip_address = models.CharField(max_length=255, null=True, blank=True)
    msg_part_count = models.SmallIntegerField(default=1)
    failure_reason = models.CharField(max_length=1000, null=True, blank=True)
    text = models.CharField(max_length=1600, null=True, blank=True)
    receivers = models.TextField(null=True, blank=True)
    receiver_count = models.IntegerField()
    success_count = models.IntegerField()
    fail_count = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

    def __str__(self):
        return f"{self.sender}: {self.success_count}: {self.fail_count}"


class SingleSms(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        FAILED = 'failed', _('Failed')
        SENT = 'sent', _('Sent')
    class SmsType(models.TextChoices):
        INCOMING = 'incoming', _('Incoming')
        OUTGOING = 'outgoing', _('Outgoing')
    class GatewayType(models.TextChoices):
        HTTPS = 'https', _('HTTPS')
        PANEL = 'panel', _('Panel')
    
    # sms = models.ForeignKey(Sms, on_delete=models.RESTRICT, null=True, blank=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    sender_ip_address = models.CharField(max_length=255, null=True, blank=True)
    msg_part_count = models.SmallIntegerField(default=1)
    
    sms_api = models.ForeignKey(SmsAPI, on_delete=models.SET_NULL, null=True, blank=True)
    receiver = models.TextField(null=True, blank=True)
    message = models.CharField(max_length=1600, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, null=True, blank=True)
    sms_type = models.CharField(max_length=20, choices=SmsType.choices, null=True, blank=True)
    gateway_type = models.CharField(max_length=20, choices=GatewayType.choices, null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    failure_reason = models.TextField(null=True, blank=True)
    # response = models.JSONField(null=True, blank=True)
    # retry_count = models.PositiveIntegerField(default=0)

    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

    def __str__(self):
        return f"{self.sender}: {self.receiver}"


# class Schedule(models.Model):
#     name = models.CharField(max_length=50)
#     try_if_failed = models.IntegerField(default=-1)
#     total_try_if_failed = models.IntegerField(default=0)
#     start_on = models.DateTimeField()
#     end_on = models.DateTimeField(default=models.functions.Now)
#     status = models.IntegerField(default=1)
#     created_at = models.DateTimeField(default=models.functions.Now)
#     modified_at = models.DateTimeField(default=models.functions.Now)
#     created_by = models.ForeignKey('User', related_name='created_schedules', on_delete=models.CASCADE)
#     modified_by = models.ForeignKey('User', related_name='modified_schedules', on_delete=models.CASCADE, null=True, blank=True)
#     repeat_every = models.IntegerField(default=-1)
#     ends_after = models.IntegerField(default=-1)
#     repeat_on = models.CharField(max_length=255)
#     is_repeat = models.IntegerField(default=0)
#     repeat_type = models.IntegerField(default=-1)
#     is_deleted = models.BooleanField()
#     sms = models.ForeignKey('Sms', on_delete=models.CASCADE, null=True, blank=True)

# class ScheduleSms(models.Model):
#     sms = models.ForeignKey('Sms', on_delete=models.CASCADE)
#     schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)
#     next_scheduled_date = models.DateTimeField()


class BalanceLog(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    current_balance = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    after_operation_balance = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)

    number_of_sms = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    number_of_sms_count = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

    def __str__(self):
        return f"{self.sender}"