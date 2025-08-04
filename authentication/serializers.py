from django.contrib.auth import get_user_model
from django.db.models import fields
from django_currentuser.middleware import (get_current_authenticated_user, get_current_user)
from rest_framework import serializers
# from rest_framework_simplejwt.tokens import RefreshToken

from authentication.models import *

# User = get_user_model()



class RoleMinimalListSerializer(serializers.ModelSerializer):
	class Meta:
		model = Role
		fields = ['id', 'name']




# for customized admin panel
class AdminUserMinimalListSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = ['id', 'email', 'first_name', 'last_name', 'username', 'primary_phone', 'secondary_phone', 'image', 'street_address_one']



class RoleListSerializer(serializers.ModelSerializer):
	created_by = serializers.SerializerMethodField()
	updated_by = serializers.SerializerMethodField()
	class Meta:
		model = Role
		fields = '__all__'
		extra_kwargs = {
			'created_at':{
				'read_only': True,
			},
			'updated_at':{
				'read_only': True,
			},
			'created_by':{
				'read_only': True,
			},
			'updated_by':{
				'read_only': True,
			},
		}
		
	def get_created_by(self, obj):
		return obj.created_by.email if obj.created_by else obj.created_by
		
	def get_updated_by(self, obj):
		return obj.updated_by.email if obj.updated_by else obj.updated_by




class RoleSerializer(serializers.ModelSerializer):
	class Meta:
		model = Role
		fields = '__all__'
		extra_kwargs = {
			'created_at':{
				'read_only': True,
			},
			'updated_at':{
				'read_only': True,
			},
			'created_by':{
				'read_only': True,
			},
			'updated_by':{
				'read_only': True,
			},
		}
		
	def create(self, validated_data):
		modelObject = super().create(validated_data=validated_data)
		user = get_current_authenticated_user()
		if user is not None:
			modelObject.created_by = user
		modelObject.save()
		return modelObject

	def update(self, instance, validated_data):
		modelObject = super().update(instance=instance, validated_data=validated_data)
		user = get_current_authenticated_user()
		if user is not None:
			modelObject.updated_by = user
		modelObject.save()
		return modelObject



class ContactGroupListSerializer(serializers.ModelSerializer):
	created_by = serializers.SerializerMethodField()
	updated_by = serializers.SerializerMethodField()
	class Meta:
		model = ContactGroup
		fields = '__all__'
		extra_kwargs = {
			'created_at':{
				'read_only': True,
			},
			'updated_at':{
				'read_only': True,
			},
			'created_by':{
				'read_only': True,
			},
			'updated_by':{
				'read_only': True,
			},
		}
		
	def get_created_by(self, obj):
		return obj.created_by.email if obj.created_by else obj.created_by
		
	def get_updated_by(self, obj):
		return obj.updated_by.email if obj.updated_by else obj.updated_by




class ContactGroupSerializer(serializers.ModelSerializer):
	class Meta:
		model = ContactGroup
		fields = '__all__'
		extra_kwargs = {
			'created_at':{
				'read_only': True,
			},
			'updated_at':{
				'read_only': True,
			},
			'created_by':{
				'read_only': True,
			},
			'updated_by':{
				'read_only': True,
			},
		}
		
	def create(self, validated_data):
		modelObject = super().create(validated_data=validated_data)
		user = get_current_authenticated_user()
		if user is not None:
			modelObject.created_by = user
		modelObject.save()
		return modelObject

	def update(self, instance, validated_data):
		modelObject = super().update(instance=instance, validated_data=validated_data)
		user = get_current_authenticated_user()
		if user is not None:
			modelObject.updated_by = user
		modelObject.save()
		return modelObject





class ContactListSerializer(serializers.ModelSerializer):
	created_by = serializers.SerializerMethodField()
	updated_by = serializers.SerializerMethodField()
	class Meta:
		model = Contact
		fields = '__all__'
		extra_kwargs = {
			'created_at':{
				'read_only': True,
			},
			'updated_at':{
				'read_only': True,
			},
			'created_by':{
				'read_only': True,
			},
			'updated_by':{
				'read_only': True,
			},
		}
		
	def get_created_by(self, obj):
		return obj.created_by.email if obj.created_by else obj.created_by
		
	def get_updated_by(self, obj):
		return obj.updated_by.email if obj.updated_by else obj.updated_by




class ContactSerializer(serializers.ModelSerializer):
	class Meta:
		model = Contact
		fields = '__all__'
		extra_kwargs = {
			'created_at':{
				'read_only': True,
			},
			'updated_at':{
				'read_only': True,
			},
			'created_by':{
				'read_only': True,
			},
			'updated_by':{
				'read_only': True,
			},
		}
		
	def create(self, validated_data):
		modelObject = super().create(validated_data=validated_data)
		user = get_current_authenticated_user()
		if user is not None:
			modelObject.created_by = user
		modelObject.save()
		return modelObject

	def update(self, instance, validated_data):
		modelObject = super().update(instance=instance, validated_data=validated_data)
		user = get_current_authenticated_user()
		if user is not None:
			modelObject.updated_by = user
		modelObject.save()
		return modelObject




# for customized admin panel 
class AdminUserListSerializer(serializers.ModelSerializer):
	role = RoleMinimalListSerializer()
	thana = serializers.SerializerMethodField()
	city = serializers.SerializerMethodField()
	country = serializers.SerializerMethodField()
	created_by = serializers.SerializerMethodField()
	updated_by = serializers.SerializerMethodField()

	class Meta:
		model = User
		exclude = ['auth_provider', 'email_token', 'phone_otp', 'is_active', 'is_admin', 'is_email_verified', 'is_primary_phone_verified']
		extra_kwargs = {
			'password': {
				'write_only': True,
				'required': False,
			},
			'created_at':{
				'read_only': True,
			},
			'updated_at':{
				'read_only': True,
			},
			'created_by':{
				'read_only': True,
			},
			'updated_by':{
				'read_only': True,
			},
		}

	def get_thana(self, obj):
		return obj.thana.name if obj.thana else obj.thana
	
	def get_city(self, obj):
		return obj.city.name if obj.city else obj.city
	
	def get_country(self, obj):
		return obj.country.name if obj.country else obj.country
	
	def get_created_by(self, obj):
		return obj.created_by.email if obj.created_by else obj.created_by
		
	def get_updated_by(self, obj):
		return obj.updated_by.email if obj.updated_by else obj.updated_by




# for customized admin panel
class AdminUserListSerializerForGeneralUse(serializers.ModelSerializer):
	thana = serializers.SerializerMethodField()
	city = serializers.SerializerMethodField()
	country = serializers.SerializerMethodField()
	created_by = serializers.SerializerMethodField()
	updated_by = serializers.SerializerMethodField()

	class Meta:
		model = User
		exclude = ['role', 'auth_provider', 'email_token', 'phone_otp', 'is_active', 'is_admin', 'is_email_verified', 'is_primary_phone_verified']
		extra_kwargs = {
			'password': {
				'write_only': True,
				'required': False,
			},
			'created_at':{
				'read_only': True,
			},
			'updated_at':{
				'read_only': True,
			},
			'created_by':{
				'read_only': True,
			},
			'updated_by':{
				'read_only': True,
			},
		}

	def get_thana(self, obj):
		return obj.thana.name if obj.thana else obj.thana
	
	def get_city(self, obj):
		return obj.city.name if obj.city else obj.city
	
	def get_country(self, obj):
		return obj.country.name if obj.country else obj.country
	
	def get_created_by(self, obj):
		return obj.created_by.email if obj.created_by else obj.created_by
		
	def get_updated_by(self, obj):
		return obj.updated_by.email if obj.updated_by else obj.updated_by




# for customized admin panel
class AdminUserSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		exclude = ['role', 'auth_provider', 'is_active', 'is_admin', 'is_email_verified', 'is_primary_phone_verified']
		extra_kwargs = {
			'password': {
				'write_only': True,
				'required': False,
			},
			'phone_otp': {
				'write_only': True,
				'required': False,
			},
			'email_token': {
				'write_only': True,
				'required': False,
			},
			'created_at':{
				'read_only': True,
			},
			'updated_at':{
				'read_only': True,
			},
			'created_by':{
				'read_only': True,
			},
			'updated_by':{
				'read_only': True,
			},
		}

	def create(self, validated_data):
		modelObject = super().create(validated_data=validated_data)
		modelObject.set_password(validated_data["password"])
		user = get_current_authenticated_user()
		if user is not None:
			modelObject.created_by = user
		modelObject.save()
		return modelObject
	
	def update(self, instance, validated_data):
		modelObject = super().update(instance=instance, validated_data=validated_data)
		user = get_current_authenticated_user()
		if user is not None:
			modelObject.updated_by = user
		modelObject.save()
		return modelObject




class UserListSerializer(serializers.ModelSerializer):
	role = RoleMinimalListSerializer()
	thana = serializers.SerializerMethodField()
	city = serializers.SerializerMethodField()
	country = serializers.SerializerMethodField()
	created_by = serializers.SerializerMethodField()
	updated_by = serializers.SerializerMethodField()

	class Meta:
		model = User
		exclude = ['auth_provider', 'email_token', 'phone_otp', 'is_active', 'is_admin', 'is_email_verified', 'is_primary_phone_verified']
		extra_kwargs = {
			'password': {
				'write_only': True,
				'required': False,
			},
			'created_at':{
				'read_only': True,
			},
			'updated_at':{
				'read_only': True,
			},
			'created_by':{
				'read_only': True,
			},
			'updated_by':{
				'read_only': True,
			},
		}

	def get_role(self, obj):
		return obj.role.name if obj.role else obj.role

	def get_thana(self, obj):
		return obj.thana.name if obj.thana else obj.thana
	
	def get_city(self, obj):
		return obj.city.name if obj.city else obj.city
	
	def get_country(self, obj):
		return obj.country.name if obj.country else obj.country
	
	def get_created_by(self, obj):
		return obj.created_by.email if obj.created_by else obj.created_by
		
	def get_updated_by(self, obj):
		return obj.updated_by.email if obj.updated_by else obj.updated_by





class UserListSerializerForGeneralUse(serializers.ModelSerializer):
	thana = serializers.SerializerMethodField()
	city = serializers.SerializerMethodField()
	country = serializers.SerializerMethodField()
	created_by = serializers.SerializerMethodField()
	updated_by = serializers.SerializerMethodField()

	class Meta:
		model = User
		exclude = ['role', 'auth_provider', 'email_token', 'phone_otp', 'is_active', 'is_admin', 'is_email_verified', 'is_primary_phone_verified']
		extra_kwargs = {
			'password': {
				'write_only': True,
				'required': False,
			},
			'created_at':{
				'read_only': True,
			},
			'updated_at':{
				'read_only': True,
			},
			'created_by':{
				'read_only': True,
			},
			'updated_by':{
				'read_only': True,
			},
		}

	def get_thana(self, obj):
		return obj.thana.name if obj.thana else obj.thana
	
	def get_city(self, obj):
		return obj.city.name if obj.city else obj.city
	
	def get_country(self, obj):
		return obj.country.name if obj.country else obj.country
	
	def get_created_by(self, obj):
		return obj.created_by.email if obj.created_by else obj.created_by
		
	def get_updated_by(self, obj):
		return obj.updated_by.email if obj.updated_by else obj.updated_by




class UserSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		exclude = ['role', 'auth_provider', 'is_active', 'is_admin', 'is_email_verified', 'is_primary_phone_verified']
		extra_kwargs = {
			'password': {
				'write_only': True,
				'required': False,
			},
			'phone_otp': {
				'write_only': True,
				'required': False,
			},
			'email_token': {
				'write_only': True,
				'required': False,
			},
			'created_at':{
				'read_only': True,
			},
			'updated_at':{
				'read_only': True,
			},
			'created_by':{
				'read_only': True,
			},
			'updated_by':{
				'read_only': True,
			},
		}

	def create(self, validated_data):
		modelObject = super().create(validated_data=validated_data)
		modelObject.set_password(validated_data["password"])
		user = get_current_authenticated_user()
		if user is not None:
			modelObject.created_by = user
		modelObject.save()
		return modelObject
	
	def update(self, instance, validated_data):
		modelObject = super().update(instance=instance, validated_data=validated_data)
		user = get_current_authenticated_user()
		if user is not None:
			modelObject.updated_by = user
		modelObject.save()
		return modelObject




class PasswordChangeSerializer(serializers.Serializer):
	password = serializers.CharField(max_length=64)
	confirm_password = serializers.CharField(max_length=64)




