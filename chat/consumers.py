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
        logger.info(f"[ChatConsumer] Connection attempt started")

        user = self.scope['user']
        logger.info(f"[ChatConsumer] User authenticated: {user.is_authenticated}, User: {user}")

        if not user.is_authenticated:
            logger.warning(f"[ChatConsumer] Connection rejected - user not authenticated")
            await self.close(code=4001)
            return

        try:
            self.customer_id = self.scope['url_route']['kwargs']['customer_id']
            self.therapist_id = self.scope['url_route']['kwargs']['therapist_id']
            logger.info(f"[ChatConsumer] Customer ID: {self.customer_id}, Therapist ID: {self.therapist_id}")
        except KeyError as e:
            logger.error(f"[ChatConsumer] Missing URL parameters: {e}")
            await self.close(code=4000)
            return

        if user.role == 'customer' and str(user.id) != str(self.customer_id):
            logger.warning(f"[ChatConsumer] Authorization failed - customer {user.id} tried to access customer {self.customer_id}")
            await self.close(code=4003)
            return
        if user.role == 'therapist' and str(user.id) != str(self.therapist_id):
            logger.warning(f"[ChatConsumer] Authorization failed - therapist {user.id} tried to access therapist {self.therapist_id}")
            await self.close(code=4003)
            return

        self.room_group_name = f'chat_{min(self.customer_id, self.therapist_id)}_{max(self.customer_id, self.therapist_id)}'
        logger.info(f"[ChatConsumer] Room group name: {self.room_group_name}")

        try:
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            logger.info(f"[ChatConsumer] Added to channel group successfully")
        except Exception as e:
            logger.error(f"[ChatConsumer] Failed to add to channel group: {e}")
            raise

        await self.accept()
        logger.info(f"[ChatConsumer] Connection accepted for user {user.id} (role: {user.role})")

        try:
            self.conversation = await self.get_or_create_conversation(self.customer_id, self.therapist_id)
            logger.info(f"[ChatConsumer] Conversation loaded/created: {self.conversation.id}")
        except Exception as e:
            logger.error(f"[ChatConsumer] Failed to get/create conversation: {e}")
            raise
    
    async def disconnect(self, close_code):
        logger.info(f"[ChatConsumer] Disconnect called with code: {close_code}")
        if hasattr(self, 'room_group_name'):
            try:
                await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
                logger.info(f"[ChatConsumer] Removed from group {self.room_group_name}")
            except Exception as e:
                logger.error(f"[ChatConsumer] Error removing from group: {e}")

    async def receive(self, text_data):
        try:
            logger.info(f"[ChatConsumer] Received message: {text_data[:100]}...")
            data = json.loads(text_data)
            message = data.get('message', '').strip()

            if not message:
                logger.warning(f"[ChatConsumer] Empty message received, ignoring")
                return

            user = self.scope['user']
            sender_id = user.id
            receiver_id = self.therapist_id if user.role == 'customer' else self.customer_id

            logger.info(f"[ChatConsumer] Creating message from {sender_id} to {receiver_id}")
            msg_obj = await self.create_message(self.conversation, sender_id, receiver_id, message)
            logger.info(f"[ChatConsumer] Message created with ID: {msg_obj.id}")

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
            logger.info(f"[ChatConsumer] Message sent to group {self.room_group_name}")
        except Exception as e:
            logger.error(f"[ChatConsumer] Error processing message: {e}", exc_info=True)
    
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
            logger.info(f"[ChatConsumer] Getting/creating conversation for customer {customer_id}, therapist {therapist_id}")
            with transaction.atomic():
                conversation = Conversation.objects.filter(
                    participants__id=customer_id
                ).filter(
                    participants__id=therapist_id
                ).first()

                if not conversation:
                    logger.info(f"[ChatConsumer] Creating new conversation")
                    conversation = Conversation.objects.create()
                    conversation.participants.add(customer_id, therapist_id)
                    logger.info(f"[ChatConsumer] New conversation created: {conversation.id}")
                else:
                    logger.info(f"[ChatConsumer] Found existing conversation: {conversation.id}")
                return conversation
        except Exception as e:
            logger.error(f"[ChatConsumer] Database error in get_or_create_conversation: {e}", exc_info=True)
            raise

    @database_sync_to_async
    def create_message(self, conversation, sender_id, receiver_id, content):
        try:
            logger.info(f"[ChatConsumer] Creating message in conversation {conversation.id}")
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

                logger.info(f"[ChatConsumer] Message saved successfully: {message_obj.id}")
                return message_obj
        except Exception as e:
            logger.error(f"[ChatConsumer] Database error in create_message: {e}", exc_info=True)
            raise

class LocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info(f"[LocationConsumer] Connection attempt started")

        user = self.scope['user']
        logger.info(f"[LocationConsumer] User authenticated: {user.is_authenticated}, User: {user}")

        if not user.is_authenticated:
            logger.warning(f"[LocationConsumer] Connection rejected - user not authenticated")
            await self.close(code=4001)
            return

        try:
            self.customer_id = self.scope['url_route']['kwargs']['customer_id']
            self.therapist_id = self.scope['url_route']['kwargs']['therapist_id']
            logger.info(f"[LocationConsumer] Customer ID: {self.customer_id}, Therapist ID: {self.therapist_id}")
        except KeyError as e:
            logger.error(f"[LocationConsumer] Missing URL parameters: {e}")
            await self.close(code=4000)
            return

        if user.role == 'customer' and str(user.id) != str(self.customer_id):
            logger.warning(f"[LocationConsumer] Authorization failed - customer {user.id} tried to access customer {self.customer_id}")
            await self.close(code=4003)
            return
        if user.role == 'therapist' and str(user.id) != str(self.therapist_id):
            logger.warning(f"[LocationConsumer] Authorization failed - therapist {user.id} tried to access therapist {self.therapist_id}")
            await self.close(code=4003)
            return

        self.room_group_name = f'location_{min(self.customer_id, self.therapist_id)}_{max(self.customer_id, self.therapist_id)}'
        logger.info(f"[LocationConsumer] Room group name: {self.room_group_name}")

        try:
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            logger.info(f"[LocationConsumer] Added to channel group successfully")
        except Exception as e:
            logger.error(f"[LocationConsumer] Failed to add to channel group: {e}")
            raise

        await self.accept()
        logger.info(f"[LocationConsumer] Connection accepted for user {user.id} (role: {user.role})")

    async def disconnect(self, close_code):
        logger.info(f"[LocationConsumer] Disconnect called with code: {close_code}")
        if hasattr(self, 'room_group_name'):
            try:
                await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
                logger.info(f"[LocationConsumer] Removed from group {self.room_group_name}")
            except Exception as e:
                logger.error(f"[LocationConsumer] Error removing from group: {e}")

    async def receive(self, text_data):
        try:
            logger.info(f"[LocationConsumer] Received location data: {text_data[:100]}...")
            data = json.loads(text_data)
            user = self.scope['user']

            if user.role == 'therapist':
                latitude = data.get('latitude')
                longitude = data.get('longitude')

                if latitude and longitude:
                    logger.info(f"[LocationConsumer] Therapist {user.id} location: {latitude}, {longitude}")
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'location_update',
                            'latitude': latitude,
                            'longitude': longitude,
                            'therapist_id': str(user.id),
                        }
                    )
                    logger.info(f"[LocationConsumer] Location sent to group {self.room_group_name}")
                else:
                    logger.warning(f"[LocationConsumer] Missing latitude or longitude in data")
            else:
                logger.warning(f"[LocationConsumer] Customer tried to send location (ignored)")
        except Exception as e:
            logger.error(f"[LocationConsumer] Error processing location: {e}", exc_info=True)
    
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