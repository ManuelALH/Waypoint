from django.db import models
from django.contrib.auth.models import User
from gamesystems.models import GameSystem

class Character(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    system = models.ForeignKey(GameSystem, on_delete=models.CASCADE)
    
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.system.name})"
