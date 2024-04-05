
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db.models import Q

from rest_framework.views import APIView, Request
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from . import forms, models, serializers
import os
from urllib.parse import urljoin


class SearchView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(5 * 60))
    def get(self, request):
        form = forms.SearchForms(request.query_params)
        if not form.is_valid():
            return Response(dict(data={'error': 'Parameter error.'}), status=status.HTTP_400_BAD_REQUEST)
        kw = request.query_params['kw']

        reserved_chars = r'''?&|!{}[]()^~*:\\"'+-'''
        replace = ['\\' + l for l in reserved_chars]
        trans = str.maketrans(dict(zip(reserved_chars, replace)))
        kw = str(kw).strip().translate(trans).replace('%', '')
        
        num = 10
        data = dict()

        sql = f"""
        select id,name,symbol,logo from token where symbol ilike %s 
        order by char_length(symbol) asc, strpos('{kw}',symbol) asc, market_cap desc limit {num};
        """
        objs = models.Coin.objects.using('source').raw(sql, [f'%{kw}%'])
        ser = serializers.CoinSearch(objs, many=True)
        ser_data = ser.data
        tokens = [t['id'] for t in ser_data]

        full_objs = models.Coin.objects.using('source').filter(Q(name__icontains = kw) | Q(slug__icontains = kw)).order_by('-market_cap')[:num]
        full_ser = serializers.CoinSearch(full_objs, many=True)
        for fs in full_ser.data:
            if fs['id'] in tokens:
                continue
            tokens.append(fs['id'])
            ser_data.append(fs)

        chain_objs = models.CoinChainData.objects.using('source').filter(address__icontains = kw)[:num]
        for chain_obj in chain_objs:
            try:
                token = chain_obj.token
                if token.id in tokens:
                    continue
                tokens.append(token.id)
                ser_data.append(dict(id=token.id,name=token.name,symbol=token.symbol,logo=urljoin(os.getenv('IMAGE_DOMAIN'), token.logo)))
            except:
                continue
        data['coin'] = ser_data[:num]
        return Response(dict(data=data), status=status.HTTP_200_OK)