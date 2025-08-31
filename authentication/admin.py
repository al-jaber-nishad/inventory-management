from django.contrib import admin
from django.contrib.auth.models import Group

from .models import *


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
	list_display = [field.name for field in User._meta.fields]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
	list_display = [field.name for field in Role._meta.fields]


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
	list_display = [field.name for field in Country._meta.fields]



@admin.register(UserGroup)
class UserGroupAdmin(admin.ModelAdmin):
	list_display = [field.name for field in UserGroup._meta.fields]



@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
	list_display = [field.name for field in Transaction._meta.fields]



@admin.register(DeveloperApi)
class DeveloperApiAdmin(admin.ModelAdmin):
	list_display = [field.name for field in DeveloperApi._meta.fields]



@admin.register(ContactGroup)
class ContactGroupAdmin(admin.ModelAdmin):
	list_display = [field.name for field in ContactGroup._meta.fields]



@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
	list_display = [field.name for field in Contact._meta.fields]


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
	list_display = [field.name for field in Supplier._meta.fields]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
	list_display = [field.name for field in Customer._meta.fields]
