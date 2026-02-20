from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User

    list_display = [
        'username', 
        'email', 
        'avatar_preview',
        'location', 
        'is_staff', 
        'date_joined'
    ]
    
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'gender']
    
    search_fields = ['username', 'email', 'location', 'phone_number']

    fieldsets = UserAdmin.fieldsets + (
        ('Información de Perfil', {
            'fields': ('avatar', 'bio', 'location', 'phone_number', 'gender')
        }),
        ('Configuración de Privacidad', {
            'fields': (
                'is_email_public', 
                'is_location_public', 
                'is_phone_public', 
                'is_gender_public',
                'is_last_login_public'
            )
        }),
    )

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="/static/img/avatars/{}" style="width: 30px; height: 30px; border-radius: 50%;" />',
                obj.avatar
            )
        return "-"
    
    avatar_preview.short_description = "Avatar"

admin.site.register(User, CustomUserAdmin)
