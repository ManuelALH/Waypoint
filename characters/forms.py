from django import forms
from .models import Character

class CharacterForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["character_class"].widget = forms.Select(choices=[])
        self.fields["race"].widget = forms.Select(choices=[])
