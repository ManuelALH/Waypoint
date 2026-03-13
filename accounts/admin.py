from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.utils.html import format_html
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    list_display = (
        #"avatar_preview",
        "colored_username",
        "email",
        "location",
        "tables_created",
        "tables_joined",
        "characters_created",
        #"is_staff",
        "is_active",
        "date_joined",
    )

    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "experience_level",
        "play_style",
        "favorite_system",
        "gender",
        "date_joined",
    )

    search_fields = (
        "username",
        "email",
        "location",
    )

    filter_horizontal = (
        "groups",
        "user_permissions",
        "blocked_users",
    )

    readonly_fields = (
        "avatar_preview",
        "date_joined",
        "last_login",
    )

    fieldsets = (
        ("Credenciales", {
            "fields": ("username", "password")
        }),

        ("Información personal", {
            "fields": (
                "avatar",
                "avatar_preview",
                "bio",
                "email",
                "phone_number",
                "location",
                "birth_date",
                "gender",
            )
        }),

        ("Preferencias de juego", {
            "fields": (
                "experience_level",
                "play_style",
                "favorite_system",
            )
        }),

        ("Configuración de privacidad", {
            "fields": (
                "is_email_public",
                "is_phone_public",
                "is_location_public",
                "is_birth_date_public",
                "is_gender_public",
                "is_last_login_public",
            )
        }),

        ("Relaciones sociales", {
            "fields": (
                "blocked_users",
            )
        }),

        ("Permisos", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),

        ("Fechas importantes", {
            "fields": (
                "last_login",
                "date_joined",
            )
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username",
                "email",
                "password1",
                "password2",
                "is_staff",
                "is_active",
            ),
        }),
    )

    ordering = ("-date_joined",)

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="/static/img/avatars/{}" style="width:40px;height:40px;border-radius:50%;" />',
                obj.avatar
            )
        return "-"

    def colored_username(self, obj):
        if not obj.is_active:
            return format_html(
                '<span style="color:red; font-weight:bold;">{}</span>',
                obj.username
            )
        return obj.username

    def tables_created(self, obj):
        count = obj.my_tables.count()
        url = (
            reverse("admin:tables_table_changelist")
            + f"?dm__id__exact={obj.id}"
        )
        return format_html('<a href="{}">{}</a>', url, count)
    
    def tables_joined(self, obj):
        count = obj.joined_tables.count()
        url = (
            reverse("admin:tables_table_changelist")
            + f"?players__id__exact={obj.id}"
        )
        return format_html('<a href="{}">{}</a>', url, count)
    
    def characters_created(self, obj):
        count = obj.characters.count()
        url = (
            reverse("admin:characters_character_changelist")
            + f"?owner__id__exact={obj.id}"
        )
        return format_html('<a href="{}">{}</a>', url, count)

    avatar_preview.short_description = "Avatar"
    colored_username.short_description = "Usuario"
    colored_username.admin_order_field = "username"        
    tables_created.short_description = "Mesas creadas"
    tables_joined.short_description = "Mesas jugadas"
    characters_created.short_description = "Personajes"