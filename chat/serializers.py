from rest_framework import serializers
from .models import Conversation, Message
from User.serializers import UserMinimalSerializer

class MessageSerializer(serializers.ModelSerializer):
    sender_details = UserMinimalSerializer(source='sender', read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_details', 'receiver', 'content', 
                 'is_read', 'created_at', 'read_at', 'message_type', 'metadata']
        read_only_fields = ('id', 'sender', 'created_at', 'read_at')

class ConversationSerializer(serializers.ModelSerializer):
    participants_details = UserMinimalSerializer(source='participants', many=True, read_only=True)
    last_message_content = serializers.SerializerMethodField()
    unread_count = serializers.IntegerField(read_only=True)
    other_participant = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'participants_details', 'last_message', 
                 'last_message_content', 'unread_count', 'updated_at', 'created_at', 
                 'is_active', 'title', 'other_participant']
        read_only_fields = ('id', 'updated_at', 'created_at')
    
    def get_last_message_content(self, obj):
        if obj.last_message:
            return MessageSerializer(obj.last_message).data
        return None
    
    def get_other_participant(self, obj):
        user = self.context['request'].user
        other = obj.get_other_participant(user)
        if other:
            return UserMinimalSerializer(other).data
        return None