from django.urls import path
from .views import UserSubscriptionCreate, UserSubscriptionUpdate, UserSubscriptionRetrieve, UserSubscriptionList

urlpatterns = [
    path('subscription/list/', UserSubscriptionList.as_view(), name='subscription-list'),
    path('subscription/create/', UserSubscriptionCreate.as_view(), name='create-subscription'),
    # path('subscription/update/<int:message_type>/', UserSubscriptionUpdate.as_view(), name='update-subscription'),
    # path('subscription/retrieve/<int:message_type>/', UserSubscriptionRetrieve.as_view(), name='retrieve-subscription'),
]
