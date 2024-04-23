from django import forms


class CoinSearchForms(forms.Form):
    kw = forms.CharField(required=True)


class AddressQueryForms(forms.Form):
    address = forms.CharField(required=True)


class ListBaseForm(forms.Form):
    page_index = forms.IntegerField(min_value=1, required=False)
    page_size = forms.IntegerField(min_value=1, max_value=100, required=False)

    def clean_page_index(self):
        return self.cleaned_data.get('page_index', 1) or 1

    def clean_page_size(self):
        return self.cleaned_data.get('page_size', 20) or 20


class CoinListForms(ListBaseForm):
    ids = forms.JSONField(required=False)

    def clean_ids(self):
        ids = self.cleaned_data.get('ids')
        if ids:
            for i in ids:
                if type(i) != dict:
                    raise forms.ValidationError('ids: wrong format')
                if 'id' not in i or 'type' not in i:
                    raise forms.ValidationError('ids: wrong format')
                if not i['id'] or int(i['id']) < 1:
                    raise forms.ValidationError('id: wrong format')
                if not i['type'] or int(i['type']) < 1:
                    raise forms.ValidationError('type: wrong format')
        return ids
    

class CoinInfoForms(forms.Form):
    address = forms.CharField(required=True, min_length=42, max_length=44)
    chain = forms.CharField(required=False, min_length=1)

