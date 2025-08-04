from email.policy import default
from random import choices
from django.db import models
from django.db.models.fields import BigAutoField
from django.utils import tree
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, AbstractUser
from django.conf import settings
from django.contrib.auth import user_logged_in, user_logged_out

# from rest_framework_simplejwt.tokens import RefreshToken

from phonenumber_field.modelfields import PhoneNumberField

# from sms.models import Package



class Country(models.Model):
     name = models.CharField(max_length=255)
     capital_name = models.CharField(max_length=255, null=True, blank=True)
     country_code = models.CharField(max_length=255, null=True, blank=True)
     country_code2 = models.CharField(max_length=255, null=True, blank=True)
     phone_code = models.CharField(max_length=255, null=True, blank=True)
     currency_code = models.CharField(max_length=255, null=True, blank=True)
     continent_name = models.CharField(max_length=255, null=True, blank=True)
     continent_code = models.CharField(max_length=255, null=True, blank=True)

     created_at = models.DateTimeField(auto_now_add=True)
     updated_at = models.DateTimeField(auto_now=True)

     created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
     updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

     class Meta:
          ordering = ('name',)
          verbose_name_plural = 'Countries'

     def __str__(self):
          return f"{self.name}"
     



class Role(models.Model):
    name = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    
    class Meta:
        ordering = ('-id', )

    def __str__(self):
        return self.name



class UserGroup(models.Model):
    name = models.CharField(max_length=255)
    owner_user = models.ForeignKey('User', on_delete=models.CASCADE, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    
    class Meta:
        ordering = ('-id', )

    def __str__(self):
        return self.name
# class UserManager(BaseUserManager):
# 	def create_user(self, email, username='', first_name='', last_name='', gender='male', password=None, **kwargs):
# 		if not email:
# 			raise ValueError('User must have an email address')
            
# 		user = self.model(
# 			email=self.normalize_email(email),
# 			username=username,
# 			first_name= first_name,
# 			last_name = last_name,
# 			gender = gender,
# 			**kwargs,
# 		)
# 		user.set_password(password)
# 		user.save(using=self._db)
# 		return user

# 	def create_superuser(self, email, username='', first_name='', last_name='', gender='male', password=None, **kwargs):
# 		user = self.create_user(
# 			email= email,
# 			username=username,
# 			first_name= first_name,
# 			last_name = last_name,
# 			gender = gender,
# 			password=password,
# 			**kwargs,
# 		)
# 		user.is_admin = True
# 		user.save(using=self._db)
# 		return user


class User(AbstractUser):
    class Gender(models.TextChoices):
        MALE = 'male', _('Male')
        FEMALE = 'female', _('Female')
        OTHERS = 'others', _('Others')
    class Region(models.TextChoices):
        LOCAL = 'local', _('Local')
        INTERNATIONAL = 'international', _('International')

    company_name = models.CharField(max_length=255, null=True, blank=True)
    
    local_masking_balance = models.DecimalField(default=0, max_digits=20, decimal_places=2, null=True, blank=True)
    local_non_masking_balance = models.DecimalField(default=0, max_digits=20, decimal_places=2, null=True, blank=True)
    local_masking_message_amount = models.IntegerField(default=0)
    local_non_masking_message_amount = models.IntegerField(default=0)
    
    internation_masking_balance = models.DecimalField(default=0, max_digits=20, decimal_places=2, null=True, blank=True)
    internation_non_masking_balance = models.DecimalField(default=0, max_digits=20, decimal_places=2, null=True, blank=True)
    internation_masking_message_amount = models.IntegerField(default=0)
    internation_non_masking_message_amount = models.IntegerField(default=0)

    package = models.ForeignKey('sms.Package', on_delete=models.SET_NULL, null=True, blank=True)
    region_type = models.CharField(max_length=20, choices=Region.choices, null=True, blank=True)

    primary_phone = PhoneNumberField(verbose_name='phone_number', null=True, blank=True, unique=True)
    secondary_phone = PhoneNumberField(null=True, blank=True)

    sender_show_number = models.CharField(max_length=500, null=True, blank=True)
    balance_valid_till = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    owner_user = models.ForeignKey('self', on_delete=models.RESTRICT, null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.RESTRICT, null=True, blank=True)
    user_group = models.ForeignKey(UserGroup, on_delete=models.RESTRICT, null=True, blank=True)

    father_name = models.CharField(max_length=255, null=True, blank=True)
    mother_name = models.CharField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    gender = models.CharField(max_length=6, choices=Gender.choices, default=Gender.MALE)
    date_of_birth = models.DateField(null=True, blank=True)

    profile_picture = models.ImageField(upload_to="users/profile_picture/", null=True, blank=True)
    nid_image = models.ImageField(upload_to="users/nid/", null=True, blank=True)
    nid_no = models.CharField(max_length=32, null=True, blank=True)
    trade_licence_image = models.ImageField(upload_to="users/nid/", null=True, blank=True)
    trade_licence_no = models.CharField(max_length=32, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    
    # USERNAME_FIELD = 'username'

    class Meta:
        ordering = ('-id', )

    def __str__(self):
        return f"{self.email}"



class ContactGroup(models.Model):
    name = models.CharField(max_length=30)
    local_contact_count = models.IntegerField(default=0)
    international_contact_count = models.IntegerField(default=0)

    owner_user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Contact Group'
        ordering = ('-id',)

    def __str__(self):
        return f"{self.name}"



class Contact(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    contact_no = models.CharField(max_length=20)
    owner_user = models.ForeignKey(User, on_delete=models.CASCADE)
    contact_group = models.ForeignKey(ContactGroup, on_delete=models.RESTRICT, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Contacts'
        ordering = ('-id',)

    def __str__(self):
        return f"{self.name}"


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        DEBIT = 'Debit', _('Debit')
        CREDIT = 'Credit', _('Credit')
    recharged_to = models.ForeignKey(User, related_name='recharged_to', on_delete=models.CASCADE, null=True, blank=True)
    recharged_by = models.ForeignKey(User, related_name='recharged_by', on_delete=models.CASCADE, null=True, blank=True)
    balance = models.DecimalField(default=0, max_digits=20, decimal_places=2, null=True, blank=True)
    message_amount = models.IntegerField(null=True, blank=True)

    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices, default=TransactionType.CREDIT)
    balance_type = models.CharField(max_length=255, null=True, blank=True)
    region_type = models.CharField(max_length=1255, null=True, blank=True)
    balance_valid_till = models.DateField(null=True, blank=True)
    remakrs = models.CharField(max_length=255, null=True, blank=True)

    respective_package_price = models.DecimalField(default=0, max_digits=20, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Transactions'
        ordering = ('-id',)

    def __str__(self):
        return f"{self.recharged_by.username}: {self.recharged_to.username}"


class DeveloperApi(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    api_key = models.CharField(max_length=255, null=True, blank=True)
    api_url = models.CharField(max_length=510, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Developer APIs'
        ordering = ('-id',)

    def __str__(self):
        return f"{self.user.username}"





class LoginHistory(models.Model):
     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT)

     ip_address = models.CharField(max_length=255, null=True, blank=True)
     mac_address = models.CharField(max_length=255, null=True, blank=True)
     g_location_info = models.CharField(max_length=500, null=True, blank=True)
     is_device_blocked = models.BooleanField(default=False)

     login_time = models.DateTimeField(null=True, blank=True)
     logout_time = models.DateTimeField(null=True, blank=True)

     status = models.CharField(max_length=255, null=True, blank=True)

     created_at = models.DateTimeField(auto_now_add=True)
     updated_at = models.DateTimeField(auto_now=True)

     created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)
     updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL, related_name="+", null=True, blank=True)

     class Meta:
          verbose_name_plural = 'LoginHistories'
          ordering = ('-id',)

     def __str__(self):
          return f"{self.user.username}"




class ActivityLog(models.Model):
    activity_module = models.CharField(max_length=255, null=True, blank=True)
    activity_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='user_activitylogs', null=True)
    comment = models.CharField(max_length=5000, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'ActivityLogs'
        ordering = ('-id',)

    def __str__(self):
        return f"{self.activity_type.name}"