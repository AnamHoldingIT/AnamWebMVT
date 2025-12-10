from django import forms
from .models import Contract


class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = [
            'full_name',
            'phone',
            'startup_name',
            'departments',
            'detail',
        ]