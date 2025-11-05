from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<customer_id>\d+)/(?P<therapist_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/location/(?P<customer_id>\d+)/(?P<therapist_id>\d+)/$', consumers.LocationConsumer.as_asgi()),
    re_path(r'ws/test/$', consumers.TestConsumer.as_asgi()),
]