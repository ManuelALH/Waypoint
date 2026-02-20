from django.db import models

class GameSystem(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    schema = models.JSONField(default=dict, blank=True) 

    def __str__(self):
        return self.name