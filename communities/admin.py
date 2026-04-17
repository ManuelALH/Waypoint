from django.contrib import admin
from .models import Community, CommunityMember, Event

class CommunityMemberInline(admin.TabularInline):
    """Permite ver y editar miembros directamente dentro de la página de la Comunidad."""
    model = CommunityMember
    extra = 1
    fields = ('user', 'role', 'is_official_dm', 'joined_at')
    readonly_fields = ('joined_at',)

@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    # Campos que se mostrarán en la lista principal de comunidades
    list_display = ('name', 'location', 'address', 'color', 'created_at')
    
    # Agrega una barra de búsqueda para estos campos
    search_fields = ('name', 'location', 'address', 'description')
    
    # Agrega filtros en el lateral derecho
    list_filter = ('created_at', 'location')
    
    # Mantiene la generación automática del slug
    prepopulated_fields = {'slug': ('name',)}
    
    # Incluye la edición de miembros dentro de la comunidad
    inlines = [CommunityMemberInline]

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    # Campos visibles en la lista de eventos
    list_display = ('title', 'community', 'date', 'location', 'created_at')
    
    # Filtros útiles para eventos
    list_filter = ('community', 'date', 'location')
    
    # Búsqueda por título o descripción
    search_fields = ('title', 'description', 'location', 'address')
    
    # Permite navegar por fechas en la parte superior
    date_hierarchy = 'date'

@admin.register(CommunityMember)
class CommunityMemberAdmin(admin.ModelAdmin):
    """Opcional: Para ver una lista global de todos los miembros de todas las comunidades."""
    list_display = ('user', 'community', 'role', 'is_official_dm', 'joined_at')
    list_filter = ('role', 'is_official_dm', 'community')
    search_fields = ('user__username', 'community__name')