from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db.models import F, Q
from django.core.exceptions import ValidationError

from .models import UserSubscription, TwitterUser, Exchange, TradeAddress
from .serializers import UserSubscriptionSerializer
from rest_framework.permissions import IsAuthenticated
from utils.constants import *

import requests
import json
import os


class UserSubscriptionCreate(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = UserSubscriptionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(dict(data=serializer.errors), status=status.HTTP_400_BAD_REQUEST)
        
        old_content = []
        new_content = request.data['content']
        message_type = request.data['message_type']

        if message_type == 3:
            for c in new_content:
                if c.get('name'):
                    continue
                c['name'] = c['address'][-4:]

        try:
            subscription = UserSubscription.objects.filter(user_id=request.user, message_type=message_type)
            if not subscription.exists():
                serializer.save(user=request.user)
            else:
                old_content = subscription.first().content
                subscription.update(**request.data)
        except ValidationError as e:
            return Response(dict(data=e.messages), status=status.HTTP_400_BAD_REQUEST)
        
        if message_type != 3:
            return Response(dict(data=serializer.data), status=status.HTTP_200_OK)
        
        old_addresses_set = set([c['address'] for c in old_content])
        new_addresses_set = set([c['address'] for c in new_content])
        add_addresses_set = new_addresses_set - old_addresses_set
        del_addresses_set = old_addresses_set - new_addresses_set

        with transaction.atomic():
            involved_records = TradeAddress.objects.filter(
                Q(address__in=add_addresses_set) | Q(address__in=del_addresses_set)
            )
            involved_records_dict = {record.address: record for record in involved_records}

            to_create = []
            to_create_addresses = []
            to_create_sol_addresses = []
            for address in add_addresses_set:
                if address in involved_records_dict:
                    record = involved_records_dict[address]
                    record.count = F('count') + 1
                else:
                    to_create.append(TradeAddress(address=address))
                    if str(address).startswith('0x'):
                        to_create_addresses.append(address)
                    else:
                        to_create_sol_addresses.append(address)
            if to_create:
                TradeAddress.objects.bulk_create(to_create)
            if to_create_addresses:
                requests.request(
                    "POST", 
                    f"{os.getenv('WEB3_EVM_API')}/evm/monitor/eoa_address/add", 
                    headers={
                        'Content-Type': 'application/json',
                    }, 
                    data=json.dumps({
                        "addressList": to_create_addresses,
                        "net": "optimism",
                    }),
                )
            if to_create_sol_addresses:
                requests.request(
                    "POST", 
                    f"{os.getenv('SUB_API')}/monitor/address/", 
                    headers={
                        'Content-Type': 'application/json',
                    }, 
                    data=json.dumps({
                        "addresses": to_create_sol_addresses,
                    }),
                )

            to_reduce_qs = TradeAddress.objects.filter(address__in=del_addresses_set).annotate(new_count=F('count') - 1)
            to_reduce_addresses = []
            to_delete_addresses = []
            to_delete_sol_addresses = []
            for record in to_reduce_qs:
                if record.new_count >= 1:
                    to_reduce_addresses.append(record.address)
                elif str(record.address).startswith('0x'):
                    to_delete_addresses.append(record.address)
                else:
                    to_delete_sol_addresses.append(record.address)
            if to_reduce_addresses:
                TradeAddress.objects.filter(address__in=to_reduce_addresses).update(count=F('count') - 1)
            if to_delete_addresses or to_delete_sol_addresses:
                TradeAddress.objects.filter(address__in=to_delete_addresses + to_delete_sol_addresses).delete()
            if to_delete_addresses:
                requests.request(
                    "POST", 
                    f"{os.getenv('WEB3_EVM_API')}/evm/monitor/eoa_address/remove", 
                    headers={
                        'Content-Type': 'application/json',
                    }, 
                    data=json.dumps({
                        "addressList": to_delete_addresses,
                        "net": "optimism",
                    }),
                )
            if to_delete_sol_addresses:
                requests.request(
                    "DELETE", 
                    f"{os.getenv('SUB_API')}/monitor/address/", 
                    headers={
                        'Content-Type': 'application/json',
                    }, 
                    data=json.dumps({
                        "addresses": to_delete_sol_addresses,
                    }),
                )

        return Response(dict(data=serializer.data), status=status.HTTP_200_OK)

class UserSubscriptionUpdate(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, message_type, *args, **kwargs):
        subscription = UserSubscription.objects.filter(user_id=request.user, message_type=message_type)
        if not subscription.exists():
            return Response(dict(data={"message": "Subscription not found."}), status=status.HTTP_404_NOT_FOUND)
        
        mutable_data = request.data.copy()
        mutable_data['message_type'] = message_type
        serializer = UserSubscriptionSerializer(subscription.first(), data=mutable_data)
        if serializer.is_valid():
            serializer.save()
            return Response(dict(data=serializer.data))
        return Response(dict(data=serializer.errors), status=status.HTTP_400_BAD_REQUEST)

class UserSubscriptionRetrieve(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, message_type, *args, **kwargs):
        subscription = UserSubscription.objects.filter(user_id=request.user, message_type=message_type).first()
        
        if subscription:
            serializer = UserSubscriptionSerializer(subscription)
            return Response(dict(data=serializer.data))
        return Response(dict(data={"message": "Subscription not found."}), status=status.HTTP_404_NOT_FOUND)

class UserSubscriptionDelete(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, message_type, *args, **kwargs):
        subscription = UserSubscription.objects.filter(user_id=request.user, message_type=message_type).first()
        if not subscription.DoesNotExist:
            return Response(dict(data={"message": "Subscription not found."}), status=status.HTTP_404_NOT_FOUND)
        
        subscription.delete()
        return Response(dict(data={"message": "Subscription deleted."}), status=status.HTTP_200_OK)
    
class UserSubscriptionList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        subscriptions = UserSubscription.objects.filter(user_id=request.user)
        my_subscribed = {MESSAGE_TYPE_DICT[s.message_type]: s.content for s in subscriptions}

        twitters = TwitterUser.objects.filter(is_deleted=0).values('twitter_id', 'name', 'logo')
        exchanges = Exchange.objects.filter(announcement_subable=1).values('id', 'slug', 'name')

        pool_dict = {p['chain']:p for p in my_subscribed.get('pool', [])}
        pool_data = [dict(
                chain = chain, 
                max = pool_dict.get(chain, {}).get('max'), 
                min = pool_dict.get(chain, {}).get('min'), 
                subscribed = True if chain in pool_dict else False,
                logo = f"{os.getenv('S3_DOMAIN')}/chains/logo/{chain}.png",
            ) for chain in CHAIN_DICT]

        data = dict(
            news = dict(message_type=0, content=my_subscribed.get('news', {"switch": "off"})),
            twitter = dict(message_type=1, content=[{**twitter, 'subscribed': twitter['twitter_id'] in my_subscribed.get('twitter', [])} for twitter in twitters]),
            announcement = dict(message_type=2, content=[{**exchange, 
                                                          'logo': f"{os.getenv('S3_DOMAIN')}/exchange/logo/{exchange['name']}.png",
                                                          'subscribed': exchange['id'] in my_subscribed.get('announcement', [])} for exchange in exchanges]),
            trade = dict(message_type=3, content=my_subscribed.get('trade', [])),
            pool = dict(message_type=4, content=pool_data),
        )
        return Response(dict(data=data))
    
