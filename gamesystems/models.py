from django.db import models

class GameSystem(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nombre del Sistema")
    slug = models.SlugField(unique=True, help_text="Identificador único (ej: dnd5e, cthulhu)")
    description = models.TextField(blank=True)
    
    schema_definition = models.JSONField(
        verbose_name="Esquema del Sistema",
        help_text="Estructura JSON que define stats, skills, etc."
    )
    
    primary_color = models.CharField(max_length=7, default="#3498db", help_text="Código Hexadecimal")
    dm_title = models.CharField(max_length=20, default="Director de Juego", help_text="Titulo del Director de Juego")
    players_title = models.CharField(max_length=20, default="Jugadores", help_text="Titulo para los Jugadores")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
