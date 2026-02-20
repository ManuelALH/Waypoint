from django.db import models
from django.conf import settings
from django.utils import timezone 

class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='received_messages'
    )
    
    parent = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='replies',
        verbose_name="En respuesta a"
    )

    subject = models.CharField(max_length=120, verbose_name="Asunto")
    body = models.CharField(max_length=255, verbose_name="Mensaje")
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)    
    sender_deleted_at = models.DateTimeField(null=True, blank=True)
    recipient_deleted_at = models.DateTimeField(null=True, blank=True)

    related_table = models.ForeignKey(
        'tables.Table', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='linked_messages',
        verbose_name="Mesa relacionada"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', 'sender_deleted_at']),
            models.Index(fields=['recipient', 'recipient_deleted_at']),
            models.Index(fields=['read_at']),
        ]

    def __str__(self):
        return f"De {self.sender} para {self.recipient}: {self.subject}"

    @property
    def is_read(self):
        return self.read_at is not None

    def mark_as_read(self):
        if self.read_at is None:
            self.read_at = timezone.now()
            self.save()
