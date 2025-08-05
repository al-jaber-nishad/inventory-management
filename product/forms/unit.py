from django import forms
from product.models import Unit

class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['name']
