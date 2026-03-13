from django.contrib import admin
from django import forms
from django.urls import reverse
from django.utils.html import format_html
from .models import GameSystem
import json

class GameSystemForm(forms.ModelForm):
    schema_file = forms.FileField(
        required=False,
        label="Cargar archivo JSON",
        help_text="Sube un archivo .json para actualizar el esquema"
    )

    schema_definition = forms.JSONField(
        widget=forms.Textarea(attrs={"rows": 10, "cols": 80}),
        required=True,
        help_text="Estructura JSON que define stats, skills, etc."
    )

    class Meta:
        model = GameSystem
        fields = "__all__"

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.schema_definition:
            self.initial["schema_definition"] = json.dumps(
                self.instance.schema_definition, indent=4, ensure_ascii=False
            )
    """

    def clean_schema_file(self):
        file = self.cleaned_data.get("schema_file")
        if file:
            try:
                data = json.load(file)
            except json.JSONDecodeError as e:
                raise forms.ValidationError(f"Archivo JSON inválido: {e}")
            return data
        return None

    def clean(self):
        cleaned_data = super().clean()
        file_data = cleaned_data.get("schema_file")
        if file_data is not None:
            cleaned_data["schema_definition"] = file_data
        return cleaned_data

@admin.register(GameSystem)
class GameSystemAdmin(admin.ModelAdmin):
    form = GameSystemForm

    list_display = (
        "name",
        "slug",
        "color_preview",
        "dm_title",
        "players_title",
        "tables_count",
        "characters_count",
        "schema_size",
    )

    list_filter = ("dm_title", "players_title")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("color_preview", "tables_count", "characters_count", "schema_size")
    fieldsets = (
        ("Información básica", {
            "fields": ("name", "slug", "description")
        }),
        ("Apariencia", {
            "fields": ("primary_color", "color_preview")
        }),
        ("Roles", {
            "fields": ("dm_title", "players_title")
        }),
        ("Definición del sistema", {
            "fields": ("schema_definition", "schema_file", "schema_size", "tables_count", "characters_count")
        }),
    )

    def color_preview(self, obj):
        return format_html(
            '<div style="width:40px; height:20px; background-color:{}; border:1px solid #000;"></div>',
            obj.primary_color
        )

    def schema_size(self, obj):
        return len(obj.schema_definition.keys()) if obj.schema_definition else 0
    

    def tables_count(self, obj):
        count = obj.table_set.count()
        url = reverse("admin:tables_table_changelist") + f"?system__id__exact={obj.id}"
        return format_html('<a href="{}">{}</a>', url, count)
    

    def characters_count(self, obj):
        count = obj.characters.count()
        url = reverse("admin:characters_character_changelist") + f"?system__id__exact={obj.id}"
        return format_html('<a href="{}">{}</a>', url, count)
    

    color_preview.short_description = "Color"
    schema_size.short_description = "Campos del esquema"
    tables_count.short_description = "Mesas"
    characters_count.short_description = "Personajes"
