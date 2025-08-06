from django import forms
from accounts.models import LedgerAccount, Group

class LedgerAccountForm(forms.ModelForm):
    class Meta:
        model = LedgerAccount
        fields = ['name', 'ledger_type', 'reference_id', 'details', 'head_group', 'amount', 'note', 'is_deletable', 'is_default']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['head_group'].queryset = Group.objects.all()