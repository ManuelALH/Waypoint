# communities/models.py
from django.db import models
from django.conf import settings  # <-- Usamos settings en lugar de User
from django.utils.text import slugify
from django.core.exceptions import PermissionDenied

class Community(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default='#000000', help_text="Color en formato HEX (ej. #6f42c1)")
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(help_text="Descripción de la comunidad")
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through='CommunityMember', related_name='communities')
    location = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ubicación")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Sede")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_member(self, user):
        return self.communitymember_set.filter(user=user).first()

    def can_manage_community(self, user):
        member = self.get_member(user)
        return member and member.role == CommunityMember.Role.FOUNDER

    def can_manage_events(self, user):
        member = self.get_member(user)
        if not member: return False
        return member.role in [CommunityMember.Role.FOUNDER, CommunityMember.Role.MODERATOR]

    def can_create_event_tables(self, user):
        member = self.get_member(user)
        if not member: return False
        return (member.role in [CommunityMember.Role.FOUNDER, CommunityMember.Role.MODERATOR] 
                or member.is_official_dm)
                
    def promote_to_moderator(self, admin_user, target_member):
        if self.can_manage_community(admin_user):
            target_member.role = CommunityMember.Role.MODERATOR
            target_member.save()

    def assign_official_dm(self, admin_user, target_member):
        if self.can_manage_events(admin_user):
            target_member.is_official_dm = True
            target_member.save()

    def can_delete_table(self, user, table):
        member = self.get_member(user)
        if not member: return False
        is_staff = member.role in [CommunityMember.Role.FOUNDER, CommunityMember.Role.MODERATOR]
        is_owner = table.dm == user
        return is_staff or is_owner

    @property
    def founder(self):
        founder_member = self.communitymember_set.filter(role='founder').first()
        if founder_member:
            return founder_member.user.username
        return "Desconocido"

    def __str__(self):
        return self.name

class CommunityMember(models.Model):
    class Role(models.TextChoices):
        FOUNDER = 'founder', 'Fundador'
        MODERATOR = 'moderator', 'Moderador'
        MEMBER = 'member', 'Miembro'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    is_official_dm = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    def resign_as_moderator(self):
        if self.role == self.Role.MODERATOR:
            self.role = self.Role.MEMBER
            self.save()
        else:
            raise PermissionDenied("Solo los moderadores pueden realizar esta acción.")

    class Meta:
        unique_together = ('user', 'community')

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()} en {self.community.name}"

class Event(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ubicación")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Sede")

    def __str__(self):
        return f"{self.title} ({self.community.name})"
