from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from utils.base_model import BaseModel

# Create your models here.

class Bank(BaseModel):
    name =  models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        ordering = ['-id',]
        
    def __str__(self):
        return f"{self.name}"       



class PrimaryGroup(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    is_deletable = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'PrimaryGroups'
        ordering = ['-id',]

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        self.name = self.name.title()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_deletable == False:
            raise ValidationError("Primary group is not deletable!")
        else:
            super().delete(*args, **kwargs)




class Group(BaseModel):
    name = models.CharField(max_length=200, unique=True)

    head_group = models.ForeignKey('self', on_delete=models.RESTRICT, null=True, blank=True, related_name='children')
    head_primarygroup = models.ForeignKey(PrimaryGroup, on_delete=models.RESTRICT, null=True, blank=True)

    is_deletable = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ['-id',]

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        self.name = self.name.title()
        if not self.head_group and not self.head_primarygroup:
            raise ValidationError('Must provide either head_group_self or head_group_primarygroup.')
        if self.head_group and self.head_primarygroup:
            raise ValidationError('Select head_group_self or head_group_primarygroup, but not both.')
        super().save(*args, **kwargs)
    


class LedgerAccount(BaseModel):

    class BalanceType(models.TextChoices):
        CREDITORS = 'creditors', _('Creditors')
        DEBTORS = 'debtors', _('Debtors')

    name = models.CharField(max_length=100, unique=True)
    ledger_type = models.CharField(max_length=30, null=True, blank=True)
    reference_id = models.CharField(max_length=255, null=True, blank=True)
    details =  models.CharField(max_length=255, null=True, blank=True)
    head_group = models.ForeignKey(Group, on_delete=models.RESTRICT, null=True, blank=True)
    head_primarygroup = models.ForeignKey(PrimaryGroup, on_delete=models.RESTRICT, null=True, blank=True)
    
    amount = models.DecimalField(default=0, max_digits=50, decimal_places=2,blank=True)
    note = models.TextField(null=True, blank=True)

    is_deletable = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'LedgerAccounts'
        ordering = ['-id',]

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        self.name = self.name.title()
        if self.ledger_type:
            self.ledger_type = self.ledger_type.replace(' ', '_').lower()
        super().save(*args, **kwargs)


class SubLedgerAccount(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'SubLedgerAccounts'
        ordering = ['-id',]

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        self.name = self.name.title()
        super().save(*args, **kwargs)




class PaymentVoucher(BaseModel):
    class Status(models.TextChoices):
        NULL = 'null', _('null')
        UPDATE_PENDING = 'update_pending', _('update_pending')
        DELETE_PENDING = 'delete_pending', _('delete_pending')
        UPDATE_APPROVED = 'update_approved', _('update_approved')
        DELETE_APPROVED = 'delete_approved', _('delete_approved')
        UPDATE_CANCELED = 'update_canceled', _('update_canceled')
        DELETE_CANCELED = 'delete_canceled', _('delete_canceled')
    ledger = models.ForeignKey(LedgerAccount, on_delete=models.RESTRICT, related_name='paymentvoucher')
    sub_ledger = models.ForeignKey(SubLedgerAccount, on_delete=models.RESTRICT, related_name='paymentvoucher', null=True, blank=True)

    is_post_date = models.BooleanField(default=False, null=True, blank=True)
    cheque_no = models.CharField(max_length=255, null=True, blank=True)
    payorder_no = models.CharField(max_length=255, null=True, blank=True)
    cheque_date =  models.DateField(null=True, blank=True)
    is_cheque = models.CharField(max_length=255, null=True, blank=True)

    inst_no = models.CharField(max_length=255, null=True, blank=True)
    bank_name =  models.ForeignKey(Bank, on_delete=models.CASCADE, null=True, blank=True)
    pdc_note = models.CharField(max_length=255, null=True, blank=True)
    pdc_type = models.CharField(max_length=255, null=True, blank=True)
    remarks = models.CharField(max_length=255, null=True, blank=True)
    favouring_name = models.CharField(max_length=255, null=True, blank=True)
    debit_amount = models.DecimalField(default=0, max_digits=20, decimal_places=2, blank=True)
    credit_amount = models.DecimalField(default=0, max_digits=20, decimal_places=2, blank=True)

    bill_no = models.IntegerField(default=0, null=True, blank=True)
    bank_or_cash = models.BooleanField(default=False, null=True, blank=True)
    balance = models.IntegerField(default=0, null=True, blank=True)
    
    invoice_no = models.CharField(max_length=255, null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    file = models.FileField(upload_to='account/PaymentVoucherFile/', null=True, blank=True)
    details = models.TextField(null=True, blank=True)

    update_status = models.CharField(max_length=15, choices=Status.choices, default=Status.NULL)

    class Meta:
        verbose_name_plural = 'PaymentVouchers'
        ordering = ['-id',]

    def __str__(self):
        return f"{self.passenger.passenger_name}"




class ReceiptVoucher(BaseModel):
    class Status(models.TextChoices):
        NULL = 'null', _('null')
        UPDATE_PENDING = 'update_pending', _('update_pending')
        DELETE_PENDING = 'delete_pending', _('delete_pending')
        UPDATE_APPROVED = 'update_approved', _('update_approved')
        DELETE_APPROVED = 'delete_approved', _('delete_approved')
        UPDATE_CANCELED = 'update_canceled', _('update_canceled')
        DELETE_CANCELED = 'delete_canceled', _('delete_canceled')
    ledger = models.ForeignKey(LedgerAccount, on_delete=models.RESTRICT, related_name='ledger_receiptvoucher')
    sub_ledger = models.ForeignKey(SubLedgerAccount, on_delete=models.RESTRICT, related_name='receiptvoucher', null=True, blank=True)    
    cheque_no = models.CharField(max_length=255, null=True, blank=True)
    payorder_no = models.CharField(max_length=255, null=True, blank=True)
    cheque_date =  models.DateField(null=True, blank=True)
    is_cheque = models.CharField(max_length=255, null=True, blank=True)

    inst_no = models.CharField(max_length=255, null=True, blank=True)
    bank_name =  models.ForeignKey(Bank, on_delete=models.CASCADE, null=True, blank=True)
    pdc_note = models.CharField(max_length=255, null=True, blank=True)
    pdc_type = models.CharField(max_length=255, null=True, blank=True)
    remarks = models.CharField(max_length=255, null=True, blank=True)
    favouring_name = models.CharField(max_length=255, null=True, blank=True)
    debit_amount = models.DecimalField(default=0, max_digits=20, decimal_places=2, blank=True)
    credit_amount = models.DecimalField(default=0, max_digits=20, decimal_places=2, blank=True)
    bill_no = models.IntegerField(default=0, null=True, blank=True)
    bank_or_cash = models.BooleanField(default=False, null=True, blank=True)
    balance = models.IntegerField(default=0, null=True, blank=True)
    
    invoice_no = models.CharField(max_length=255, null=True, blank=True)
    receipt_date = models.DateField(null=True, blank=True)
    file = models.FileField(upload_to='account/ReceiptVoucherFile/', null=True, blank=True)
    details = models.TextField(null=True, blank=True)

    update_status = models.CharField(max_length=15, choices=Status.choices, default=Status.NULL)

    class Meta:
        verbose_name_plural = 'ReceiptVouchers'
        ordering = ['-id',]

    def __str__(self):
        return f"{self.id}"



class Contra(BaseModel):
    class Status(models.TextChoices):
        NULL = 'null', _('null')
        UPDATE_PENDING = 'update_pending', _('update_pending')
        DELETE_PENDING = 'delete_pending', _('delete_pending')
        UPDATE_APPROVED = 'update_approved', _('update_approved')
        DELETE_APPROVED = 'delete_approved', _('delete_approved')
        UPDATE_CANCELED = 'update_canceled', _('update_canceled')
        DELETE_CANCELED = 'delete_canceled', _('delete_canceled')
    
    ledger = models.ForeignKey(LedgerAccount, on_delete=models.RESTRICT, related_name='contras')
    cheque_no = models.CharField(max_length=255, null=True, blank=True)
    payorder_no = models.CharField(max_length=255, null=True, blank=True)
    bank_name =  models.ForeignKey(Bank, on_delete=models.CASCADE, null=True, blank=True)
    cheque_date =  models.DateField(null=True, blank=True)
    
    bill_no = models.IntegerField(default=0, null=True, blank=True)
    bank_or_cash = models.BooleanField(default=False, null=True, blank=True)
    balance = models.IntegerField(default=0, null=True, blank=True)

    invoice_no = models.CharField(max_length=255, null=True, blank=True)

    debit_amount = models.DecimalField(default=0, max_digits=20, decimal_places=2, blank=True)
    credit_amount = models.DecimalField(default=0, max_digits=20, decimal_places=2, blank=True)
    contra_date = models.DateTimeField(null=True, blank=True)
    details = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Contras'
        ordering = ['-id',]

    def __str__(self):
        return str(self.id)


class AccountLog(BaseModel):
    ledger = models.ForeignKey(LedgerAccount, on_delete=models.RESTRICT, related_name='account_logs', null=True, blank=True)
    sub_ledger = models.ForeignKey(SubLedgerAccount, on_delete=models.RESTRICT, related_name='account_logs', null=True, blank=True)
    reference_no = models.CharField(max_length=255, null=True, blank=True)
    log_type = models.CharField(max_length=20, null=True, blank=True)
    debit_amount = models.DecimalField(default=0, max_digits=20, decimal_places=2, null=True, blank=True)
    credit_amount = models.DecimalField(default=0, max_digits=20, decimal_places=2, null=True, blank=True)
    log_date = models.DateTimeField(null=True, blank=True)
    details = models.TextField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'AccountLogs'
        ordering = ['-id',]

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
