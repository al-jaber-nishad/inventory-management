from django import forms
from accounts.models import SubLedgerAccount

class SubLedgerAccountForm(forms.ModelForm):
    class Meta:
        model = SubLedgerAccount
        fields = ['name']