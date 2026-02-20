from django.contrib import admin
from .models.base import Character

@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ('name', 'system', 'owner', 'created_at')
    list_filter = ('system',)