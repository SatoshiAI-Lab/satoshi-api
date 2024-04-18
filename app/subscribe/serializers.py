from rest_framework import serializers
from users.models import UserSubscription

class UserSubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = UserSubscription
        fields = '__all__'