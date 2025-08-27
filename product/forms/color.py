from django import forms
from product.models import Color

class ColorForm(forms.ModelForm):
    class Meta:
        model = Color
        fields = ['name', 'hex_code']
        widgets = {
            'hex_code': forms.TextInput(attrs={'type': 'color', 'placeholder': '#FF0000'})
        }