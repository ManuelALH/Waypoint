from django.contrib import admin
from .models import GameSystem

@admin.register(GameSystem)
class GameSystemAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'primary_color', 'dm_title', 'players_title')
