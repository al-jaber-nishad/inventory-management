from django import forms
from django.core.exceptions import ValidationError
from product.models import Product
from inventory.models import InventoryAdjustment


class InventoryAdjustmentForm(forms.ModelForm):
    class Meta:
        model = InventoryAdjustment
        fields = ['product', 'adjustment_type', 'quantity', 'reason']
        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-select select2_search',
                'required': True
            }),
            'adjustment_type': forms.Select(attrs={
                'class': 'form-select select2_search',
                'required': True
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter quantity',
                'required': True,
                'min': '0.01',
                'step': '0.01'
            }),
            'reason': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter reason for adjustment'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_active=True)
        self.fields['product'].empty_label = "Select Product"

    def clean(self):
        cleaned_data = super().clean()
        adjustment_type = cleaned_data.get('adjustment_type')
        quantity = cleaned_data.get('quantity')
        product = cleaned_data.get('product')
        
        if adjustment_type == InventoryAdjustment.AdjustmentType.DECREASE and product and quantity:
            from inventory.utils.stock_quantity import get_current_stock
            current_stock = get_current_stock(product.id)
            
            if quantity > current_stock:
                raise ValidationError(
                    f"Cannot decrease stock by {quantity}. Current stock is only {current_stock}."
                )
        
        return cleaned_data