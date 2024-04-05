from django import forms


class SearchForms(forms.Form):
    kw = forms.CharField(required=True)