from django.db import models
from django.conf import settings

class Character(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="characters"
    )
    name = models.CharField(max_length=100)
    
    system = models.ForeignKey(
        'gamesystems.GameSystem', 
        on_delete=models.CASCADE,
        related_name='characters'
    )
    
    data = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
