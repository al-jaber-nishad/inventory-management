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
