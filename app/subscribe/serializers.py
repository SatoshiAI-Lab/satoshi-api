from rest_framework import serializers
from users.models import UserSubscription
from utils import constants


class UserSubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = UserSubscription
        fields = '__all__'

    def validate(self, data):
        self.message_type = data.get('message_type')
        self.content = data.get('content')

        if self.message_type < 0 or self.message_type > 4:
            raise serializers.ValidationError({'content': 'Content must between 0 and 4.'})
        if self.message_type == 0: # news
            if not isinstance(self.content, dict) or not 'switch' in self.content or self.content['switch'] not in ['on', 'off']:
                raise serializers.ValidationError({'content': 'Content must be a dictionary containing switch.'})
        elif self.message_type == 1: # twitter
            if not (isinstance(self.content, list) and all(isinstance(item, str) and len(item) > 0 for item in self.content)):
                raise serializers.ValidationError({'content': 'Content must be a list of strings.'})
            if len(self.content) != len(set(self.content)):
                raise serializers.ValidationError({'content': 'Content elements are repeated.'})
        elif self.message_type == 2: # announcement
            if not (isinstance(self.content, list) and all(isinstance(item, int) and item > 0 for item in self.content)):
                raise serializers.ValidationError({'content': 'Content must be a list of integers.'})
            if len(self.content) != len(set(self.content)):
                raise serializers.ValidationError({'content': 'Content elements are repeated.'})
        elif self.message_type == 3: # trade
            if not (isinstance(self.content, list) and all(isinstance(item, dict) and len(item.get('address', '')) > 41 for item in self.content)):
                raise serializers.ValidationError({'content': 'Content mit must be a dictionary array. The element values in other dictionaries must contain address.'})
            addresses = [c['address'] for c in self.content]
            if len(addresses) != len(set(addresses)):
                raise serializers.ValidationError({'content': 'Content address elements are repeated.'})
        elif self.message_type == 4: # pool
            if not (isinstance(self.content, list) and all(isinstance(item, dict) and item.get('chain', '') in constants.CHAIN_DICT for item in self.content)):
                raise serializers.ValidationError({'content': 'Content mit must be a dictionary array. The element values in other dictionaries must contain chain.'})
            chains = [c['chain'] for c in self.content]
            if len(chains) != len(set(chains)):
                raise serializers.ValidationError({'content': 'Content chain elements are repeated.'})
        return data
