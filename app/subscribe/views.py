from typing import Any
from django.db.models.manager import BaseManager
import requests
import json
import os

from rest_framework.views import APIView
from django.db import transaction
from django.db.models import F, Q
from django.core.exceptions import ValidationError

from users.models import UserSubscription
from .models import TwitterUser, Exchange, TradeAddress
from .serializers import UserSubscriptionSerializer
from rest_framework.permissions import IsAuthenticated
from utils import constants
from utils.response_util import ResponseUtil
from rest_framework.request import Request
from rest_framework.response import Response


class UserSubscriptionSettings(APIView):
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    @transaction.atomic
    def post(self, request: Request, *args, **kwargs) -> Response:   
        serializer: UserSubscriptionSerializer = UserSubscriptionSerializer(data=request.data)
        if not serializer.is_valid():
            return ResponseUtil.field_error()
        
        old_content: list = []
        new_content: str = request.data['content']
        message_type: int = request.data['message_type']
                
        try:
            subscription: BaseManager[UserSubscription] = UserSubscription.objects.filter(user_id=request.user, message_type=message_type)
            if not subscription.exists():
                serializer.save(user=request.user)
            else:
                old_content = subscription.first().content
                subscription.update(**request.data)
        except ValidationError as e:
            return ResponseUtil.field_error(msg=e.messages)
        
        if message_type != 3:
            return ResponseUtil.success(data=serializer.data)
        else:
            for c in new_content:
                if str(c['address']).startswith('0x') and len(str(c['address'])) == 42:
                    c['address'] = str(c['address']).lower()
                if c.get('name'):
                    continue
                c['name'] = c['address'][-4:]
        
        old_addresses_set: set[str] = set([c['address'].lower() for c in old_content])
        new_addresses_set: set[str] = set([c['address'].lower() for c in new_content])
        add_addresses_set: set[str] = new_addresses_set - old_addresses_set
        del_addresses_set: set[str] = old_addresses_set - new_addresses_set

        with transaction.atomic():
            involved_records: BaseManager[TradeAddress] = TradeAddress.objects.filter(
                Q(address__in=add_addresses_set) | Q(address__in=del_addresses_set)
            )
            involved_records_dict: dict[str, TradeAddress] = {record.address.lower(): record for record in involved_records}

            to_create: list = []
            to_create_addresses: list = []
            to_create_sol_addresses: list = []
            for address in add_addresses_set:
                if address in involved_records_dict:
                    record: TradeAddress = involved_records_dict[address]
                    record.count = F(name='count') + 1
                else:
                    to_create.append(TradeAddress(address=address))
                    if str(object=address).startswith('0x') and len(str(object=address)) == 42:
                        to_create_addresses.append(address)
                    else:
                        to_create_sol_addresses.append(address)
            if to_create:
                TradeAddress.objects.bulk_create(objs=to_create)
            if to_create_addresses:
                requests.request(
                    method="POST", 
                    url=f"{os.getenv(key='WEB3_EVM_API')}/evm/monitor/eoa_address/add", 
                    headers={
                        'Content-Type': 'application/json',
                    }, 
                    data=json.dumps(obj={
                        "addressList": to_create_addresses,
                        "net": "optimism",
                    },
                    ),
                    timeout=15,
                )
            if to_create_sol_addresses:
                requests.request(
                    method="POST", 
                    url=f"{os.getenv(key='SUB_API')}/monitor/address/", 
                    headers={
                        'Content-Type': 'application/json',
                    }, 
                    data=json.dumps(obj={
                        "addresses": to_create_sol_addresses,
                    },
                    ),
                    timeout=15,
                )

            to_reduce_qs: BaseManager[TradeAddress] = TradeAddress.objects.filter(address__in=del_addresses_set).annotate(new_count=F(name='count') - 1)
            to_reduce_addresses: list = []
            to_delete_addresses: list = []
            to_delete_sol_addresses: list = []
            for record in to_reduce_qs:
                if record.new_count >= 1:
                    to_reduce_addresses.append(record.address)
                elif str(object=record.address).startswith('0x') and len(str(object=record.address)) == 42:
                    to_delete_addresses.append(record.address)
                else:
                    to_delete_sol_addresses.append(record.address)
            if to_reduce_addresses:
                TradeAddress.objects.filter(address__in=to_reduce_addresses).update(count=F(name='count') - 1)
            if to_delete_addresses or to_delete_sol_addresses:
                TradeAddress.objects.filter(address__in=to_delete_addresses + to_delete_sol_addresses).delete()
            if to_delete_addresses:
                requests.request(
                    method="POST", 
                    url=f"{os.getenv(key='WEB3_EVM_API')}/evm/monitor/eoa_address/remove", 
                    headers={
                        'Content-Type': 'application/json',
                    }, 
                    data=json.dumps(obj={
                        "addressList": to_delete_addresses,
                        "net": "optimism",
                    },
                    ),
                    timeout=15,
                )
            if to_delete_sol_addresses:
                requests.request(
                    method="DELETE", 
                    url=f"{os.getenv(key='SUB_API')}/monitor/address/", 
                    headers={
                        'Content-Type': 'application/json',
                    }, 
                    data=json.dumps(obj={
                        "addresses": to_delete_sol_addresses,
                    },
                    ),
                    timeout=15,
                )
        return ResponseUtil.success(data=serializer.data)


class UserSubscriptionList(APIView):
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    def get(self, request: Request, *args, **kwargs) -> Response:
        subscriptions: BaseManager[UserSubscription] = UserSubscription.objects.filter(user_id=request.user)
        my_subscribed: dict[str, Any] = {constants.MESSAGE_TYPE_DICT[s.message_type]: s.content for s in subscriptions}

        twitters: Any = TwitterUser.objects.filter(is_deleted=0).values('twitter_id', 'name', 'logo')
        exchanges: Any = Exchange.objects.filter(announcement_subable=1).values('id', 'slug', 'name')

        pool_dict: dict[str, Any] = {p['chain']:p for p in my_subscribed.get('pool', [])}
        pool_data: list[dict[str, str | bool]] = [dict(
                chain = chain, 
                max = pool_dict.get(chain, {}).get('max'), 
                min = pool_dict.get(chain, {}).get('min'), 
                subscribed = True if chain in pool_dict else False,
                logo = f"{os.getenv(key='S3_DOMAIN')}/chains/logo/{chain}.png",
            ) for chain in constants.CHAIN_DICT]

        data: dict[str, dict[str, Any]] = dict(
            news = dict(message_type=0, content=my_subscribed.get('news', {"switch": "on"})),
            twitter = dict(message_type=1, content=[{**twitter, 'subscribed': twitter['twitter_id'] in my_subscribed.get('twitter', [])} for twitter in twitters]),
            announcement = dict(message_type=2, content=[{**exchange, 
                                                          'logo': f"{os.getenv(key='S3_DOMAIN')}/exchange/logo/{exchange['name']}.png",
                                                          'subscribed': exchange['id'] in my_subscribed.get('announcement', [])} for exchange in exchanges]),
            trade = dict(message_type=3, content=my_subscribed.get('trade', [])),
            pool = dict(message_type=4, content=pool_data),
        )
        return ResponseUtil.success(data=data)    
