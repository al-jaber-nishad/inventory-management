from django.contrib import admin
from django.contrib.auth.models import Group

from .models import *


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
	list_display = [field.name for field in Bank._meta.fields]


@admin.register(PrimaryGroup)
class PrimaryGroupAdmin(admin.ModelAdmin):
	list_display = [field.name for field in PrimaryGroup._meta.fields]


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
	list_display = [field.name for field in Group._meta.fields]


@admin.register(LedgerAccount)
class LedgerAccountAdmin(admin.ModelAdmin):
	list_display = [field.name for field in LedgerAccount._meta.fields]


@admin.register(SubLedgerAccount)
class SubLedgerAccountAdmin(admin.ModelAdmin):
	list_display = [field.name for field in SubLedgerAccount._meta.fields]


@admin.register(PaymentVoucher)
class PaymentVoucherAdmin(admin.ModelAdmin):
	list_display = [field.name for field in PaymentVoucher._meta.fields]


@admin.register(ReceiptVoucher)
class ReceiptVoucherAdmin(admin.ModelAdmin):
	list_display = [field.name for field in ReceiptVoucher._meta.fields]


@admin.register(Contra)
class ContraAdmin(admin.ModelAdmin):
	list_display = [field.name for field in Contra._meta.fields]


@admin.register(AccountLog)
class AccountLogAdmin(admin.ModelAdmin):
	list_display = [field.name for field in AccountLog._meta.fields]
