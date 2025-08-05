from django import forms
from product.models import ProductCategory

class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['name', 'description', 'image', 'parent', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
