
from django import forms


class WalletTransactionForms(forms.Form):
    platform = forms.CharField(min_length=1, max_length=10, required=False)
    input_token = forms.CharField(min_length=1, max_length=128)
    output_token = forms.CharField(min_length=1, max_length=128)
    amount = forms.CharField(min_length=1, max_length=128)
    slippageBps = forms.IntegerField(min_value=0, max_value=100, required=False)
