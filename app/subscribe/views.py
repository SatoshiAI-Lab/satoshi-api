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


class UserSubscriptionSettings(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):   
        serializer = UserSubscriptionSerializer(data=request.data)
        if not serializer.is_valid():
            return ResponseUtil.field_error()
        
        old_content = []
        new_content = request.data['content']
        message_type = request.data['message_type']
                
        try:
            subscription = UserSubscription.objects.filter(user_id=request.user, message_type=message_type)
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
        
        old_addresses_set = set([c['address'].lower() for c in old_content])
        new_addresses_set = set([c['address'].lower() for c in new_content])
        add_addresses_set = new_addresses_set - old_addresses_set
        del_addresses_set = old_addresses_set - new_addresses_set

        with transaction.atomic():
            involved_records = TradeAddress.objects.filter(
                Q(address__in=add_addresses_set) | Q(address__in=del_addresses_set)
            )
            involved_records_dict = {record.address.lower(): record for record in involved_records}

            to_create = []
            to_create_addresses = []
            to_create_sol_addresses = []
            for address in add_addresses_set:
                if address in involved_records_dict:
                    record = involved_records_dict[address]
                    record.count = F('count') + 1
                else:
                    to_create.append(TradeAddress(address=address))
                    if str(address).startswith('0x') and len(str(address)) == 42:
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
                    },
                    ),
                    timeout=15,
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
                    },
                    ),
                    timeout=15,
                )

            to_reduce_qs = TradeAddress.objects.filter(address__in=del_addresses_set).annotate(new_count=F('count') - 1)
            to_reduce_addresses = []
            to_delete_addresses = []
            to_delete_sol_addresses = []
            for record in to_reduce_qs:
                if record.new_count >= 1:
                    to_reduce_addresses.append(record.address)
                elif str(record.address).startswith('0x') and len(str(record.address)) == 42:
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
                    },
                    ),
                    timeout=15,
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
                    },
                    ),
                    timeout=15,
                )

        return ResponseUtil.success(data=serializer.data)


class UserSubscriptionList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        subscriptions = UserSubscription.objects.filter(user_id=request.user)
        my_subscribed = {constants.MESSAGE_TYPE_DICT[s.message_type]: s.content for s in subscriptions}

        twitters = TwitterUser.objects.filter(is_deleted=0).values('twitter_id', 'name', 'logo')
        exchanges = Exchange.objects.filter(announcement_subable=1).values('id', 'slug', 'name')

        pool_dict = {p['chain']:p for p in my_subscribed.get('pool', [])}
        pool_data = [dict(
                chain = chain, 
                max = pool_dict.get(chain, {}).get('max'), 
                min = pool_dict.get(chain, {}).get('min'), 
                subscribed = True if chain in pool_dict else False,
                logo = f"{os.getenv('S3_DOMAIN')}/chains/logo/{chain}.png",
            ) for chain in constants.CHAIN_DICT]

        data = dict(
            news = dict(message_type=0, content=my_subscribed.get('news', {"switch": "on"})),
            twitter = dict(message_type=1, content=[{**twitter, 'subscribed': twitter['twitter_id'] in my_subscribed.get('twitter', [])} for twitter in twitters]),
            announcement = dict(message_type=2, content=[{**exchange, 
                                                          'logo': f"{os.getenv('S3_DOMAIN')}/exchange/logo/{exchange['name']}.png",
                                                          'subscribed': exchange['id'] in my_subscribed.get('announcement', [])} for exchange in exchanges]),
            trade = dict(message_type=3, content=my_subscribed.get('trade', [])),
            pool = dict(message_type=4, content=pool_data),
        )
        return ResponseUtil.success(data=data)    
