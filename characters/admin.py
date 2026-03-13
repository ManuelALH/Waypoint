from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from characters.models import Character


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "system",
        "owner",
        "tables_count",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "system",
        "created_at",
    )

    search_fields = (
        "name",
        "owner__username",
        "owner__email",
    )

    autocomplete_fields = (
        "owner",
        "system",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    date_hierarchy = "created_at"

    ordering = ("-created_at",)

    def tables_count(self, obj):
        count = obj.joined_tables.count()
        if count == 0:
            return "-"
        url = (
            reverse("admin:tables_table_changelist")
            + f"?characters__id__exact={obj.id}"
        )
        return format_html('<a href="{}">{}</a>', url, count)

    tables_count.short_description = "Mesas"