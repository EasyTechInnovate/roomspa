from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count, Max, F, Subquery, OuterRef
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer

class MessagePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_list(request):
    user = request.user
    conversations = (
        Conversation.objects.filter(participants=user)
        .prefetch_related('participants')
        .select_related('last_message')
        .annotate(
            unread_count=Count(
                'messages',
                filter=Q(messages__receiver=user, messages__is_read=False)
            )
        )
        .order_by('-updated_at')
    )
    serializer = ConversationSerializer(conversations, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_messages(request):
    conversation_id = request.query_params.get('conversation_id', '').strip()
    if not conversation_id:
        return Response({'message': 'conversation_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        conversation = Conversation.objects.get(id=conversation_id)
    except Conversation.DoesNotExist:
        return Response({'message': 'Conversation not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.user not in conversation.participants.all():
        return Response({'message': 'User not a participant of this conversation.'}, status=status.HTTP_403_FORBIDDEN)
    
    messages = Message.objects.filter(conversation=conversation).select_related('sender')
    
    paginator = MessagePagination()
    paginated_messages = paginator.paginate_queryset(messages, request)
    serializer = MessageSerializer(paginated_messages, many=True, context={'request': request})
    
    return paginator.get_paginated_response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_conversation_read(request):
    conversation_id = request.data.get('conversation_id')
    if not conversation_id:
        return Response({'message': 'conversation_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        conversation = Conversation.objects.get(id=conversation_id)
    except Conversation.DoesNotExist:
        return Response({'message': 'Conversation not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.user not in conversation.participants.all():
        return Response({'message': 'User not a participant of this conversation.'}, status=status.HTTP_403_FORBIDDEN)
    
    updated_count = conversation.mark_all_as_read(request.user.id)
    
    return Response({'message': f'Marked {updated_count} messages as read.'}, status=status.HTTP_200_OK)