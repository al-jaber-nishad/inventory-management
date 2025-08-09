from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm
from phonenumber_field.formfields import PhoneNumberField
from authentication.models import Contact, ContactGroup, Role, User, UserGroup
from django.forms.widgets import ClearableFileInput

# from sms.models import Package

class CustomLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Your userName'}))

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'please enter password'}))
    # username = forms.CharField(label="Username or email or primary phone.", max_length=100)
    # password = forms.PasswordInput()



class CustomUserUpdateForm(UserChangeForm):
    primary_phone = PhoneNumberField(
        error_messages={'invalid': 'Enter a valid phone number (e.g. +8801*********)'}
    )
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'gender', 'primary_phone', 'secondary_phone', 'date_of_birth', 'is_active',
            'role', 'user_group', 'father_name', 'mother_name', 'address', 'nid_image', 'nid_no',
            'profile_picture'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'required': True, 'class' :'mandatory'}),
            'email': forms.EmailInput(attrs={'required': True, 'class' :'mandatory'}),
            'primary_phone': forms.TextInput(attrs={'required': True, 'class' :'mandatory'}),
            'role': forms.Select(attrs={'required': True, 'class' :'mandatory select2_search'}),
            'user_group': forms.Select(attrs={'required': True, 'class' :'mandatory select2_search', 'disabled': 'disabled'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'nid_image': ClearableFileInput(attrs={'class':'form-control'}),
            'profile_picture': ClearableFileInput(attrs={'class':'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class':'form-check-input'}),
            'gender': forms.Select(attrs={'class': 'select2_search'}),
        }
    
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if request:
            if not self.initial.get('role'):
                if request.user.role.name == "ADMIN":
                    self.fields['role'].queryset = Role.objects.filter(name='MANAGER')
                    self.fields['role'].initial = Role.objects.get(name='MANAGER')



class CustomUserCreationForm(UserCreationForm):
    primary_phone = PhoneNumberField(
        error_messages={'invalid': 'Enter a valid phone number (e.g. +8801*********)'}
    )

    class Meta:
        model = User
        fields = [
            'username', 'password1', 'password2', 'first_name', 'last_name', 'email',
            'gender', 'primary_phone', 'secondary_phone', 'date_of_birth', 'is_active',
            'role', 'user_group', 'father_name', 'mother_name', 'address', 'nid_image', 'nid_no',
            'profile_picture'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'required': True, 'class': 'mandatory'}),
            'password1': forms.PasswordInput(attrs={'required': True, 'class': 'mandatory'}),
            'password2': forms.PasswordInput(attrs={'required': True, 'class': 'mandatory'}),
            'email': forms.EmailInput(attrs={'required': True, 'class': 'mandatory'}),
            'primary_phone': forms.TextInput(attrs={'required': True, 'class': 'mandatory'}),
            'role': forms.Select(attrs={'required': True, 'class': 'mandatory select2_search'}),
            'user_group': forms.Select(attrs={'required': True, 'class': 'mandatory select2_search'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'nid_image': ClearableFileInput(attrs={'class': 'form-control'}),
            'profile_picture': ClearableFileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'gender': forms.Select(attrs={'class': 'select2_search'}),
        }

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if request:
            if request.user.role and request.user.role.name == "ADMIN":
                self.fields['role'].queryset = Role.objects.filter(name='MANAGER')
                self.fields['role'].initial = Role.objects.get(name='MANAGER')

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Passwords do not match")

        return cleaned_data


class UserProfileForm(forms.ModelForm):
    primary_phone = PhoneNumberField(
        error_messages={'invalid': 'Enter a valid phone number (e.g. +8801*********)'}
    )
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'gender', 'primary_phone', 'secondary_phone', 'date_of_birth', 'is_active',
            'father_name', 'mother_name', 'address', 'nid_image', 'nid_no',
            'profile_picture'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'disabled': 'disabled',}),
            'email': forms.EmailInput(attrs={'required': True,}),
            'primary_phone': forms.TextInput(attrs={'required': True, 'class' :'mandatory'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'nid_image': ClearableFileInput(attrs={'class':'form-control'}),
            'profile_picture': ClearableFileInput(attrs={'class':'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class':'form-check-input'}),
            'gender': forms.Select(attrs={'class': 'select2_search'}),
        }
    
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if request:
            if not self.initial.get('role'):
                if request.user.role.name == "ADMIN":
                    self.fields['role'].queryset = Role.objects.filter(name='MANAGER')
                    self.fields['role'].initial = Role.objects.get(name='MANAGER')



class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [  # Include all fields except the excluded ones
            'username',
            'first_name',
            'last_name',
            'email',
            'primary_phone',
            'role',
        ]


class UserGroupForm(forms.ModelForm):
    class Meta:
        model = UserGroup
        fields = [
            'name',
        ]


class ContactGroupForm(forms.ModelForm):
    class Meta:
        model = ContactGroup
        fields = [  
            'name',
        ]

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = [  
            'name', 'contact_no', 'contact_group'
        ]

        widgets = {
            'contact_group': forms.Select(attrs={'class': 'form-control select2_search'}),  
        }
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if request:
            self.fields['contact_group'].queryset = ContactGroup.objects.filter(owner_user=request.user)
            # self.fields['contact_group'].empty_label = ''
            