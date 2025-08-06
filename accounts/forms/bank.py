from django import forms
from accounts.models import Bank

class BankForm(forms.ModelForm):
    class Meta:
        model = Bank
        fields = ['name']