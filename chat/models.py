from django.db import models
from django.conf import settings
from django.utils import timezone

class Conversation(models.Model):
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations',
        db_index=True,
    )
    last_message = models.ForeignKey(
        'Message',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='last_message_for',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_index=True,
    )
    # Allow NULL so that existing rows don’t need a default
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['-updated_at']),
        ]

    def __str__(self):
        participants_str = ", ".join(
            str(p) for p in self.participants.all()[:3]
        )
        return f"Conversation {self.id}: {participants_str}"

    def mark_all_as_read(self, user_id):
        return self.messages.filter(
            receiver_id=user_id,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )

    def get_other_participant(self, user):
        return self.participants.exclude(id=user.id).first()


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages',
    )
    content = models.TextField()
    is_read = models.BooleanField(
        default=False,
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    message_type = models.CharField(
        max_length=20,
        default='text',
        choices=[
            ('text', 'Text Message'),
            ('image', 'Image'),
            ('file', 'File'),
            ('system', 'System Message'),
        ],
    )
    metadata = models.JSONField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['receiver', 'is_read']),
        ]

    def __str__(self):
        return f"Message {self.id} from {self.sender} to {self.receiver}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
        return self