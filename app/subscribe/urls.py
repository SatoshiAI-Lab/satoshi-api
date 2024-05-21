from django.urls import path
from django.urls.resolvers import URLPattern
from .views import UserSubscriptionSettings, UserSubscriptionList

urlpatterns: list[URLPattern] = [
    path(route='subscription/list/', view=UserSubscriptionList.as_view(), name='subscription-list'),
    path(route='subscription/create/', view=UserSubscriptionSettings.as_view(), name='create-subscription'),
]
