
from django import forms
from utils.constants import *


class WalletTransactionForms(forms.Form):
    chain = forms.CharField(min_length=1, max_length=30, required=False)
    input_token = forms.CharField(min_length=1, max_length=128)
    output_token = forms.CharField(min_length=1, max_length=128)
    amount = forms.CharField(min_length=1, max_length=128)
    slippageBps = forms.IntegerField(min_value=0, max_value=100, required=False)

    def clean_chain(self):
        chain = self.cleaned_data.get('chain')
        if chain and chain not in CHAIN_DICT:
            raise forms.ValidationError('Chain error')


class UserSelectForms(forms.Form):
    ids = forms.JSONField(required=True)
    status = forms.IntegerField(required=True)

    def clean_ids(self):
        ids = self.cleaned_data.get('ids')
        if not isinstance(ids, list):
            raise forms.ValidationError('Must a list')

        for item in ids:
            if not isinstance(item, dict) or 'id' not in item or 'type' not in item:
                raise forms.ValidationError('Must have id and type')
        
            if not item['id'] or int(item['id']) < 1:
                raise forms.ValidationError('id: wrong format')
            if not item['type'] or int(item['type']) < 1:
                raise forms.ValidationError('type: wrong format')
        return ids
    

class CreateTokenForms(forms.Form):
    chain = forms.CharField(min_length=1, max_length=30, required=False)
    name = forms.CharField(min_length=1, max_length=100)    
    symbol = forms.CharField(min_length=1, max_length=100) 
    decimals = forms.IntegerField(min_value=1,max_value=18) 
    desc = forms.CharField(min_length=1, max_length=100,required=False)


class MintTokenForms(forms.Form):
    chain = forms.CharField(min_length=1, max_length=30, required=False)
    created_hash = forms.CharField(min_length=1, max_length=128)
    amount = forms.IntegerField(min_value=1)