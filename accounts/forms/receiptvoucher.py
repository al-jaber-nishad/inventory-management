from django import forms
from django.core.exceptions import ValidationError
from accounts.models import ReceiptVoucher

class ReceiptVoucherForm(forms.ModelForm):
    date = forms.DateField(
        input_formats=['%d-%m-%Y'],
        widget=forms.DateInput(format='%d-%m-%Y', attrs={'type': 'text'})
    )
    class Meta:
        model = ReceiptVoucher
        fields = [
            'date', 'receipt_ledger', 'sub_ledger', 'bank_or_cash', 'bank_name', 
            'cheque_no', 'cheque_date', 'amount',
            'bill_no', 'file', 'details'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'receipt_ledger': forms.Select(attrs={'class': 'form-control select2_search'}),
            'cheque_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'sub_ledger': forms.Select(attrs={'class': 'form-control select2_search'}),
            'bank_name': forms.Select(attrs={'class': 'form-control'}),
            'bank_or_cash': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cheque_no': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'bill_no': forms.NumberInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'details': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)