from django.urls import path
from . import views

urlpatterns = [
    path('conversations/', views.conversation_list, name='conversation-list'),
    path('messages/', views.conversation_messages, name='conversation-messages'),
    path('conversations/read/', views.mark_conversation_read, name='mark-conversation-read'),
]