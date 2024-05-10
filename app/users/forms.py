
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
    amount = forms.IntegerField(required=False)


class MintTokenForms(forms.Form):
    chain = forms.CharField(min_length=1, max_length=30, required=False)
    created_hash = forms.CharField(min_length=1, max_length=128)
    amount = forms.IntegerField(min_value=1)


class CoinCrossQuoteForms(forms.Form):
    crossAmount = forms.CharField(min_length=1, max_length=128)
    slippageBps = forms.IntegerField(min_value=0, max_value=10000, required=False)
    fromData = forms.JSONField(required=True)
    toData = forms.JSONField(required=True)

    def clean_fromData(self):
        fromData = self.cleaned_data.get('fromData')
        if not isinstance(fromData, dict):
            raise forms.ValidationError('Must a dict')
        if 'chain' not in fromData or 'tokenAddress' not in fromData:
            raise forms.ValidationError('Must have chain and tokenAddress')
        
    def clean_toData(self):
        toData = self.cleaned_data.get('toData')
        if not isinstance(toData, dict):
            raise forms.ValidationError('Must a dict')
        if 'chain' not in toData or 'tokenAddress' not in toData:
            raise forms.ValidationError('Must have chain and tokenAddress')
        

class CoinCrossForms(forms.Form):
    provider = forms.CharField(required=True)
    crossAmount = forms.CharField(min_length=1, max_length=128)
    slippageBps = forms.IntegerField(min_value=0, max_value=10000, required=False)
    fromData = forms.JSONField(required=True)
    toData = forms.JSONField(required=True)

    def clean_fromData(self):
        fromData = self.cleaned_data.get('fromData')
        if not isinstance(fromData, dict):
            raise forms.ValidationError('Must a dict')
        if 'chain' not in fromData or 'tokenAddress' not in fromData:
            raise forms.ValidationError('Must have chain and tokenAddress')
        
    def clean_toData(self):
        toData = self.cleaned_data.get('toData')
        if not isinstance(toData, dict):
            raise forms.ValidationError('Must a dict')
        if 'chain' not in toData or 'tokenAddress' not in toData or 'walletAddress' not in toData:
            raise forms.ValidationError('Must have chain, walletAddress and tokenAddress')
