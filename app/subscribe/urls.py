from django.urls import path
from .views import UserSubscriptionCreate, UserSubscriptionUpdate, UserSubscriptionRetrieve, UserSubscriptionList

urlpatterns = [
    path('subscription/list/', UserSubscriptionList.as_view(), name='subscription-list'),
    path('subscription/create/', UserSubscriptionCreate.as_view(), name='create-subscription'),
]
