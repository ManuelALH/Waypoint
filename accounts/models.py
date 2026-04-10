from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Avatar(models.TextChoices):
        BOOK_SKULL = 'book_skull.png', 'Libro con Calavera'
        BOOK_SPELLS = 'book_spells.png', 'Libro de Hechizos'
        COFFIN = 'coffin.png', 'Ataud'
        CTHULHU = 'cthulhu.png', 'Cthulhu'        
        D20 = 'd20.png', 'D20'
        D20_BLUE = 'd20_blue.png', 'D20 Azul'
        D20_RED = 'd20_red.png', 'D20 Rojo'
        DRAGON_BLACK = 'dragon_black.png', 'Dragon Negro'
        DRAGON_BLUE = 'dragon_blue.png', 'Dragon Azul'
        DRAGON_GREEN = 'dragon_green.png', 'Dragon Verde'
        DRAGON_RED = 'dragon_red.png', 'Dragon Rojo'
        INVESTIGATOR = 'investigator.png', 'Investigador'
        SPELL_FIRE = 'spell_fire.png', 'Hechizo de Fuego'
        SWORD_MAGIC = 'sword_magic.png', 'Espada Magica'
        SWORD_PAIR = 'sword_pair.png', 'Par de Espadas'
        SWORD_SHIELD = 'sword_shield.png', 'Espada con Escudo'
        VAMPIRE_FANGS = 'vampire_fangs.png', 'Colmillos de Vampiro'
        VAMPIRE_FEMALE = 'vampire_female.png', 'Vampira'
        VAMPIRE_MALE = 'vampire_male.png', 'Vampiro'        
        WEREWOLF = 'werewolf.png', 'Hombre Lobo'
    
    class Gender(models.TextChoices):
        MASCULINO = 'M', 'Masculino'
        FEMENINO = 'F', 'Femenino'
        NO_BINARIO = 'NB', 'No Binario'
        GENERO_FLUIDO = 'GF', 'Género Fluido'
        AGENERO = 'AG', 'Agénero'
        OTRO = 'O', 'Otro'
        PREFIERO_NO_DECIR = 'P', 'Prefiero no decir'
    
    class ExperienceLevel(models.TextChoices):
        BEGINNER = 'beginner', 'Principiante'
        INTERMEDIATE = 'intermediate', 'Intermedio'
        VETERAN = 'veteran', 'Veterano'

    class PlayStyle(models.TextChoices):
        ROLEPLAY = 'roleplay', 'Full Roleplay (Interpretación)'
        COMBAT = 'combat', 'Full Combat (Wargame)'
        BALANCED = 'balanced', 'Balanceado (50/50)'

    avatar = models.CharField(
        max_length=50, 
        choices=Avatar.choices, 
        default=Avatar.D20,
        verbose_name="Avatar"
    )

    bio = models.TextField(max_length=500, blank=True, verbose_name="Sobre mí")

    email = models.EmailField(unique=True)
    is_email_public = models.BooleanField(default=False, verbose_name="Email Público")

    phone_number = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    is_phone_public = models.BooleanField(default=False, verbose_name="Mostrar Teléfono")

    location = models.CharField(max_length=100, blank=True, verbose_name="Ubicación")
    is_location_public = models.BooleanField(default=False, verbose_name="Mostrar Ubicación")

    birth_date = models.DateField(null=True, blank=True, verbose_name="Fecha de Nacimiento")
    is_birth_date_public = models.BooleanField(default=False, verbose_name="Mostrar Cumpleaños")

    gender = models.CharField(max_length=2, choices=Gender.choices, blank=True, verbose_name="Género")
    is_gender_public = models.BooleanField(default=False, verbose_name="Mostrar Género")

    experience_level = models.CharField(
        max_length=20, 
        choices=ExperienceLevel.choices, 
        default=ExperienceLevel.BEGINNER,
        verbose_name="Nivel de Experiencia"
    )

    play_style = models.CharField(
        max_length=20, 
        choices=PlayStyle.choices, 
        default=PlayStyle.BALANCED,
        verbose_name="Estilo de Juego"
    )

    favorite_system = models.ForeignKey(
        'gamesystems.GameSystem', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='fans',
        verbose_name="Sistema Favorito"
    )

    is_last_login_public = models.BooleanField(
        default=False, 
        verbose_name="Mostrar última conexión"
    )

    blocked_users = models.ManyToManyField(
        'self', 
        symmetrical=False, 
        blank=True, 
        related_name='blocked_by',
        verbose_name="Usuarios Bloqueados"
    )
