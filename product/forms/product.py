from django import forms
from product.models import Product
from django.core.exceptions import ValidationError

class ProductForm(forms.ModelForm):
    initial_stock = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        initial=0,
        required=False,
        help_text="Initial stock quantity for this product.",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1'})
    )
    
    class Meta:
        model = Product
        fields = ['name', 'sku', 'image', 'category', 'description', 'price', 'is_active', 'brand', 'unit', 'color']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control select2_search'}),
            'brand': forms.Select(attrs={'class': 'form-control select2_search'}),
            'unit': forms.Select(attrs={'class': 'form-control select2_search'}),
            'color': forms.Select(attrs={'class': 'form-control select2_search'}),
        }

    def __init__(self, *args, **kwargs):
        # expecting request passed in for possible future scoping/choices
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        # Example: if you want to limit categories to some user-specific subset later
        # if self.request:
        #     self.fields['category'].queryset = ProductCategory.objects.filter(...) 

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is None:
            raise ValidationError("Price is required.")
        if price < 0:
            raise ValidationError("Price cannot be negative.")
        return price

    def clean_sku(self):
        sku = self.cleaned_data.get('sku', '').strip().upper()
        if not sku:
            raise ValidationError("SKU is required.")
        return sku
