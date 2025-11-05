import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.db import transaction
from chat.models import Conversation, Message

User = get_user_model()
logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        
        if not user.is_authenticated:
            await self.close(code=4001)
            return
            
        try:
            self.customer_id = self.scope['url_route']['kwargs']['customer_id']
            self.therapist_id = self.scope['url_route']['kwargs']['therapist_id']
        except KeyError:
            await self.close(code=4000)
            return
            
        if user.role == 'customer' and str(user.id) != str(self.customer_id):
            await self.close(code=4003)
            return
        if user.role == 'therapist' and str(user.id) != str(self.therapist_id):
            await self.close(code=4003)
            return
            
        self.room_group_name = f'chat_{min(self.customer_id, self.therapist_id)}_{max(self.customer_id, self.therapist_id)}'
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        self.conversation = await self.get_or_create_conversation(self.customer_id, self.therapist_id)
    
    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data.get('message', '').strip()
            
            if not message:
                return
                
            user = self.scope['user']
            sender_id = user.id
            receiver_id = self.therapist_id if user.role == 'customer' else self.customer_id
            
            msg_obj = await self.create_message(self.conversation, sender_id, receiver_id, message)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': str(sender_id),
                    'message_id': str(msg_obj.id),
                    'timestamp': msg_obj.created_at.isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'message_id': event['message_id'],
            'timestamp': event['timestamp'],
        }))
    
    @database_sync_to_async
    def get_or_create_conversation(self, customer_id, therapist_id):
        try:
            with transaction.atomic():
                conversation = Conversation.objects.filter(
                    participants__id=customer_id
                ).filter(
                    participants__id=therapist_id
                ).first()
                
                if not conversation:
                    conversation = Conversation.objects.create()
                    conversation.participants.add(customer_id, therapist_id)
                return conversation
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise
    
    @database_sync_to_async
    def create_message(self, conversation, sender_id, receiver_id, content):
        try:
            with transaction.atomic():
                sender = User.objects.get(id=sender_id)
                receiver = User.objects.get(id=receiver_id)
                
                message_obj = Message.objects.create(
                    conversation=conversation, 
                    sender=sender, 
                    receiver=receiver, 
                    content=content
                )
                
                conversation.last_message = message_obj
                conversation.save(update_fields=['last_message', 'updated_at'])
                
                return message_obj
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise

class LocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        
        if not user.is_authenticated:
            await self.close(code=4001)
            return
            
        try:
            self.customer_id = self.scope['url_route']['kwargs']['customer_id']
            self.therapist_id = self.scope['url_route']['kwargs']['therapist_id']
        except KeyError:
            await self.close(code=4000)
            return
            
        if user.role == 'customer' and str(user.id) != str(self.customer_id):
            await self.close(code=4003)
            return
        if user.role == 'therapist' and str(user.id) != str(self.therapist_id):
            await self.close(code=4003)
            return
            
        self.room_group_name = f'location_{min(self.customer_id, self.therapist_id)}_{max(self.customer_id, self.therapist_id)}'
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            user = self.scope['user']
            
            if user.role == 'therapist':
                latitude = data.get('latitude')
                longitude = data.get('longitude')
                
                if latitude and longitude:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'location_update',
                            'latitude': latitude,
                            'longitude': longitude,
                            'therapist_id': str(user.id),
                        }
                    )
        except Exception as e:
            logger.error(f"Error processing location: {e}")
    
    async def location_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'location',
            'latitude': event['latitude'],
            'longitude': event['longitude'],
            'therapist_id': event['therapist_id'],
        }))

class TestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'WebSocket connection successful!',
            'timestamp': '2024-01-01T00:00:00Z'
        }))
    
    async def disconnect(self, close_code):
        pass
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data.get('message', 'No message provided')
            
            await self.send(text_data=json.dumps({
                'type': 'echo',
                'message': f'Echo: {message}',
                'timestamp': '2024-01-01T00:00:00Z'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error: {str(e)}',
                'timestamp': '2024-01-01T00:00:00Z'
            }))