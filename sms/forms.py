from django import forms
from django.forms import inlineformset_factory
from authentication.models import User
from sms.models import Package, Sms, SmsAPI, AssignSmsAPI

class PackageForm(forms.ModelForm):
    class Meta:
        model = Package
        fields = [
            'name', 
            'bill_type', 
            'is_deletable', 
            'masking_national_msg_charge', 
            'non_masking_national_msg_charge', 
            'masking_internation_msg_charge', 
            'non_masking_internation_msg_charge', 
            'prefix_based', 
            'masking_prefix_013_charge', 
            'non_masking_prefix_013_charge', 
            'masking_prefix_014_charge', 
            'non_masking_prefix_014_charge', 
            'masking_prefix_015_charge', 
            'non_masking_prefix_015_charge', 
            'masking_prefix_016_charge', 
            'non_masking_prefix_016_charge', 
            'masking_prefix_017_charge', 
            'non_masking_prefix_017_charge', 
            'masking_prefix_018_charge', 
            'non_masking_prefix_018_charge', 
            'masking_prefix_019_charge', 
            'non_masking_prefix_019_charge'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter package name', 'class': 'form-control'}),
            'bill_type': forms.Select(attrs={'class': 'form-control select2_search'}),
            'is_deletable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'masking_national_msg_charge': forms.NumberInput(attrs={'placeholder': 'Enter masking national msg charge', 'class': 'form-control'}),
            'non_masking_national_msg_charge': forms.NumberInput(attrs={'placeholder': 'Enter non-masking national msg charge', 'class': 'form-control'}),
            'masking_internation_msg_charge': forms.NumberInput(attrs={'placeholder': 'Enter masking international msg charge', 'class': 'form-control'}),
            'non_masking_internation_msg_charge': forms.NumberInput(attrs={'placeholder': 'Enter non-masking international msg charge', 'class': 'form-control'}),
            'prefix_based': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'masking_prefix_013_charge': forms.NumberInput(attrs={'placeholder': 'Enter masking prefix 013 charge', 'class': 'form-control'}),
            'non_masking_prefix_013_charge': forms.NumberInput(attrs={'placeholder': 'Enter non-masking prefix 013 charge', 'class': 'form-control'}),
            'masking_prefix_014_charge': forms.NumberInput(attrs={'placeholder': 'Enter masking prefix 014 charge', 'class': 'form-control'}),
            'non_masking_prefix_014_charge': forms.NumberInput(attrs={'placeholder': 'Enter non-masking prefix 014 charge', 'class': 'form-control'}),
            'masking_prefix_015_charge': forms.NumberInput(attrs={'placeholder': 'Enter masking prefix 015 charge', 'class': 'form-control'}),
            'non_masking_prefix_015_charge': forms.NumberInput(attrs={'placeholder': 'Enter non-masking prefix 015 charge', 'class': 'form-control'}),
            'masking_prefix_016_charge': forms.NumberInput(attrs={'placeholder': 'Enter masking prefix 016 charge', 'class': 'form-control'}),
            'non_masking_prefix_016_charge': forms.NumberInput(attrs={'placeholder': 'Enter non-masking prefix 016 charge', 'class': 'form-control'}),
            'masking_prefix_017_charge': forms.NumberInput(attrs={'placeholder': 'Enter masking prefix 017 charge', 'class': 'form-control'}),
            'non_masking_prefix_017_charge': forms.NumberInput(attrs={'placeholder': 'Enter non-masking prefix 017 charge', 'class': 'form-control'}),
            'masking_prefix_018_charge': forms.NumberInput(attrs={'placeholder': 'Enter masking prefix 018 charge', 'class': 'form-control'}),
            'non_masking_prefix_018_charge': forms.NumberInput(attrs={'placeholder': 'Enter non-masking prefix 018 charge', 'class': 'form-control'}),
            'masking_prefix_019_charge': forms.NumberInput(attrs={'placeholder': 'Enter masking prefix 019 charge', 'class': 'form-control'}),
            'non_masking_prefix_019_charge': forms.NumberInput(attrs={'placeholder': 'Enter non-masking prefix 019 charge', 'class': 'form-control'}),
        }



class AssignedPackageForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['package']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(AssignedPackageForm, self).__init__(*args, **kwargs)
        
        # Filter the queryset for the package field
        if self.request:
            self.fields['package'].queryset = User.objects.filter(owner_user=self.request.user)


class SmsForm(forms.ModelForm):
    class Meta:
        model = Sms
        fields = ['text', 'receivers']

        widgets = {
            'text': forms.Textarea(attrs={'type': 'text', 'style': 'height: 400px;'}),
            'receivers': forms.Textarea(attrs={'style': 'height: 500px;'}),
        }

class SmsAPIForm(forms.ModelForm):
    class Meta:
        model = SmsAPI
        fields = ['name', 'url', 'priority', 'is_deletable']

        widgets = {
            'url': forms.Textarea(attrs={'type': 'text'}),
            'is_deletable': forms.CheckboxInput(attrs={'class':'form-check-input'}),
        }


class AssignSmsAPIForm(forms.ModelForm):
    class Meta:
        model = AssignSmsAPI
        fields = ['user', 'sms_api', 'priority', 'is_active', 'is_shared', 'share_percentage']
    
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control select2_search'}),  
            'sms_api': forms.Select(attrs={'class': 'form-control select2_search'}),  
            'is_active': forms.CheckboxInput(attrs={'class':'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(AssignSmsAPIForm, self).__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(role__name='RESELLER')



class UpdatePriorityForm(forms.ModelForm):
    class Meta:
        model = AssignSmsAPI
        fields = ['priority']
        widgets = {
            'priority': forms.HiddenInput()
        }