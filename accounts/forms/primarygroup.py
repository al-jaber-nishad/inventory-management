from django import forms
from accounts.models import PrimaryGroup

class PrimaryGroupForm(forms.ModelForm):
    class Meta:
        model = PrimaryGroup
        fields = ['name', 'is_deletable']