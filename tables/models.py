from django.db import models
from django.conf import settings
from gamesystems.models import GameSystem
from characters.models import Character

class Table(models.Model):
    class Modality(models.TextChoices):
        PRESENTIAL = 'presential', 'Presencial'
        VIRTUAL = 'virtual', 'Virtual'
        HYBRID = 'hybrid', 'Híbrido'

    class ExperienceLevel(models.TextChoices):
        BEGINNER = 'beginner', 'Principiante'
        INTERMEDIATE = 'intermediate', 'Intermedio'
        ADVANCED = 'advanced', 'Avanzado'

    class PlayStyle(models.TextChoices):
        ROLEPLAY = 'roleplay', 'Roleplay'
        COMBAT = 'combat', 'Combate'
        BALANCED = 'balanced', 'Balanceado'

    class PriceType(models.TextChoices):
        FREE = 'free', 'Gratuito'
        PAID = 'paid', 'De pago'

    class Frequency(models.TextChoices):
        ONESHOT = 'oneshot', 'Oneshot'
        WEEKLY = 'weekly', 'Semanal'
        BIWEEKLY = 'biweekly', 'Quincenal'
        MONTHLY = 'monthly', 'Mensual'

    dm = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='my_tables')
    system = models.ForeignKey(GameSystem, on_delete=models.PROTECT, verbose_name="Sistema de Juego")
    name = models.CharField(max_length=100, verbose_name="Nombre de la Campaña")
    description = models.TextField(verbose_name="Descripción", blank=True)
    location = models.CharField(max_length=100, verbose_name="Ubicación", blank=True, null=True)
    address = models.CharField(max_length=255, verbose_name="Dirección del Lugar", blank=True, null=True)

    frequency = models.CharField(
        max_length=20, 
        choices=Frequency.choices, 
        default=Frequency.WEEKLY,
        verbose_name="Frecuencia"
    )

    modality = models.CharField(
        max_length=20, 
        choices=Modality.choices, 
        default=Modality.VIRTUAL,
        verbose_name="Modalidad"
    )

    experience_level = models.CharField(
        max_length=20, 
        choices=ExperienceLevel.choices, 
        default=ExperienceLevel.BEGINNER,
        verbose_name="Nivel de Juego"
    )
    
    play_style = models.CharField(
        max_length=20, 
        choices=PlayStyle.choices, 
        default=PlayStyle.BALANCED,
        verbose_name="Estilo de Juego"
    )
    
    price_type = models.CharField(
        max_length=20, 
        choices=PriceType.choices, 
        default=PriceType.FREE,
        verbose_name="Precio"
    )

    is_private = models.BooleanField(default=False, verbose_name="Mesa Privada")
    play_days = models.CharField(max_length=200, verbose_name="Días de Juego")
    start_time = models.TimeField(verbose_name="Hora Inicio")
    end_time = models.TimeField(verbose_name="Hora Fin")
    max_players = models.PositiveIntegerField(default=8, verbose_name="Jugadores Máximos")
    created_at = models.DateTimeField(auto_now_add=True)
    players = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='joined_tables', 
        blank=True
    )

    characters = models.ManyToManyField(
        'characters.Character',
        related_name='joined_tables',
        blank=True,
        help_text="Personajes que participan en esta mesa"
    )

    community = models.ForeignKey(
        'communities.Community', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='community_tables'
    )
    event = models.ForeignKey(
        'communities.Event', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='event_tables'
    )

    invite_only = models.BooleanField(
        default=False, 
        verbose_name="Solo invitación"
    )

    is_archived = models.BooleanField(
        default=False, 
        verbose_name="Archivada"
    )

    def __str__(self):
        return f"{self.name} - DM: {self.dm}"

class TableInvitation(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='invitations')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='table_invitations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('table', 'receiver')

class CampaignLog(models.Model):
    class EntryTypes(models.TextChoices):
        FREE = 'free', 'Libre'
        PROGRESSION = 'progression', 'Progresión'
        ACHIEVEMENT = 'achievement', 'Logro'
        ITEM = 'item', 'Objeto'
        DEATH = 'death', 'Muerte'

    entry_type = models.CharField(
        max_length=20, 
        choices=EntryTypes.choices, 
        default=EntryTypes.FREE,
        verbose_name="Tipo de Entrada"
    )

    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='logs')
    content = models.TextField(blank=True, null=True)
    target_character = models.ForeignKey('characters.Character', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=True, verbose_name="Es visible para jugadores")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Autor")
    updated_at = models.DateTimeField(auto_now=True)

    def was_edited(self):
        return (self.updated_at - self.created_at).total_seconds() > 60

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_entry_type_display()} - {self.table.name}"

class TableNote(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def was_edited(self):
        return (self.updated_at - self.created_at).total_seconds() > 60

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Nota de {self.author.username} en {self.table.name}"
