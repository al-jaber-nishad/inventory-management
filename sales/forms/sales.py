from django import forms
from sales.models import Sale, SaleItem
from authentication.models import Customer
from product.models import Product
from django.core.exceptions import ValidationError
import uuid


class SaleForm(forms.ModelForm):
    sale_date = forms.DateField(
        input_formats=['%d-%m-%Y'],
        widget=forms.DateInput(format='%d-%m-%Y', attrs={'type': 'text'})
    )
    due_date = forms.DateField(
        input_formats=['%d-%m-%Y'],
        widget=forms.DateInput(format='%d-%m-%Y', attrs={'type': 'text'})
    )
    class Meta:
        model = Sale
        fields = [
            'payment_ledger', 'customer', 'invoice_number', 'sale_date', 'due_date',
            'discount', 'paid', 'due', 'tax', 'note', 'status'
        ]
        widgets = {
            'payment_ledger': forms.Select(attrs={'class': 'form-control select2_search'}),
            'customer': forms.Select(attrs={'class': 'form-control select2_search'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Invoice number', 'readonly': 'readonly',}),
            'sale_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'discount': forms.NumberInput(attrs={'class':"w-20 px-2 py-1 border border-gray-300 rounded-md", 'step': '1', 'min': '0'}),
            'tax': forms.NumberInput(attrs={'class':"w-20 px-2 py-1 border border-gray-300 rounded-md", 'step': '1', 'min': '0'}),
            'paid': forms.NumberInput(attrs={'class':"w-20 px-2 py-1 border border-gray-300 rounded-md", 'step': '1', 'min': '0'}),
            'due': forms.NumberInput(attrs={'id': '', 'class':"w-20 px-2 py-1 border border-gray-300 rounded-md", 'step': '1', 'min': '0'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Generate invoice number for new sales
        if not self.instance.pk and not self.initial.get('invoice_number'):
            self.fields['invoice_number'].initial = self.generate_invoice_number()

    def generate_invoice_number(self):
        import datetime
        today = datetime.date.today()
        prefix = f"SO-{today.year}-"
        
        # Find the last sale of this year
        last_sale = Sale.objects.filter(
            invoice_number__startswith=prefix
        ).order_by('-invoice_number').first()
        
        if last_sale:
            try:
                last_number = int(last_sale.invoice_number.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:05d}"

    def clean_invoice_number(self):
        invoice_number = self.cleaned_data.get('invoice_number', '').strip()
        if not invoice_number:
            raise ValidationError("Invoice number is required.")
        
        # Check for uniqueness, excluding current instance
        existing = Sale.objects.filter(invoice_number=invoice_number)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError("Invoice number already exists.")
        
        return invoice_number

    def clean(self):
        cleaned_data = super().clean()
        sale_date = cleaned_data.get('sale_date')
        due_date = cleaned_data.get('due_date')
        
        if sale_date and due_date and due_date < sale_date:
            raise ValidationError("Due date cannot be earlier than sale date.")
        
        return cleaned_data


class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ['product', 'quantity', 'unit_price', 'discount_percentage']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control product-select select2_search'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity-input', 'step': '0.01', 'min': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control price-input', 'step': '0.01', 'min': '0.01'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control discount-input', 'step': '0.01', 'min': '0', 'max': '100'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_active=True)

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is None or quantity <= 0:
            raise ValidationError("Quantity must be greater than 0.")
        return quantity

    def clean_unit_price(self):
        unit_price = self.cleaned_data.get('unit_price')
        if unit_price is None or unit_price < 0:
            raise ValidationError("Unit price cannot be negative.")
        return unit_price

    def clean_discount_percentage(self):
        discount = self.cleaned_data.get('discount_percentage')
        if discount is not None and (discount < 0 or discount > 100):
            raise ValidationError("Discount percentage must be between 0 and 100.")
        return discount

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Calculate discount amount and total price
        if instance.quantity and instance.unit_price:
            subtotal = instance.quantity * instance.unit_price
            discount_percentage = instance.discount_percentage or 0
            instance.discount_amount = (subtotal * discount_percentage) / 100
            instance.total_price = subtotal - instance.discount_amount
        
        if commit:
            instance.save()
        return instance