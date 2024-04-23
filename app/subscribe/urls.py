from django.urls import path
from .views import UserSubscriptionSettings, UserSubscriptionList

urlpatterns = [
    path('subscription/list/', UserSubscriptionList.as_view(), name='subscription-list'),
    path('subscription/create/', UserSubscriptionSettings.as_view(), name='create-subscription'),
]
