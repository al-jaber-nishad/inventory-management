from django import forms
from purchase_return.models import PurchaseReturn, PurchaseReturnItem
from authentication.models import Supplier
from product.models import Product
from purchase.models import Purchase, PurchaseItem
from django.core.exceptions import ValidationError
import uuid


class PurchaseReturnForm(forms.ModelForm):
    return_date = forms.DateField(
        input_formats=['%d-%m-%Y'],
        widget=forms.DateInput(format='%d-%m-%Y', attrs={'type': 'text'})
    )
    
    class Meta:
        model = PurchaseReturn
        fields = [
            'payment_ledger', 'supplier', 'original_purchase', 'return_number', 'return_date',
            'discount', 'refunded', 'due', 'tax', 'reason', 'note', 'status', 'is_active'
        ]
        widgets = {
            'payment_ledger': forms.Select(attrs={'class': 'form-control select2_search'}),
            'supplier': forms.Select(attrs={'class': 'form-control select2_search'}),
            'original_purchase': forms.Select(attrs={'class': 'form-control select2_search'}),
            'return_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Return number', 'readonly': 'readonly'}),
            'return_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'discount': forms.NumberInput(attrs={'class':"w-20 px-2 py-1 border border-gray-300 rounded-md", 'step': '1', 'min': '0'}),
            'tax': forms.NumberInput(attrs={'class':"w-20 px-2 py-1 border border-gray-300 rounded-md", 'step': '1', 'min': '0'}),
            'refunded': forms.NumberInput(attrs={'class':"w-20 px-2 py-1 border border-gray-300 rounded-md", 'step': '1', 'min': '0'}),
            'due': forms.NumberInput(attrs={'id': '', 'class':"w-20 px-2 py-1 border border-gray-300 rounded-md", 'step': '1', 'min': '0'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for return'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Generate return number for new returns
        if not self.instance.pk and not self.initial.get('return_number'):
            self.fields['return_number'].initial = self.generate_return_number()
            
        # Filter original purchases to show only confirmed/received purchases
        self.fields['original_purchase'].queryset = Purchase.objects.filter(
            status__in=[Purchase.Status.CONFIRMED, Purchase.Status.RECEIVED]
        ).order_by('-purchase_date')

    def generate_return_number(self):
        import datetime
        today = datetime.date.today()
        prefix = f"PR-{today.year}-"
        
        # Find the last purchase return of this year
        last_return = PurchaseReturn.objects.filter(
            return_number__startswith=prefix
        ).order_by('-return_number').first()
        
        if last_return:
            try:
                last_number = int(last_return.return_number.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:05d}"

    def clean_return_number(self):
        return_number = self.cleaned_data.get('return_number', '').strip()
        if not return_number:
            raise ValidationError("Return number is required.")
        
        # Check for uniqueness, excluding current instance
        existing = PurchaseReturn.objects.filter(return_number=return_number)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError("Return number already exists.")
        
        return return_number

    def clean(self):
        cleaned_data = super().clean()
        original_purchase = cleaned_data.get('original_purchase')
        supplier = cleaned_data.get('supplier')
        
        # If original purchase is selected, supplier should match
        if original_purchase and supplier and original_purchase.supplier != supplier:
            raise ValidationError("Supplier must match the original purchase supplier.")
        
        # If original purchase is selected, auto-set supplier
        if original_purchase and not supplier:
            cleaned_data['supplier'] = original_purchase.supplier
        
        return cleaned_data


class PurchaseReturnItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseReturnItem
        fields = ['product', 'original_purchase_item', 'quantity', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control product-select select2_search'}),
            'original_purchase_item': forms.Select(attrs={'class': 'form-control original-item-select select2_search'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity-input', 'step': '1', 'min': '1'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control price-input', 'step': '1', 'min': '1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_active=True)
        self.fields['original_purchase_item'].queryset = PurchaseItem.objects.all()
        self.fields['original_purchase_item'].required = False

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is None or quantity <= 0:
            raise ValidationError("Quantity must be greater than 0.")
        
        # If original purchase item is selected, check if return quantity doesn't exceed purchased quantity
        original_item = self.cleaned_data.get('original_purchase_item')
        if original_item:
            # Calculate total already returned for this item
            existing_returns = PurchaseReturnItem.objects.filter(
                original_purchase_item=original_item
            )
            if self.instance.pk:
                existing_returns = existing_returns.exclude(pk=self.instance.pk)
            
            total_returned = sum(item.quantity for item in existing_returns)
            available_to_return = original_item.quantity - total_returned
            
            if quantity > available_to_return:
                raise ValidationError(
                    f"Cannot return {quantity} items. Only {available_to_return} available to return."
                )
        
        return quantity

    def clean_unit_price(self):
        unit_price = self.cleaned_data.get('unit_price')
        if unit_price is None or unit_price < 0:
            raise ValidationError("Unit price cannot be negative.")
        return unit_price

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        original_item = cleaned_data.get('original_purchase_item')
        
        # If original purchase item is selected, product should match
        if original_item and product and original_item.product != product:
            raise ValidationError("Product must match the original purchase item.")
        
        # If original purchase item is selected, auto-set product and unit price
        if original_item and not product:
            cleaned_data['product'] = original_item.product
        if original_item and not cleaned_data.get('unit_price'):
            cleaned_data['unit_price'] = original_item.unit_price
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Calculate total price
        if instance.quantity and instance.unit_price:
            instance.total_price = instance.quantity * instance.unit_price
        
        if commit:
            instance.save()
        return instance