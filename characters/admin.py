from django.contrib import admin
from characters.models import Character

@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ('name', 'system', 'owner', 'created_at')
    list_filter = ('system',)