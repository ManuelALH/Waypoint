from django.contrib import admin
from django.utils.html import format_html
from .models import Table, TableInvitation, CampaignLog

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "dm",
        "system",
        "players_status",
        "is_full",
        "is_private",
        "created_at",
    )

    list_filter = (
        "system",
        "modality",
        "frequency",
        "experience_level",
        "play_style",
        "price_type",
        "is_private",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
        "dm__username",
        "location",
    )

    filter_horizontal = (
        "players",
        "characters",
    )

    date_hierarchy = "created_at"

    autocomplete_fields = (
        "dm",
        "system",
    )

    def player_count(self, obj):
        return obj.players.count()

    def players_status(self, obj):
        current = obj.players.count()
        maximum = obj.max_players
        if current >= maximum:
            return format_html(
                '<span style="color:red; font-weight:bold;">{}/{}</span>',
                current,
                maximum
            )
        return "{}/{}".format(current, maximum)

    def is_full(self, obj):
        return obj.players.count() >= obj.max_players

    player_count.short_description = "Jugadores actuales"
    players_status.short_description = "Jugadores"
    is_full.boolean = True
    is_full.short_description = "Mesa llena"

@admin.register(TableInvitation)
class TableInvitationAdmin(admin.ModelAdmin):
    list_display = (
        "table",
        "receiver",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "table__name",
        "receiver__username",
    )

    autocomplete_fields = (
        "table",
        "receiver",
    )

    date_hierarchy = "created_at"


@admin.register(CampaignLog)
class CampaignLogAdmin(admin.ModelAdmin):
    list_display = (
        "entry_type",
        "table",
        "target_character",
        "author",
        "is_public",
        "created_at",
        "was_edited",
    )

    list_filter = (
        "entry_type",
        "is_public",
        "created_at",
    )

    search_fields = (
        "table__name",
        "author__username",
        "content",
    )

    autocomplete_fields = (
        "table",
        "author",
        "target_character",
    )

    date_hierarchy = "created_at"
