from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import UserSubscription, TwitterUser, Exchange, TradeAddress
from .serializers import UserSubscriptionSerializer
from rest_framework.permissions import IsAuthenticated
from utils.constants import *


class UserSubscriptionCreate(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = UserSubscriptionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(dict(data=serializer.errors), status=status.HTTP_400_BAD_REQUEST)
        subscription = UserSubscription.objects.filter(user_id=request.user, message_type=request.data['message_type'])
        if not subscription.exists():
            serializer.save(user=request.user)
        else:
            subscription.update(**request.data)
            return Response(dict(data=serializer.data))
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
        pools = [{"name": "Ethereum"}, {"name": "Solana"}]

        data = dict(
            news = dict(message_type=0, content=my_subscribed.get('news', {"switch": "off"})),
            twitter = dict(message_type=1, content=[{**twitter, 'subscribed': twitter['twitter_id'] in my_subscribed.get('twitter', [])} for twitter in twitters]),
            announcement = dict(message_type=2, content=[{**exchange, 'subscribed': exchange['id'] in my_subscribed.get('announcement', [])} for exchange in exchanges]),
            trade = dict(message_type=3, content=my_subscribed.get('trade', [])),
            pool = dict(message_type=4, content=[{**pool, 'subscribed': pool['name'] in my_subscribed.get('pool', [])} for pool in pools]),
        )
        return Response(dict(data=data))
    
