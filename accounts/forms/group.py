from django import forms
from accounts.models import Group, PrimaryGroup

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'head_group', 'head_primarygroup', 'is_deletable', 'is_primary', 'is_default']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['head_primarygroup'].queryset = PrimaryGroup.objects.all()
        self.fields['head_group'].queryset = Group.objects.all()
        
        if self.instance and self.instance.pk:
            self.fields['head_group'].queryset = Group.objects.exclude(pk=self.instance.pk)